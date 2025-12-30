import React, { useEffect, useRef, useState, memo } from 'react';
import * as pdfjsLib from 'pdfjs-dist';

// Ensure worker is set up
if (typeof window !== 'undefined' && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
}

interface PageThumbnailSidebarProps {
    fileUrl: string | null;
    numPages: number;
    currentPage: number;
    onPageClick: (page: number) => void;
}

// Memoized individual thumbnail component to prevent re-renders and isolate canvas logic
const ThumbnailItem = memo(({
    pageIndex,
    pdfDoc,
    isActive,
    onClick
}: {
    pageIndex: number;
    pdfDoc: pdfjsLib.PDFDocumentProxy | null;
    isActive: boolean;
    onClick: () => void;
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isRendered, setIsRendered] = useState(false);
    const pageNumber = pageIndex + 1;

    useEffect(() => {
        if (!pdfDoc || !canvasRef.current || isRendered) return;

        let isCancelled = false;

        const renderThumbnail = async () => {
            console.log(`[ThumbnailItem] Rendering page ${pageNumber}`);
            try {
                const page = await pdfDoc.getPage(pageNumber);
                if (isCancelled) return;

                const viewport = page.getViewport({ scale: 0.2 }); // Low res thumbnail
                const canvas = canvasRef.current;
                if (!canvas) return;

                const context = canvas.getContext('2d');
                if (!context) return;

                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = {
                    canvasContext: context,
                    viewport: viewport,
                };

                await page.render(renderContext).promise;
                if (!isCancelled) setIsRendered(true);
            } catch (error) {
                console.error(`Error rendering thumbnail for page ${pageNumber}:`, error);
            }
        };

        // Use IntersectionObserver to lazy load? 
        // For simplicity in this iteration, we'll try to render. 
        // In a large doc, we should definitely lazy load.
        // Let's implement a simple viewport check using standard IntersectionObserver if possible, 
        // or just fire it. 
        // Given complexity, let's just fire but with a requestIdleCallback if available or timeout?
        // Actually, let's just render. Browsers handle off-screen canvas rendering okay-ish, 
        // but typically you want to observer.

        // Basic observer implementation:
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                renderThumbnail();
                observer.disconnect();
            }
        });

        if (canvasRef.current) {
            observer.observe(canvasRef.current);
        }

        return () => {
            isCancelled = true;
            observer.disconnect();
        };
    }, [pdfDoc, pageNumber, isRendered]);

    return (
        <div
            onClick={onClick}
            className={`cursor-pointer mb-4 flex flex-col items-center group ${isActive ? 'opacity-100' : 'opacity-70 hover:opacity-100'}`}
        >
            <div className={`relative bg-white shadow-sm transition-all duration-200 ${isActive
                ? 'ring-2 ring-blue-500 ring-offset-2'
                : 'border border-gray-200 hover:border-gray-300'
                }`}>
                <canvas ref={canvasRef} className="block w-full h-auto" />
                {!isRendered && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50 text-xs text-gray-400">
                        Loading...
                    </div>
                )}
            </div>
            <span className={`mt-1 text-xs font-medium ${isActive ? 'text-blue-600' : 'text-gray-500'}`}>
                {pageNumber}
            </span>
        </div>
    );
});

ThumbnailItem.displayName = 'ThumbnailItem';

export default function PageThumbnailSidebar({
    fileUrl,
    numPages,
    currentPage,
    onPageClick,
}: PageThumbnailSidebarProps) {
    const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null);

    // Load PDF Document for thumbnail generation
    useEffect(() => {
        if (!fileUrl) return;

        let loadingTask: pdfjsLib.PDFDocumentLoadingTask | null = null;

        const loadPdf = async () => {
            console.log('[PageThumbnailSidebar] Loading PDF for thumbnails:', fileUrl);
            try {
                loadingTask = pdfjsLib.getDocument(fileUrl);
                const pdf = await loadingTask.promise;
                console.log('[PageThumbnailSidebar] PDF loaded, pages:', pdf.numPages);
                setPdfDoc(pdf);
            } catch (error) {
                console.error("Error loading PDF for thumbnails:", error);
            }
        };

        loadPdf();

        return () => {
            if (loadingTask) {
                loadingTask.destroy();
            }
        };
    }, [fileUrl]);

    return (
        <div className="w-full h-full bg-gray-50 p-4 min-h-0">
            <div className="space-y-2">
                {fileUrl && numPages > 0 ? (
                    Array.from({ length: numPages }).map((_, index) => (
                        <ThumbnailItem
                            key={index}
                            pageIndex={index}
                            pdfDoc={pdfDoc}
                            isActive={currentPage === index + 1}
                            onClick={() => onPageClick(index + 1)}
                        />
                    ))
                ) : (
                    !fileUrl ? (
                        <div className="text-xs text-gray-400 text-center py-4">No Document</div>
                    ) : (
                        // Skeletons
                        Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="mb-4">
                                <div className="aspect-[3/4] bg-gray-200 animate-pulse rounded-sm mb-1" />
                            </div>
                        ))
                    )
                )}
            </div>
        </div>
    );
}

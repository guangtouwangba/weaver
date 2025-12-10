# PDF Viewer 迁移方案

> 从 react-pdf 迁移到 pdfjs-dist 完整 Viewer，实现专业级的文本选择、高亮和拖拽功能。

## 背景

### 当前实现

当前使用 `react-pdf` 库（底层基于 pdfjs-dist）实现 PDF 查看功能：

```typescript
// SourcePanel.tsx
import { Document, Page, pdfjs } from 'react-pdf';
```

**已实现的功能**：
- PDF 渲染和分页
- 基于 `window.getSelection()` 的文本选择拖拽
- 基于 searchText 的跳转高亮

**存在的问题**：
1. **Text Layer 结构问题**：react-pdf 渲染的文本层由很多小 span 元素拼接，文本选择体验不连贯
2. **拖拽依赖浏览器默认行为**：无法自定义拖拽预览，没有持久化高亮
3. **复杂布局支持差**：多栏、表格等复杂 PDF 布局选择混乱

### 迁移目标

实现专业级的 PDF 交互体验：
- 流畅的文本选择
- 可视化的选择高亮
- 自定义拖拽预览
- 精确的跳转定位

---

## 方案对比

| 方案 | 工作量 | 体验上限 | 适用场景 |
|------|--------|----------|----------|
| A. 增强现有 react-pdf | 2-3天 | 中等 | 快速验证需求 |
| B. 迁移到 pdfjs-dist 完整 Viewer | 5-7天 | 高 | 专业级体验 |
| C. 商业库 (PSPDFKit/PDFTron) | 1-2天 | 最高 | 预算充足 |

**推荐方案 B**：在可控工作量内实现专业级体验。

---

## 方案 B 详细设计

### 影响范围

| 层级 | 需要修改 | 说明 |
|------|----------|------|
| 后端 | 否 | PDF 文本提取 (pymupdf.py) 与前端显示无关 |
| 前端 | 是 | 核心改动在 SourcePanel.tsx 及新增组件 |

### 接口兼容性

以下接口保持不变，确保向后兼容：

```typescript
// StudioContext.tsx - 导航接口不变
navigateToSource(documentId: string, pageNumber: number, searchText?: string)

// CanvasNode - 数据结构不变
interface CanvasNode {
  sourceId?: string;
  sourcePage?: number;
  // ...
}

// 拖拽数据格式不变
{
  sourceType: 'pdf',
  sourceId: string,
  sourceTitle: string,
  pageNumber: number,
  content: string
}
```

---

## 前端改动清单

### 1. 依赖变更

**文件**: `app/frontend/package.json`

```diff
  "dependencies": {
    "pdfjs-dist": "^4.0.379",
-   "react-pdf": "^9.0.0",
+   // react-pdf 可选择保留或移除
  }
```

### 2. 新增文件结构

```
app/frontend/src/components/pdf/
├── PDFViewerWrapper.tsx   (~200行) - 封装 pdfjs PDFViewer
├── SelectionManager.ts    (~150行) - 选择状态管理
├── HighlightOverlay.tsx   (~100行) - 高亮渲染层
├── DragHandler.ts         (~80行)  - 拖拽逻辑封装
├── types.ts               (~30行)  - 类型定义
└── index.ts               (~10行)  - 导出

app/frontend/src/styles/
└── pdf-viewer.css         (~50行)  - 样式覆盖
```

### 3. 核心组件设计

#### 3.1 PDFViewerWrapper

封装 pdfjs-dist 的 PDFViewer：

```typescript
// components/pdf/PDFViewerWrapper.tsx
import * as pdfjsLib from 'pdfjs-dist';
import { PDFViewer, EventBus, PDFLinkService } from 'pdfjs-dist/web/pdf_viewer';
import 'pdfjs-dist/web/pdf_viewer.css';

interface PDFViewerWrapperProps {
  fileUrl: string;
  pageNumber: number;
  width: number;
  onPageChange: (page: number) => void;
  onDocumentLoad: (numPages: number) => void;
  onTextSelect: (selection: TextSelection) => void;
  highlightText?: string;
}

export function PDFViewerWrapper({
  fileUrl,
  pageNumber,
  width,
  onPageChange,
  onDocumentLoad,
  onTextSelect,
  highlightText,
}: PDFViewerWrapperProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const eventBusRef = useRef<EventBus | null>(null);
  const viewerRef = useRef<PDFViewer | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // 初始化 EventBus 和 PDFViewer
    const eventBus = new EventBus();
    eventBusRef.current = eventBus;

    const linkService = new PDFLinkService({ eventBus });

    const viewer = new PDFViewer({
      container: containerRef.current,
      eventBus,
      linkService,
      textLayerMode: 2, // 启用增强文本层
      annotationMode: 2,
    });
    viewerRef.current = viewer;

    linkService.setViewer(viewer);

    // 监听文档加载
    eventBus.on('pagesinit', () => {
      viewer.currentScaleValue = 'page-width';
    });

    // 加载 PDF
    const loadDocument = async () => {
      const loadingTask = pdfjsLib.getDocument(fileUrl);
      const pdf = await loadingTask.promise;
      viewer.setDocument(pdf);
      linkService.setDocument(pdf);
      onDocumentLoad(pdf.numPages);
    };

    loadDocument();

    return () => {
      viewer.cleanup();
    };
  }, [fileUrl]);

  // 页面跳转
  useEffect(() => {
    if (viewerRef.current && pageNumber > 0) {
      viewerRef.current.currentPageNumber = pageNumber;
    }
  }, [pageNumber]);

  return (
    <div ref={containerRef} className="pdf-viewer-container">
      <div className="pdfViewer" />
    </div>
  );
}
```

#### 3.2 SelectionManager

管理文本选择状态：

```typescript
// components/pdf/SelectionManager.ts
export interface TextSelection {
  text: string;
  rects: DOMRect[];
  pageNumber: number;
}

export class SelectionManager {
  private container: HTMLElement;
  private onSelectionChange: (selection: TextSelection | null) => void;

  constructor(
    container: HTMLElement,
    onSelectionChange: (selection: TextSelection | null) => void
  ) {
    this.container = container;
    this.onSelectionChange = onSelectionChange;
    this.setupListeners();
  }

  private setupListeners() {
    document.addEventListener('selectionchange', this.handleSelectionChange);
    this.container.addEventListener('mouseup', this.handleMouseUp);
  }

  private handleSelectionChange = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      this.onSelectionChange(null);
      return;
    }

    // 检查选择是否在 PDF 容器内
    const anchorNode = selection.anchorNode;
    if (!this.container.contains(anchorNode)) {
      return;
    }

    const text = selection.toString().trim();
    if (!text) {
      this.onSelectionChange(null);
      return;
    }

    const range = selection.getRangeAt(0);
    const rects = Array.from(range.getClientRects());

    // 获取页码
    const pageElement = anchorNode?.parentElement?.closest('.page');
    const pageNumber = pageElement
      ? parseInt(pageElement.getAttribute('data-page-number') || '1')
      : 1;

    this.onSelectionChange({ text, rects, pageNumber });
  };

  private handleMouseUp = () => {
    // 延迟处理，确保选择已完成
    setTimeout(() => this.handleSelectionChange(), 10);
  };

  public destroy() {
    document.removeEventListener('selectionchange', this.handleSelectionChange);
    this.container.removeEventListener('mouseup', this.handleMouseUp);
  }
}
```

#### 3.3 HighlightOverlay

渲染高亮层：

```typescript
// components/pdf/HighlightOverlay.tsx
interface HighlightOverlayProps {
  selection: TextSelection | null;
  searchHighlight?: {
    text: string;
    pageNumber: number;
  };
  containerRef: React.RefObject<HTMLElement>;
}

export function HighlightOverlay({
  selection,
  searchHighlight,
  containerRef,
}: HighlightOverlayProps) {
  const [highlightRects, setHighlightRects] = useState<DOMRect[]>([]);

  // 计算高亮位置
  useEffect(() => {
    if (!selection || !containerRef.current) {
      setHighlightRects([]);
      return;
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const adjustedRects = selection.rects.map(rect => ({
      ...rect,
      left: rect.left - containerRect.left,
      top: rect.top - containerRect.top,
    }));
    setHighlightRects(adjustedRects as DOMRect[]);
  }, [selection, containerRef]);

  if (highlightRects.length === 0) return null;

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 10,
      }}
    >
      {highlightRects.map((rect, index) => (
        <Box
          key={index}
          sx={{
            position: 'absolute',
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            bgcolor: 'rgba(255, 235, 59, 0.4)',
            borderRadius: '2px',
          }}
        />
      ))}
    </Box>
  );
}
```

#### 3.4 DragHandler

拖拽逻辑封装：

```typescript
// components/pdf/DragHandler.ts
export interface DragData {
  sourceType: 'pdf';
  sourceId: string;
  sourceTitle: string;
  pageNumber: number;
  content: string;
}

export function createDragHandler(
  documentId: string,
  documentTitle: string
) {
  return {
    handleDragStart: (
      e: React.DragEvent,
      selection: { text: string; pageNumber: number }
    ) => {
      const data: DragData = {
        sourceType: 'pdf',
        sourceId: documentId,
        sourceTitle: documentTitle,
        pageNumber: selection.pageNumber,
        content: selection.text,
      };

      e.dataTransfer.setData('application/json', JSON.stringify(data));
      e.dataTransfer.effectAllowed = 'copy';

      // 自定义拖拽预览
      const preview = document.createElement('div');
      preview.textContent =
        selection.text.length > 50
          ? selection.text.substring(0, 50) + '...'
          : selection.text;
      preview.style.cssText = `
        position: absolute;
        top: -1000px;
        padding: 8px 12px;
        background: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 13px;
        max-width: 200px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      `;
      document.body.appendChild(preview);
      e.dataTransfer.setDragImage(preview, 0, 0);

      // 清理
      setTimeout(() => document.body.removeChild(preview), 0);
    },
  };
}
```

### 4. SourcePanel.tsx 改动

**文件**: `app/frontend/src/components/studio/SourcePanel.tsx`

需要替换的代码段：

```diff
- // PDF Viewer
- import { Document, Page, pdfjs } from 'react-pdf';
- import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
- import 'react-pdf/dist/esm/Page/TextLayer.css';
- 
- // Set worker
- pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

+ // PDF Viewer (pdfjs-dist full viewer)
+ import { PDFViewerWrapper, SelectionManager, HighlightOverlay, createDragHandler } from '@/components/pdf';
+ import '@/styles/pdf-viewer.css';
```

替换渲染部分 (原 933-945 行)：

```diff
- <Document
-   file={fileUrl}
-   onLoadSuccess={onDocumentLoadSuccess}
-   loading={<Typography variant="body2" sx={{ mt: 4 }}>Loading PDF...</Typography>}
-   error={<Typography variant="body2" color="error" sx={{ mt: 4 }}>Failed to load PDF</Typography>}
- >
-   <Page 
-     pageNumber={pageNumber} 
-     renderTextLayer={true}
-     renderAnnotationLayer={true}
-     width={width - 40}
-   />
- </Document>

+ <PDFViewerWrapper
+   fileUrl={fileUrl}
+   pageNumber={pageNumber}
+   width={width - 40}
+   onPageChange={setPageNumber}
+   onDocumentLoad={setNumPages}
+   onTextSelect={setTextSelection}
+   highlightText={sourceNavigation?.searchText}
+ />
+ <HighlightOverlay
+   selection={textSelection}
+   containerRef={pageRef}
+ />
+ {textSelection && (
+   <DraggableSelectionHandle
+     selection={textSelection}
+     onDragStart={(e) => dragHandler.handleDragStart(e, textSelection)}
+   />
+ )}
```

### 5. 样式文件

**文件**: `app/frontend/src/styles/pdf-viewer.css`

```css
/* PDF Viewer 容器 */
.pdf-viewer-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #f5f5f5;
}

/* 覆盖 pdfjs 默认样式 */
.pdfViewer .page {
  margin: 16px auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

/* 文本层优化 */
.pdfViewer .textLayer {
  opacity: 0.3;
}

.pdfViewer .textLayer ::selection {
  background: rgba(59, 130, 246, 0.3);
}

/* 高亮动画 */
@keyframes highlightPulse {
  0% { background-color: rgba(255, 235, 59, 0.6); }
  50% { background-color: rgba(255, 235, 59, 0.3); }
  100% { background-color: rgba(255, 235, 59, 0.6); }
}

.search-highlight {
  animation: highlightPulse 1.5s ease-in-out infinite;
}
```

---

## 实现步骤

| 步骤 | 任务 | 预估时间 |
|------|------|----------|
| 1 | 创建 pdf 组件目录和类型定义 | 0.5天 |
| 2 | 实现 PDFViewerWrapper (pdfjs PDFViewer 封装) | 1天 |
| 3 | 实现 SelectionManager 选择状态管理 | 0.5天 |
| 4 | 实现 HighlightOverlay 高亮渲染层 | 0.5天 |
| 5 | 实现 DragHandler 拖拽逻辑 | 0.5天 |
| 6 | 重构 SourcePanel.tsx 使用新 PDF 组件 | 1天 |
| 7 | 添加样式文件和 TypeScript 类型支持 | 0.5天 |
| 8 | 测试和调试 (选择、高亮、拖拽、跳转) | 1-2天 |
| **总计** | | **5-7天** |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| pdfjs-dist/web/pdf_viewer 模块导入问题 | 高 | 使用动态导入，确保客户端渲染 |
| SSR 兼容性 | 中 | 使用 `next/dynamic` 禁用 SSR |
| 样式冲突 | 低 | 使用 scoped CSS 或 CSS Modules |
| 性能问题 | 中 | 实现虚拟滚动，按需渲染页面 |

### Next.js SSR 处理

```typescript
// 动态导入，禁用 SSR
import dynamic from 'next/dynamic';

const PDFViewerWrapper = dynamic(
  () => import('@/components/pdf/PDFViewerWrapper'),
  { ssr: false, loading: () => <div>Loading PDF viewer...</div> }
);
```

---

## 后续扩展

完成基础迁移后，可考虑以下增强功能：

1. **持久化高亮标注** - 将用户的高亮保存到后端
2. **批注功能** - 支持在 PDF 上添加注释
3. **缩略图导航** - 页面缩略图快速跳转
4. **搜索功能** - PDF 内文本搜索
5. **多文档对比** - 并排查看多个 PDF


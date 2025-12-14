'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Box, Menu, MenuItem, TextField, Button, IconButton, Paper, Snackbar, Alert, Slide, Tooltip } from '@mui/material';
import { Edit2, Trash2, X, AlertCircle } from 'lucide-react';
import HighlightOverlay, { HighlightPosition } from './HighlightOverlay';
import SelectionToolbar, { HighlightColor } from './SelectionToolbar';
import { highlightsApi, HighlightResponse } from '@/lib/api';

// 扩展 Highlight 类型以包含 rects
type Highlight = HighlightResponse & {
  rects?: DOMRect[];
};

interface PDFViewerProps {
  documentId: string;
  content: React.ReactNode; // PDF 内容（可以是文本或其他格式）
  onHighlightCreate?: (highlight: Highlight) => void;
  onHighlightUpdate?: (highlight: Highlight) => void;
  onHighlightDelete?: (highlightId: string) => void;
}

export default function PDFViewer({
  documentId,
  content,
  onHighlightCreate,
  onHighlightUpdate,
  onHighlightDelete,
}: PDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selection, setSelection] = useState<Selection | null>(null);
  const [toolbarPosition, setToolbarPosition] = useState<{ x: number; y: number } | null>(null);
  const [highlightMenuAnchor, setHighlightMenuAnchor] = useState<{ x: number; y: number } | null>(null);
  const [selectedHighlight, setSelectedHighlight] = useState<Highlight | null>(null);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [isCreatingHighlight, setIsCreatingHighlight] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pendingHighlights, setPendingHighlights] = useState<Map<string, { highlight: Highlight; retryCount: number }>>(new Map());
  // 保存待添加批注的选中信息（用于在对话框打开后选择可能被清除的情况）
  const [pendingNoteSelection, setPendingNoteSelection] = useState<{
    text: string;
    position: HighlightPosition;
  } | null>(null);

  // 加载高亮列表
  useEffect(() => {
    if (!documentId) return;

    const loadHighlights = async () => {
      try {
        const highlightsList = await highlightsApi.list(documentId);
        // 转换 API 返回的数据为包含 rects 的格式
        // 注意：如果后端存储了 rects，需要在这里恢复
        // 目前先设置为空数组，等待用户重新选择时计算
        setHighlights(highlightsList.map((h) => ({ ...h, rects: [] })));
      } catch (error) {
        console.error('Failed to load highlights:', error);
        // 如果 API 不存在，设置为空数组（开发阶段）
        setHighlights([]);
      }
    };

    loadHighlights();
  }, [documentId]);

  // 计算选中文本的位置信息（用于高亮渲染）
  const calculateSelectionPosition = useCallback((): HighlightPosition | null => {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return null;

    const range = sel.getRangeAt(0);
    const text = sel.toString().trim();

    if (!text || !containerRef.current) return null;

    // 检查选中内容是否在容器内
    if (!containerRef.current.contains(range.commonAncestorContainer)) {
      return null;
    }

    // 获取所有文本节点和位置
    const rects: DOMRect[] = [];
    const containerRect = containerRef.current.getBoundingClientRect();
    const scrollLeft = containerRef.current.scrollLeft;
    const scrollTop = containerRef.current.scrollTop;

    // 获取所有选中区域的矩形，并转换为相对于容器内容的坐标（包含滚动偏移）
    // 这样存储的 rects 是“内容坐标系”，不会随着滚动改变；
    // 在滚动容器中使用 position:absolute 渲染时，直接使用该坐标即可随内容一起滚动。
    for (let i = 0; i < range.getClientRects().length; i++) {
      const clientRect = range.getClientRects().item(i);
      if (clientRect) {
        // clientRect 是相对于视口的 -> 转换为相对于容器内容的位置（加上当前滚动偏移）
        const relativeLeft = clientRect.left - containerRect.left + scrollLeft;
        const relativeTop = clientRect.top - containerRect.top + scrollTop;
        
        const relativeRect = new DOMRect(
          relativeLeft,
          relativeTop,
          clientRect.width,
          clientRect.height
        );
        rects.push(relativeRect);
      }
    }

    if (rects.length === 0) return null;

    // 计算页码（简化处理，假设单页）
    const pageNumber = 1; // TODO: 如果有多页，需要根据滚动位置计算

    // 计算文本偏移量（相对于容器开始）
    const textContent = containerRef.current.textContent || '';
    const startOffset = textContent.indexOf(text);
    const endOffset = startOffset + text.length;

    return {
      pageNumber,
      startOffset,
      endOffset,
      rects,
    };
  }, []);

  // 处理鼠标抬起事件（文本选择）
  const handleMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) {
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
      return;
    }

    const text = sel.toString().trim();
    if (!text) {
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
      return;
    }

    const position = calculateSelectionPosition();
    if (!position) {
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
      return;
    }

    // 工具栏位置需要使用视口坐标（因为 SelectionToolbar 使用 position:fixed）
    const range = sel.getRangeAt(0);
    const clientRects = range.getClientRects();
    if (clientRects.length === 0) {
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
      return;
    }

    // 计算工具栏位置（选中区域中心上方，使用 clientRect 的视口坐标）
    const firstClientRect = clientRects[0];
    const lastClientRect = clientRects[clientRects.length - 1];
    const centerX = (firstClientRect.left + lastClientRect.right) / 2;
    const centerY = Math.min(firstClientRect.top, lastClientRect.top);

    setSelectedText(text);
    setSelection(sel);
    setToolbarPosition({ x: centerX, y: centerY });
  }, [calculateSelectionPosition]);

  // 处理颜色选择
  const handleColorSelect = useCallback(
    async (color: HighlightColor) => {
      if (!selectedText || !selection || !toolbarPosition || isCreatingHighlight) return;

      setIsCreatingHighlight(true);
      const position = calculateSelectionPosition();
      if (!position) {
        setIsCreatingHighlight(false);
        return;
      }

      // 立即创建本地高亮对象（乐观更新）
      const tempId = `local-${Date.now()}`;
      const highlightWithRects: Highlight = {
        id: tempId,
        documentId,
        pageNumber: position.pageNumber,
        startOffset: position.startOffset,
        endOffset: position.endOffset,
        color,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        rects: position.rects,
      };

      // 立即更新状态，让高亮立即显示
      setHighlights((prev) => [...prev, highlightWithRects]);
      
      // 清除选择
      window.getSelection()?.removeAllRanges();
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
      setIsCreatingHighlight(false);

      // 记录待处理的高亮
      setPendingHighlights((prev) => {
        const newMap = new Map(prev);
        newMap.set(tempId, { highlight: highlightWithRects, retryCount: 0 });
        return newMap;
      });

      // 异步调用 API（不阻塞 UI）
      const createHighlightWithRetry = async (retryCount = 0): Promise<void> => {
        try {
          const newHighlight = await highlightsApi.create(documentId, {
            pageNumber: position.pageNumber,
            startOffset: position.startOffset,
            endOffset: position.endOffset,
            color,
            rects: position.rects.map((rect) => ({
              left: rect.left,
              top: rect.top,
              width: rect.width,
              height: rect.height,
              right: rect.right,
              bottom: rect.bottom,
            })),
          });

          // API 成功返回后，更新为服务器返回的 ID
          setHighlights((prev) =>
            prev.map((h) => (h.id === tempId ? { ...newHighlight, rects: position.rects } : h))
          );

          // 移除待处理记录
          setPendingHighlights((prev) => {
            const newMap = new Map(prev);
            newMap.delete(tempId);
            return newMap;
          });

          onHighlightCreate?.({ ...newHighlight, rects: position.rects });
        } catch (error: any) {
          console.error('Failed to create highlight:', error);

          // 如果是网络错误且重试次数少于 2 次，自动重试
          const isNetworkError = !error.status || error.status >= 500 || error.message?.includes('fetch');
          if (isNetworkError && retryCount < 2) {
            console.log(`Retrying highlight creation (attempt ${retryCount + 1}/2)...`);
            await new Promise((resolve) => setTimeout(resolve, 1000 * (retryCount + 1))); // 递增延迟
            return createHighlightWithRetry(retryCount + 1);
          }

          // 重试失败或非网络错误，显示错误提示
          setPendingHighlights((prev) => {
            const newMap = new Map(prev);
            const pending = newMap.get(tempId);
            if (pending) {
              newMap.set(tempId, { ...pending, retryCount: retryCount + 1 });
            }
            return newMap;
          });

          const errorMsg = error.status === 404
            ? '高亮功能暂不可用'
            : error.status >= 500
            ? '服务器错误，请稍后重试'
            : error.message || '创建高亮失败，请稍后重试';

          setErrorMessage(errorMsg);
        }
      };

      createHighlightWithRetry();
    },
    [selectedText, selection, toolbarPosition, documentId, calculateSelectionPosition, onHighlightCreate, isCreatingHighlight]
  );

  // 处理添加批注
  const handleAddNote = useCallback(() => {
    if (!selectedText || !toolbarPosition) return;
    
    const position = calculateSelectionPosition();
    if (!position) return;
    
    // 保存选中信息，以便在对话框打开后即使选择被清除也能使用
    setPendingNoteSelection({
      text: selectedText,
      position,
    });
    setNoteDialogOpen(true);
  }, [selectedText, toolbarPosition, calculateSelectionPosition]);

  // 保存批注
  const handleSaveNote = useCallback(async () => {
    // 使用保存的选中信息，而不是依赖可能已经被清除的状态
    if (!pendingNoteSelection) return;

    const { text: savedText, position } = pendingNoteSelection;

    // 立即创建本地高亮对象（乐观更新）
    const tempId = `local-${Date.now()}`;
    const highlightWithRects: Highlight = {
      id: tempId,
      documentId,
      pageNumber: position.pageNumber,
      startOffset: position.startOffset,
      endOffset: position.endOffset,
      color: 'yellow',
      note: noteText,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      rects: position.rects,
    };

    // 立即更新状态，让高亮立即显示
    setHighlights((prev) => [...prev, highlightWithRects]);

    // 清除选择
    window.getSelection()?.removeAllRanges();
    setToolbarPosition(null);
    setSelectedText('');
    setSelection(null);
    setNoteDialogOpen(false);
    setNoteText('');
    setPendingNoteSelection(null); // 清除保存的选中信息

    // 记录待处理的高亮
    setPendingHighlights((prev) => {
      const newMap = new Map(prev);
      newMap.set(tempId, { highlight: highlightWithRects, retryCount: 0 });
      return newMap;
    });

    // 异步调用 API（不阻塞 UI）
    const createHighlightWithRetry = async (retryCount = 0): Promise<void> => {
      try {
        const newHighlight = await highlightsApi.create(documentId, {
          pageNumber: position.pageNumber,
          startOffset: position.startOffset,
          endOffset: position.endOffset,
          color: 'yellow',
          note: noteText,
          rects: position.rects.map((rect) => ({
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
            right: rect.right,
            bottom: rect.bottom,
          })),
        });

        // API 成功返回后，更新为服务器返回的 ID
        setHighlights((prev) =>
          prev.map((h) => (h.id === tempId ? { ...newHighlight, rects: position.rects } : h))
        );

        // 移除待处理记录
        setPendingHighlights((prev) => {
          const newMap = new Map(prev);
          newMap.delete(tempId);
          return newMap;
        });

        onHighlightCreate?.({ ...newHighlight, rects: position.rects });
      } catch (error: any) {
        console.error('Failed to create highlight with note:', error);

        // 如果是网络错误且重试次数少于 2 次，自动重试
        const isNetworkError = !error.status || error.status >= 500 || error.message?.includes('fetch');
        if (isNetworkError && retryCount < 2) {
          console.log(`Retrying highlight creation with note (attempt ${retryCount + 1}/2)...`);
          await new Promise((resolve) => setTimeout(resolve, 1000 * (retryCount + 1)));
          return createHighlightWithRetry(retryCount + 1);
        }

        // 重试失败或非网络错误，显示错误提示
        setPendingHighlights((prev) => {
          const newMap = new Map(prev);
          const pending = newMap.get(tempId);
          if (pending) {
            newMap.set(tempId, { ...pending, retryCount: retryCount + 1 });
          }
          return newMap;
        });

        const errorMsg = error.status === 404
          ? '高亮功能暂不可用'
          : error.status >= 500
          ? '服务器错误，请稍后重试'
          : error.message || '创建高亮失败，请稍后重试';

        setErrorMessage(errorMsg);
      }
    };

    createHighlightWithRetry();
  }, [pendingNoteSelection, noteText, documentId, onHighlightCreate]);

  // 处理复制
  const handleCopy = useCallback(() => {
    if (selectedText) {
      navigator.clipboard.writeText(selectedText);
      // 清除选择
      window.getSelection()?.removeAllRanges();
      setToolbarPosition(null);
      setSelectedText('');
      setSelection(null);
    }
  }, [selectedText]);

  // 处理高亮点击（编辑菜单位置与添加高亮工具栏风格一致：悬浮在文字上方，不遮挡内容）
  const handleHighlightClick = useCallback(
    (highlight: Highlight, event?: React.MouseEvent | MouseEvent) => {
      console.log('Highlight clicked:', highlight, event);
      setSelectedHighlight(highlight);

      if (highlight.rects && highlight.rects.length > 0 && containerRef.current) {
        // 使用高亮区域的矩形计算菜单位置（视口坐标）
        const containerRect = containerRef.current.getBoundingClientRect();
        const firstRect = highlight.rects[0];
        const lastRect = highlight.rects[highlight.rects.length - 1];

        const centerX = containerRect.left + (firstRect.left + lastRect.right) / 2;
        // 取文本顶部再往上偏移一点，让菜单像 SelectionToolbar 一样悬浮在上方
        const textTopInViewport = containerRect.top + Math.min(firstRect.top, lastRect.top);
        const offset = 48; // 与 SelectionToolbar 视觉高度接近的上移距离
        const anchorY = textTopInViewport - offset;

        setHighlightMenuAnchor({ x: centerX, y: anchorY });
        console.log('Menu anchor set above highlight:', { x: centerX, y: anchorY });
      } else if (event) {
        // 兜底：没有 rects 时退回到点击位置
        const mouseEvent = event as MouseEvent;
        setHighlightMenuAnchor({ x: mouseEvent.clientX, y: mouseEvent.clientY - 40 });
        console.log('Menu anchor fallback to mouse position:', {
          x: mouseEvent.clientX,
          y: mouseEvent.clientY - 40,
        });
      } else {
        console.warn('Highlight has no rects and no event, cannot show menu');
      }
    },
    []
  );

  // 处理编辑高亮
  const handleEditHighlight = useCallback(() => {
    if (!selectedHighlight) return;
    setNoteText(selectedHighlight.note || '');
    setNoteDialogOpen(true);
    setHighlightMenuAnchor(null);
  }, [selectedHighlight]);

  // 保存编辑的批注
  const handleSaveEditNote = useCallback(async () => {
    if (!selectedHighlight) {
      console.warn('No selected highlight to save note');
      return;
    }

    const originalNote = selectedHighlight.note;

    // 乐观更新：立即更新本地状态
    const updatedWithRects: Highlight = {
      ...selectedHighlight,
      note: noteText,
      updatedAt: new Date().toISOString(),
      rects: selectedHighlight.rects,
    };

    setHighlights((prev) =>
      prev.map((h) => (h.id === selectedHighlight.id ? updatedWithRects : h))
    );

    setNoteDialogOpen(false);
    setNoteText('');
    const savedHighlight = selectedHighlight;
    setSelectedHighlight(null);

    // 异步调用 API
    try {
      const updated = await highlightsApi.update(documentId, savedHighlight.id, {
        note: noteText,
      });

      // API 成功，更新为服务器返回的数据
      const serverUpdated: Highlight = {
        ...updated,
        rects: savedHighlight.rects,
      };
      setHighlights((prev) =>
        prev.map((h) => (h.id === savedHighlight.id ? serverUpdated : h))
      );
      onHighlightUpdate?.(serverUpdated);
    } catch (error: any) {
      console.error('Failed to update highlight note:', error);

      // API 失败，回滚到原来的批注
      setHighlights((prev) =>
        prev.map((h) =>
          h.id === savedHighlight.id
            ? { ...savedHighlight, note: originalNote }
            : h
        )
      );

      const errorMsg = error.status === 404
        ? '高亮功能暂不可用'
        : error.status >= 500
        ? '服务器错误，批注修改已回滚'
        : error.message || '保存批注失败，已回滚';

      setErrorMessage(errorMsg);
    }
  }, [selectedHighlight, noteText, documentId, onHighlightUpdate]);

  // 处理删除高亮
  const handleDeleteHighlight = useCallback(async () => {
    if (!selectedHighlight) return;

    const deletedHighlight = selectedHighlight;

    // 乐观更新：立即从 UI 中移除
    setHighlights((prev) => prev.filter((h) => h.id !== deletedHighlight.id));
    setHighlightMenuAnchor(null);
    setSelectedHighlight(null);

    // 异步调用 API
    try {
      await highlightsApi.delete(documentId, deletedHighlight.id);
      onHighlightDelete?.(deletedHighlight.id);
    } catch (error: any) {
      console.error('Failed to delete highlight:', error);

      // API 失败，恢复高亮
      setHighlights((prev) => [...prev, deletedHighlight]);

      const errorMsg = error.status === 404
        ? '高亮功能暂不可用'
        : error.status >= 500
        ? '服务器错误，删除操作已回滚'
        : error.message || '删除高亮失败，已回滚';

      setErrorMessage(errorMsg);
    }
  }, [selectedHighlight, documentId, onHighlightDelete]);

  // 处理修改颜色
  const handleChangeColor = useCallback(
    async (color: HighlightColor) => {
      if (!selectedHighlight) {
        console.warn('No selected highlight to change color');
        return;
      }

      console.log('Changing highlight color:', selectedHighlight.id, 'to', color);

      // --- 乐观更新：先在本地立即改颜色，再异步调接口 ---
      const previousHighlight = selectedHighlight;

      // 本地立即更新选中高亮和高亮列表
      const optimisticallyUpdated: Highlight = {
        ...selectedHighlight,
        color,
        updatedAt: new Date().toISOString(),
      };
      setSelectedHighlight(optimisticallyUpdated);
      setHighlights((prev) =>
        prev.map((h) => (h.id === selectedHighlight.id ? optimisticallyUpdated : h))
      );

      try {
        const updated = await highlightsApi.update(documentId, selectedHighlight.id, {
          color,
        }).catch((error) => {
          // 如果 API 不存在，更新本地状态（开发阶段）
          console.warn('Highlight API not available, updating local highlight:', error);
          return {
            ...selectedHighlight,
            color,
            updatedAt: new Date().toISOString(),
          } as HighlightResponse;
        });

        const updatedWithRects: Highlight = {
          ...updated,
          rects: selectedHighlight.rects, // 保留原有的 rects
        };

        // 用后端返回的数据再覆盖一次（确保时间戳等一致）
        setHighlights((prev) =>
          prev.map((h) => (h.id === selectedHighlight.id ? updatedWithRects : h))
        );
        onHighlightUpdate?.(updatedWithRects);

        setHighlightMenuAnchor(null);
        setSelectedHighlight(null);
      } catch (error: any) {
        console.error('Failed to update highlight color:', error);

        // 接口失败时回滚颜色
        setHighlights((prev) =>
          prev.map((h) => (h.id === previousHighlight.id ? previousHighlight : h))
        );
        setSelectedHighlight(previousHighlight);

        const errorMsg = error.status === 404
          ? '高亮颜色修改暂不可用'
          : error.status >= 500
          ? '服务器错误，颜色修改已回滚'
          : error.message || '更新高亮颜色失败，已回滚';
        setErrorMessage(errorMsg);
      }
    },
    [selectedHighlight, documentId, onHighlightUpdate]
  );

  // 为高亮添加 rects 信息（从存储的数据恢复）
  // 注意：目前高亮创建时会保存 rects，但如果页面重新加载，需要重新计算
  // 这需要后端存储 rects 数据，或者前端根据 startOffset/endOffset 重新计算
  const highlightsWithRects = highlights.map((h) => {
    // 确保 rects 存在且是 DOMRect 数组
    if (h.rects && h.rects.length > 0) {
      // 如果 rects 是普通对象，转换为 DOMRect
      const rects = h.rects.map((rect: any) => {
        if (rect instanceof DOMRect) {
          return rect;
        }
        // 从普通对象创建 DOMRect（rect 可能是序列化的对象）
        if (rect && typeof rect === 'object' && rect.left !== undefined && rect.top !== undefined) {
          return new DOMRect(rect.left, rect.top, rect.width || 0, rect.height || 0);
        }
        return rect;
      });
      return { ...h, rects };
    }
    return h;
  });

  return (
    <Box
      ref={containerRef}
      onMouseUp={handleMouseUp}
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'auto',
        userSelect: 'text',
      }}
    >
      {/* PDF 内容 */}
      <Box sx={{ position: 'relative', zIndex: 1 }}>{content}</Box>

      {/* 高亮覆盖层 */}
      <HighlightOverlay
        highlights={highlightsWithRects.filter((h) => h.rects && h.rects.length > 0)}
        containerRef={containerRef}
        onHighlightClick={(highlight, event) => {
          console.log('HighlightOverlay onHighlightClick called:', highlight, event);
          handleHighlightClick(highlight, event);
        }}
      />

      {/* 选择工具栏 */}
      {toolbarPosition && (
        <SelectionToolbar
          position={toolbarPosition}
          selectedText={selectedText}
          onColorSelect={handleColorSelect}
          onAddNote={handleAddNote}
          onCopy={handleCopy}
          onClose={() => {
            window.getSelection()?.removeAllRanges();
            setToolbarPosition(null);
            setSelectedText('');
            setSelection(null);
          }}
        />
      )}

      {/* 高亮编辑菜单（浅色 & 与整体风格统一） */}
      <Menu
        open={highlightMenuAnchor !== null && selectedHighlight !== null}
        onClose={() => {
          setHighlightMenuAnchor(null);
          setSelectedHighlight(null);
        }}
        anchorReference="anchorPosition"
        anchorPosition={
          highlightMenuAnchor !== null
            ? { top: highlightMenuAnchor.y, left: highlightMenuAnchor.x }
            : undefined
        }
        PaperProps={{
          sx: {
            // 与 SelectionToolbar 保持一致的卡片风格
            borderRadius: 3,
            minWidth: 'auto',
            px: 1,
            py: 0.5,
            boxShadow: '0 2px 8px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08)',
            border: '1px solid',
            borderColor: '#E5E7EB',
            bgcolor: '#FFFFFF',
            backdropFilter: 'blur(8px)',
          },
        }}
        MenuListProps={{
          sx: {
            display: 'flex',
            alignItems: 'center',
            gap: 0.25,
            px: 0,
            py: 0,
          },
        }}
        transformOrigin={{ horizontal: 'center', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
      >
        {/* 颜色点：主用颜色表达，保持简洁 */}
        {(['yellow', 'green', 'blue', 'pink'] as HighlightColor[]).map((color) => (
          <MenuItem
            key={color}
            onClick={() => selectedHighlight && handleChangeColor(color)}
            disableGutters
            sx={{
              mx: 0.25,
              p: 0,
              borderRadius: 2,
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 28,
                height: 28,
                minWidth: 28,
                bgcolor:
                  color === 'yellow'
                    ? '#FFEB3B'
                    : color === 'green'
                    ? '#4CAF50'
                    : color === 'blue'
                    ? '#2196F3'
                    : '#E91E63',
                border: '1.5px solid',
                borderColor:
                  selectedHighlight?.color === color ? '#171717' : 'transparent',
                borderRadius: 1.5,
                transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  bgcolor:
                    color === 'yellow'
                      ? '#FFD700'
                      : color === 'green'
                      ? '#45A049'
                      : color === 'blue'
                      ? '#1976D2'
                      : '#C2185B',
                  borderColor: '#171717',
                  transform: 'scale(1.08)',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                },
                '&:active': {
                  transform: 'scale(0.95)',
                },
              }}
            />
          </MenuItem>
        ))}

        {/* 编辑批注：图标 + 浅色 hover，保持简洁 */}
        <Tooltip title={selectedHighlight?.note ? '编辑批注' : '添加批注'} arrow>
          <MenuItem
            onClick={handleEditHighlight}
            sx={{
              mx: 0.25,
              p: 0,
              borderRadius: 2,
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 28,
                height: 28,
                minWidth: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 1.5,
                color: 'text.secondary',
                transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  bgcolor: '#F3F4F6',
                  color: 'text.primary',
                  transform: 'scale(1.05)',
                },
                '&:active': {
                  transform: 'scale(0.95)',
                },
              }}
            >
              <Edit2 size={14} />
            </Box>
          </MenuItem>
        </Tooltip>

        {/* 删除：高亮红色图标，仍保持简洁 */}
        <Tooltip title="删除高亮" arrow>
          <MenuItem
            onClick={handleDeleteHighlight}
            sx={{
              mx: 0.25,
              p: 0,
              borderRadius: 2,
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 28,
                height: 28,
                minWidth: 28,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 1.5,
                color: '#EF4444',
                transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  bgcolor: '#FEE2E2',
                  transform: 'scale(1.05)',
                },
                '&:active': {
                  transform: 'scale(0.95)',
                },
              }}
            >
              <Trash2 size={14} />
            </Box>
          </MenuItem>
        </Tooltip>
      </Menu>

      {/* 批注对话框 */}
      {noteDialogOpen && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(0,0,0,0.5)',
            zIndex: 2000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 2,
          }}
          onClick={() => {
            setNoteDialogOpen(false);
            setNoteText('');
            setSelectedHighlight(null);
            setPendingNoteSelection(null);
          }}
        >
          <Paper
            elevation={0}
            sx={{
              width: '100%',
              maxWidth: 500,
              borderRadius: 3,
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              border: '1px solid',
              borderColor: '#E5E7EB',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ fontSize: 18, fontWeight: 600, color: 'text.primary' }}>
                  {selectedHighlight ? '编辑批注' : '添加批注'}
                </Box>
                <IconButton
                  size="small"
                  onClick={() => {
                    setNoteDialogOpen(false);
                    setNoteText('');
                    setSelectedHighlight(null);
                  }}
                  sx={{
                    color: 'text.secondary',
                    '&:hover': {
                      bgcolor: '#F3F4F6',
                    },
                  }}
                >
                  <X size={18} />
                </IconButton>
              </Box>

              <TextField
                multiline
                rows={5}
                placeholder="输入批注内容..."
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                fullWidth
                autoFocus
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    fontSize: 14,
                  },
                }}
              />

              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1.5, mt: 3 }}>
                <Button
                  onClick={() => {
                    setNoteDialogOpen(false);
                    setNoteText('');
                    setSelectedHighlight(null);
                  }}
                  sx={{
                    color: 'text.secondary',
                    '&:hover': {
                      bgcolor: '#F3F4F6',
                    },
                  }}
                >
                  取消
                </Button>
                <Button
                  variant="contained"
                  onClick={selectedHighlight ? handleSaveEditNote : handleSaveNote}
                  sx={{
                    bgcolor: '#171717',
                    color: '#FFFFFF',
                    '&:hover': {
                      bgcolor: '#000000',
                    },
                    borderRadius: 2,
                    px: 2.5,
                  }}
                >
                  保存
                </Button>
              </Box>
            </Box>
          </Paper>
        </Box>
      )}

      {/* 错误提示 Snackbar */}
      <Snackbar
        open={errorMessage !== null}
        autoHideDuration={6000}
        onClose={() => setErrorMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        TransitionComponent={Slide}
      >
        <Alert
          severity="error"
          onClose={() => setErrorMessage(null)}
          icon={<AlertCircle size={20} />}
          sx={{
            minWidth: 300,
            '& .MuiAlert-message': {
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            },
          }}
          action={
            pendingHighlights.size > 0 && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Button
                  size="small"
                  color="inherit"
                  onClick={() => {
                    // 重试所有待处理的高亮
                    pendingHighlights.forEach(({ highlight }, tempId) => {
                      const position = highlight.rects?.[0]
                        ? {
                            pageNumber: highlight.pageNumber,
                            startOffset: highlight.startOffset,
                            endOffset: highlight.endOffset,
                            rects: highlight.rects,
                          }
                        : null;

                      if (position) {
                        highlightsApi
                          .create(documentId, {
                            pageNumber: position.pageNumber,
                            startOffset: position.startOffset,
                            endOffset: position.endOffset,
                            color: highlight.color,
                            note: highlight.note,
                            rects: position.rects.map((rect) => ({
                              left: rect.left,
                              top: rect.top,
                              width: rect.width,
                              height: rect.height,
                              right: rect.right,
                              bottom: rect.bottom,
                            })),
                          })
                          .then((newHighlight) => {
                            setHighlights((prev) =>
                              prev.map((h) =>
                                h.id === tempId ? { ...newHighlight, rects: highlight.rects } : h
                              )
                            );
                            setPendingHighlights((prev) => {
                              const newMap = new Map(prev);
                              newMap.delete(tempId);
                              return newMap;
                            });
                          })
                          .catch(() => {
                            // 重试失败，保持待处理状态
                          });
                      }
                    });
                    setErrorMessage(null);
                  }}
                >
                  重试
                </Button>
                <Button
                  size="small"
                  color="inherit"
                  onClick={() => {
                    // 移除所有待处理的高亮
                    const tempIds = Array.from(pendingHighlights.keys());
                    setHighlights((prev) => prev.filter((h) => !tempIds.includes(h.id)));
                    setPendingHighlights(new Map());
                    setErrorMessage(null);
                  }}
                >
                  移除
                </Button>
              </Box>
            )
          }
        >
          {errorMessage}
          {pendingHighlights.size > 0 && (
            <Box component="span" sx={{ fontSize: '0.75rem', opacity: 0.8, ml: 1 }}>
              ({pendingHighlights.size} 个高亮待保存)
            </Box>
          )}
        </Alert>
      </Snackbar>
    </Box>
  );
}


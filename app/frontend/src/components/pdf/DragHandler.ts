import { DragData } from './types';

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
        z-index: 9999;
      `;
      document.body.appendChild(preview);
      e.dataTransfer.setDragImage(preview, 0, 0);

      // 清理
      setTimeout(() => document.body.removeChild(preview), 0);
    },
  };
}

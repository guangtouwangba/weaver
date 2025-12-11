import { TextSelection } from './types';

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
    // PDFJS text layer elements are usually inside a div with class 'page' or similar structure
    // We look for a closest parent with data-page-number attribute
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
    if (this.container) {
        this.container.removeEventListener('mouseup', this.handleMouseUp);
    }
  }
}

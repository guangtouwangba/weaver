from typing import Any, List
from modules.schemas import Document
from modules.file_loader.pdf.base import PDFLoadStrategy, register_pdf_load_strategy, StrategyName


@register_pdf_load_strategy(StrategyName.UNSTRUCTURED)
class UnstructuredPDFLoadStrategy(PDFLoadStrategy):
    def load(self, *args, **kwargs) -> List[Document]:
        pass
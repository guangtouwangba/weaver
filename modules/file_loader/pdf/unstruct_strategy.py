from typing import Any, List

from modules.file_loader.pdf.base import (
    PDFLoadStrategy,
    StrategyName,
    register_pdf_load_strategy,
)
from modules.schemas import Document


@register_pdf_load_strategy(StrategyName.UNSTRUCTURED)
class UnstructuredPDFLoadStrategy(PDFLoadStrategy):
    def load(self, *args, **kwargs) -> List[Document]:
        pass

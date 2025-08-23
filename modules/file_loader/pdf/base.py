from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List


class StrategyName(Enum):
    UNSTRUCTURED = "unstructured"
    PYPDF = "pypdf"
    PDFMINER = "pdfminer"
    FITZ = "fitz"
    SLATE = "slate"


class PDFLoadStrategy(ABC):

    @abstractmethod
    def load(self, *args, **kwargs) -> List[Any]:
        pass


class PDFLoadStrategyFactory:

    strategies = {}

    @staticmethod
    def register_strategy(strategy_name: str, strategy_cls: PDFLoadStrategy) -> None:
        PDFLoadStrategyFactory.strategies[strategy_name] = strategy_cls

    @staticmethod
    def get_strategy(strategy_name: StrategyName) -> PDFLoadStrategy:
        strategy_cls = PDFLoadStrategyFactory.strategies.get(strategy_name)
        if not strategy_cls:
            raise ValueError(f"Strategy {strategy_name} not found")
        return strategy_cls()


def register_pdf_load_strategy(strategy_name: StrategyName):
    def decorator(strategy_cls: PDFLoadStrategy):
        PDFLoadStrategyFactory.register_strategy(strategy_name, strategy_cls)
        return strategy_cls

    return decorator

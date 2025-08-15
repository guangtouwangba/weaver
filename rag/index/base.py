from abc import ABC
from abc import abstractmethod


class Index(ABC):
    def __init__(self, document: str):
        self.document = document

    @abstractmethod
    def index(self):
        pass
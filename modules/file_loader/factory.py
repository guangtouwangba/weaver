from typing import List, Union
from .base import IFileLoader
from ..schemas.enums import ContentType
import inspect


class FileLoaderFactory:
    """
    _loaders :   dict[str, IFileLoader] = {}
    """

    _loaders = {}

    @classmethod
    def register(cls, content_type: ContentType, file_loader_class):
        """
        Register file loader

        Args:
            file_loader_class: Class which implements IFileLoader
            content_type: ContentType enum value that the loader supports
        """
        # If passed a class, store class; if passed an instance, store instance
        cls._loaders[content_type] = file_loader_class
        
        # Get loader name for printing
        if hasattr(file_loader_class, 'loader_name'):
            if inspect.isclass(file_loader_class):
                # If it's a class, temporarily create instance to get name
                try:
                    temp_instance = file_loader_class()
                    loader_name = temp_instance.loader_name
                except:
                    loader_name = file_loader_class.__name__
            else:
                # If it's an instance, get name directly
                loader_name = file_loader_class.loader_name
        else:
            loader_name = file_loader_class.__name__ if inspect.isclass(file_loader_class) else str(file_loader_class)
            
        print(f"Registered file loader: {loader_name}")


    @classmethod
    def get_loader(cls, content_type: ContentType) -> IFileLoader:
        """
        Return the file loader for the given content type
        """
        if content_type not in cls._loaders:
            raise ValueError(f"No file loader registered for content type: {content_type}")
        
        loader_class_or_instance = cls._loaders[content_type]
        
        # If stored as class, create instance; if stored as instance, return directly
        if inspect.isclass(loader_class_or_instance):
            return loader_class_or_instance()
        else:
            return loader_class_or_instance




def register_file_loader(content_type: ContentType):
    """
    Decorator to register a file loader class
    """
    def decorator(file_loader: IFileLoader):
        FileLoaderFactory.register(content_type, file_loader)
        return file_loader
    return decorator

def register_multi_type_file_loader(content_types: List[ContentType]):
    """
    Decorator to register a file loader class for multiple content types
    """
    def decorator(file_loader: IFileLoader):
        for content_type in content_types:
            FileLoaderFactory.register(content_type, file_loader)
        return file_loader
    return decorator

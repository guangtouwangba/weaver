import inspect
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel

from modules.schemas.enums import ContentType

from .base import IFileLoader

logger = logging.getLogger(__name__)


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
        if hasattr(file_loader_class, "loader_name"):
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
            loader_name = (
                file_loader_class.__name__
                if inspect.isclass(file_loader_class)
                else str(file_loader_class)
            )

        logger.info(
            f"Registered file loader '{loader_name}' for content type '{content_type}'"
        )

    @classmethod
    def get_loader(cls, content_type: ContentType) -> IFileLoader:
        """
        Return the file loader for the given content type
        """
        if content_type not in cls._loaders:
            raise ValueError(
                f"No file loader registered for content type: {content_type}"
            )

        loader_class_or_instance = cls._loaders[content_type]

        # If stored as class, create instance; if stored as instance, return directly
        if inspect.isclass(loader_class_or_instance):
            return loader_class_or_instance()
        else:
            return loader_class_or_instance

    @classmethod
    async def load_document(
        cls, request, auto_detect: bool = True, fallback_to_text: bool = True
    ):
        """
        One-step document loading with automatic type detection and fallback

        Args:
            request: Document loading request with file_path and other metadata
            auto_detect: Whether to auto-detect content type from file extension/mime type
            fallback_to_text: Whether to fallback to text loader if specific loader fails

        Returns:
            Loaded document object

        Raises:
            ValueError: If no suitable loader found and fallback disabled
        """
        content_type = request.content_type

        # Auto-detect content type if not provided or if auto_detect is enabled
        if auto_detect and hasattr(request, "file_path"):
            detected_type = cls._detect_content_type(request.file_path)
            if detected_type:
                content_type = detected_type
                request.content_type = content_type.value

        # Try to load with the determined content type
        try:
            loader = cls.get_loader(content_type)
            document = await loader.load_document(request)

            # Add metadata about the loader used
            if hasattr(document, "metadata"):
                document.metadata.update(
                    {
                        "loader_type": loader.__class__.__name__,
                        "content_type_used": content_type.value,
                        "auto_detected": auto_detect,
                    }
                )

            logger.info(
                f"Successfully loaded document using {loader.__class__.__name__}"
            )
            return document

        except (ValueError, Exception) as e:
            if not fallback_to_text:
                raise

            logger.warning(
                f"Primary loader failed for content type {content_type}, "
                f"trying text fallback: {e}"
            )

            # Fallback to text loader
            try:
                text_loader = cls.get_loader(ContentType.TXT)
                original_content_type = request.content_type
                request.content_type = ContentType.TXT.value

                document = await text_loader.load_document(request)

                # Add fallback metadata
                if hasattr(document, "metadata"):
                    document.metadata.update(
                        {
                            "loader_type": text_loader.__class__.__name__,
                            "content_type_used": ContentType.TXT.value,
                            "original_content_type": original_content_type,
                            "fallback_used": True,
                            "fallback_reason": str(e),
                        }
                    )

                logger.info(f"Successfully loaded document using text fallback")
                return document

            except Exception as fallback_error:
                logger.error(
                    f"Both primary and fallback loaders failed: {fallback_error}"
                )
                raise ValueError(
                    f"Failed to load document with content type {content_type} "
                    f"and text fallback: {fallback_error}"
                ) from fallback_error

    @classmethod
    def _detect_content_type(cls, file_path: Union[str, Path]) -> Optional[ContentType]:
        """
        Auto-detect content type from file extension and mime type

        Args:
            file_path: Path to the file

        Returns:
            Detected ContentType or None if unknown
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Get file extension
        extension = file_path.suffix.lower()

        # Map common extensions to content types
        extension_map = {
            ".txt": ContentType.TXT,
            ".md": ContentType.TXT,
            ".markdown": ContentType.TXT,
            ".pdf": ContentType.PDF,
            ".docx": ContentType.DOC,
            ".doc": ContentType.DOC,
            ".html": ContentType.HTML,
            ".htm": ContentType.HTML,
            ".json": ContentType.JSON,
            ".csv": ContentType.CSV,
        }

        if extension in extension_map:
            return extension_map[extension]

        # Try mime type detection as fallback
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type:
                mime_map = {
                    "text/plain": ContentType.TXT,
                    "text/markdown": ContentType.TXT,
                    "application/pdf": ContentType.PDF,
                    "application/msword": ContentType.DOC,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ContentType.DOC,
                    "text/html": ContentType.HTML,
                    "application/json": ContentType.JSON,
                    "text/csv": ContentType.CSV,
                }
                return mime_map.get(mime_type)
        except Exception as e:
            logger.debug(f"Mime type detection failed: {e}")

        return None

    @classmethod
    def get_supported_types(cls) -> List[ContentType]:
        """Get list of all supported content types"""
        return list(cls._loaders.keys())

    @classmethod
    def is_supported(cls, content_type: ContentType) -> bool:
        """Check if a content type is supported"""
        return content_type in cls._loaders

    @classmethod
    def get_loader_info(cls) -> dict:
        """Get information about all registered loaders"""
        info = {}
        for content_type, loader_class_or_instance in cls._loaders.items():
            if inspect.isclass(loader_class_or_instance):
                loader_name = loader_class_or_instance.__name__
            else:
                loader_name = loader_class_or_instance.__class__.__name__

            info[content_type.value] = {
                "loader_class": loader_name,
                "content_type": content_type.value,
            }
        return info


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


# Convenience functions for easier usage
async def load_document(file_path: str, content_type: ContentType = None, **kwargs):
    """
    Convenience function to load a document using the factory

    Args:
        file_path: Path to the file
        content_type: Content type, will be auto-detected if not provided
        **kwargs: Additional metadata

    Returns:
        Document: Loaded document
    """
    from ..models import FileLoadRequest

    # Auto-detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(file_path)

    # Create request
    request = FileLoadRequest(
        file_path=file_path, content_type=content_type, metadata=kwargs
    )

    # Get appropriate loader and load document
    loader = FileLoaderFactory.get_loader(content_type)
    return await loader.load_document(request)


def detect_content_type(file_path: str) -> ContentType:
    """
    Detect content type from file extension

    Args:
        file_path: Path to the file

    Returns:
        ContentType: Detected content type
    """
    from pathlib import Path

    from modules.schemas.enums import ContentType

    ext = Path(file_path).suffix.lower()

    content_type_mapping = {
        ".pdf": ContentType.PDF,
        ".txt": ContentType.TXT,
        ".md": ContentType.MD,
        ".json": ContentType.JSON,
        ".csv": ContentType.CSV,
        ".xml": ContentType.XML,
        ".html": ContentType.HTML,
        ".doc": ContentType.DOC,
        ".docx": ContentType.DOCX,
    }

    return content_type_mapping.get(ext, ContentType.TXT)


def get_supported_types() -> List[ContentType]:
    """
    Get all supported content types

    Returns:
        List[ContentType]: List of supported content types
    """
    return list(FileLoaderFactory._loaders.keys())


def is_supported(content_type: ContentType) -> bool:
    """
    Check if a content type is supported

    Args:
        content_type: Content type to check

    Returns:
        bool: True if supported, False otherwise
    """
    return content_type in FileLoaderFactory._loaders

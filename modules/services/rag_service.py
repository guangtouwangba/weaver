"""
RAGService implementation

整合所有RAG相关的Service implementation，包括：
- 嵌入Service implementation（OpenAI, HuggingFace, Local）
- 向量存储Service implementation（Weaviate, pgvector, ChromaDB）
- 文档处理管道Service implementation
"""

import asyncio
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

# Other dependencies
from modules.file_loader import IFileLoader
from modules.models import FileLoadRequest
# RAG interfaces
from modules.rag.embedding import (
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResult,
    IEmbeddingService,
)
from modules.rag.pipeline import (
    DocumentProcessingRequest,
    DocumentProcessingResult,
    IDocumentPipeline,
    PipelineConfig,
    PipelineStatus,
    ProcessingProgress,
    ProcessingStage,
    ProcessingStageResult,
)
from modules.rag.processors import IDocumentProcessor
from modules.rag.vector_store import (
    BulkOperationResult,
    IVectorStore,
    SearchFilter,
    SearchResult,
    VectorDocument,
    VectorStoreConfig,
    VectorStoreError,
    VectorStoreProvider,
)

logger = logging.getLogger(__name__)


# =================================
# Embedding Service Implementations
# =================================


class OpenAIEmbeddingService(IEmbeddingService):
    """OpenAI嵌入Service implementation"""

    def __init__(self, config: EmbeddingConfig):
        self._config = config
        self._client = None

    async def initialize(self) -> None:
        try:
            import openai

            self._client = openai.AsyncOpenAI(api_key=self._config.api_key)
            logger.info(f"OpenAI嵌入服务初始化完成: {self._config.model_name}")
        except ImportError:
            raise EmbeddingError(
                "OpenAI library not installed",
                provider="openai",
                error_code="LIBRARY_MISSING",
            )
        except Exception as e:
            raise EmbeddingError(
                f"OpenAI初始化失败: {e}",
                provider="openai",
                error_code="INIT_FAILED",
                original_error=e,
            )

    async def cleanup(self) -> None:
        self._client = None

    async def generate_embeddings(self, texts: List[str]) -> EmbeddingResult:
        start_time = time.time()

        try:
            response = await self._client.embeddings.create(
                model=self._config.model_name, input=texts
            )

            vectors = [embedding.embedding for embedding in response.data]
            processing_time = (time.time() - start_time) * 1000

            return EmbeddingResult(
                vectors=vectors,
                texts=texts,
                model_name=self._config.model_name,
                dimension=len(vectors[0]) if vectors else 0,
                processing_time_ms=processing_time,
                metadata={
                    "provider": "openai",
                    "usage": (
                        response.usage.dict() if hasattr(response, "usage") else None
                    ),
                },
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            raise EmbeddingError(
                f"OpenAI嵌入生成失败: {e}",
                provider="openai",
                error_code="GENERATION_FAILED",
                original_error=e,
            )

    async def generate_single_embedding(self, text: str) -> List[float]:
        result = await self.generate_embeddings([text])
        return result.vectors[0]

    async def get_embedding_dimension(self) -> int:
        return self._config.dimension

    async def health_check(self) -> Dict[str, Any]:
        try:
            await self.generate_single_embedding("test")
            return {
                "status": "healthy",
                "provider": "openai",
                "model": self._config.model_name,
            }
        except Exception as e:
            return {"status": "unhealthy", "provider": "openai", "error": str(e)}

    @property
    def service_name(self) -> str:
        return f"OpenAIEmbeddingService[{self._config.model_name}]"

    @property
    def config(self) -> EmbeddingConfig:
        return self._config

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "zh", "ja", "ko", "fr", "de", "es", "it", "pt", "ru"]


class HuggingFaceEmbeddingService(IEmbeddingService):
    """HuggingFace嵌入Service implementation"""

    def __init__(self, config: EmbeddingConfig):
        self._config = config
        self._model = None
        self._tokenizer = None

    async def initialize(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self._config.model_name)
            self._model = AutoModel.from_pretrained(self._config.model_name)

            if torch.cuda.is_available():
                self._model = self._model.cuda()

            logger.info(f"HuggingFace嵌入服务初始化完成: {self._config.model_name}")

        except ImportError:
            raise EmbeddingError(
                "Transformers library not installed",
                provider="huggingface",
                error_code="LIBRARY_MISSING",
            )
        except Exception as e:
            raise EmbeddingError(
                f"HuggingFace初始化失败: {e}",
                provider="huggingface",
                error_code="INIT_FAILED",
                original_error=e,
            )

    async def cleanup(self) -> None:
        self._model = None
        self._tokenizer = None

    async def generate_embeddings(self, texts: List[str]) -> EmbeddingResult:
        start_time = time.time()

        try:
            import torch

            # Tokenize
            inputs = self._tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            )

            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate embeddings
            with torch.no_grad():
                outputs = self._model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)  # Mean pooling

            vectors = embeddings.cpu().numpy().tolist()
            processing_time = (time.time() - start_time) * 1000

            return EmbeddingResult(
                vectors=vectors,
                texts=texts,
                model_name=self._config.model_name,
                dimension=len(vectors[0]) if vectors else 0,
                processing_time_ms=processing_time,
                metadata={
                    "provider": "huggingface",
                    "device": "cuda" if torch.cuda.is_available() else "cpu",
                },
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            raise EmbeddingError(
                f"HuggingFace嵌入生成失败: {e}",
                provider="huggingface",
                error_code="GENERATION_FAILED",
                original_error=e,
            )

    async def generate_single_embedding(self, text: str) -> List[float]:
        result = await self.generate_embeddings([text])
        return result.vectors[0]

    async def get_embedding_dimension(self) -> int:
        return self._config.dimension

    async def health_check(self) -> Dict[str, Any]:
        try:
            await self.generate_single_embedding("test")
            return {
                "status": "healthy",
                "provider": "huggingface",
                "model": self._config.model_name,
            }
        except Exception as e:
            return {"status": "unhealthy", "provider": "huggingface", "error": str(e)}

    @property
    def service_name(self) -> str:
        return f"HuggingFaceEmbeddingService[{self._config.model_name}]"

    @property
    def config(self) -> EmbeddingConfig:
        return self._config

    @property
    def supported_languages(self) -> List[str]:
        return ["en", "zh"]  # Depends on specific model


# =================================
# Vector Store Implementations
# =================================


class WeaviateVectorStore(IVectorStore):
    """Weaviate向量存储实现"""

    def __init__(self, config: VectorStoreConfig):
        self._config = config
        self._client = None
        self._client_version = None

    async def initialize(self) -> None:
        try:
            import weaviate

            # Try to determine Weaviate client version/compatibility
            try:
                # Try v4 client initialization first
                import weaviate.classes as wvc
                from weaviate.classes.init import Auth

                # Parse connection string to extract host and port
                connection_url = self._config.connection_string
                if connection_url.startswith("http://"):
                    connection_url = connection_url[7:]  # Remove http://
                elif connection_url.startswith("https://"):
                    connection_url = connection_url[8:]  # Remove https://

                # Use Weaviate v4 client initialization with init checks disabled for compatibility
                self._client = weaviate.connect_to_local(
                    host=(
                        connection_url.split(":")[0]
                        if ":" in connection_url
                        else connection_url
                    ),
                    port=(
                        int(connection_url.split(":")[1])
                        if ":" in connection_url
                        else 8080
                    ),
                    grpc_port=50051,
                    skip_init_checks=True,  # Skip gRPC health checks for compatibility
                )
                self._client_version = "v4"

                # Test connection
                if self._client.is_ready():
                    logger.info(
                        f"Weaviate v4向量存储初始化完成: {self._config.collection_name}"
                    )
                else:
                    raise Exception("Weaviate v4 client is not ready")

            except Exception as v4_error:
                # Log the compatibility issue
                if (
                    "version" in str(v4_error).lower()
                    and "not supported" in str(v4_error).lower()
                ):
                    logger.warning(
                        f"Weaviate server version incompatibility: {v4_error}"
                    )
                    logger.warning(
                        "Please upgrade Weaviate server to version 1.23.7 or higher for full compatibility"
                    )
                    raise VectorStoreError(
                        f"Weaviate server version incompatible with client. {v4_error}",
                        provider="weaviate",
                        error_code="VERSION_INCOMPATIBLE",
                        original_error=v4_error,
                    )
                else:
                    # Other initialization errors
                    raise Exception(
                        f"Weaviate v4 client initialization failed: {v4_error}"
                    )

        except ImportError:
            raise VectorStoreError(
                "Weaviate library not installed",
                provider="weaviate",
                error_code="LIBRARY_MISSING",
            )
        except Exception as e:
            raise VectorStoreError(
                f"Weaviate初始化失败: {e}",
                provider="weaviate",
                error_code="INIT_FAILED",
                original_error=e,
            )

    async def cleanup(self) -> None:
        if self._client:
            # v4 client has close(), v3 might not need explicit cleanup
            if hasattr(self._client, "close"):
                self._client.close()
        self._client = None
        self._client_version = None

    async def create_collection(self, config: VectorStoreConfig) -> bool:
        try:
            import weaviate.classes as wvc

            # Create collection using Weaviate v4 API
            collection = self._client.collections.create(
                name=config.collection_name,
                vectorizer_config=wvc.config.Configure.Vectorizer.none(),  # We provide our own vectors
                properties=[
                    wvc.config.Property(
                        name="content", data_type=wvc.config.DataType.TEXT
                    ),
                    wvc.config.Property(
                        name="document_id", data_type=wvc.config.DataType.TEXT
                    ),
                    wvc.config.Property(
                        name="chunk_index", data_type=wvc.config.DataType.INT
                    ),
                    wvc.config.Property(
                        name="metadata", data_type=wvc.config.DataType.OBJECT
                    ),
                ],
            )
            return True

        except Exception as e:
            logger.error(f"Weaviate collection creation failed: {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        try:
            self._client.collections.delete(collection_name)
            return True
        except Exception as e:
            logger.error(f"Weaviate collection deletion failed: {e}")
            return False

    async def upsert_vectors(
        self, documents: List[VectorDocument]
    ) -> BulkOperationResult:
        start_time = time.time()
        success_count = 0
        errors = []

        try:
            import weaviate.classes as wvc

            # Get the collection
            collection = self._client.collections.get(self._config.collection_name)

            # Prepare data objects for batch insertion
            data_objects = []
            for doc in documents:
                try:
                    data_obj = wvc.data.DataObject(
                        properties={
                            "content": doc.content,
                            "document_id": doc.document_id,
                            "chunk_index": doc.chunk_index,
                            "metadata": doc.metadata,
                        },
                        uuid=doc.id,
                        vector=doc.vector,
                    )
                    data_objects.append(data_obj)
                    success_count += 1
                except Exception as e:
                    errors.append(f"Document {doc.id}: {str(e)}")

            # Batch insert
            if data_objects:
                collection.data.insert_many(data_objects)

            processing_time = (time.time() - start_time) * 1000

            return BulkOperationResult(
                success_count=success_count,
                failed_count=len(errors),
                total_count=len(documents),
                processing_time_ms=processing_time,
                errors=errors,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            raise VectorStoreError(
                f"Weaviate批量插入失败: {e}",
                provider="weaviate",
                error_code="BULK_UPSERT_FAILED",
                original_error=e,
            )

    async def upsert_single_vector(self, document: VectorDocument) -> bool:
        result = await self.upsert_vectors([document])
        return result.success_count > 0

    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[SearchFilter] = None,
    ) -> List[SearchResult]:
        try:
            query = self._client.query.get(
                self._config.collection_name,
                ["content", "document_id", "chunk_index", "metadata"],
            )

            # Apply vector search
            query = query.with_near_vector({"vector": query_vector}).with_limit(limit)

            # Apply filters if provided
            if filters and filters.metadata_filters:
                # TODO: Implement metadata filtering
                pass

            result = query.with_additional(["certainty"]).do()

            search_results = []
            for i, item in enumerate(
                result.get("data", {})
                .get("Get", {})
                .get(self._config.collection_name, [])
            ):
                doc = VectorDocument(
                    id=item.get("_additional", {}).get("id", ""),
                    vector=[],  # Vector not returned in search
                    content=item.get("content", ""),
                    metadata=item.get("metadata", {}),
                    document_id=item.get("document_id"),
                    chunk_index=item.get("chunk_index"),
                )

                score = item.get("_additional", {}).get("certainty", 0.0)

                if score_threshold is None or score >= score_threshold:
                    search_results.append(
                        SearchResult(document=doc, score=score, rank=i + 1)
                    )

            return search_results

        except Exception as e:
            raise VectorStoreError(
                f"Weaviate搜索失败: {e}",
                provider="weaviate",
                error_code="SEARCH_FAILED",
                original_error=e,
            )

    async def get_vector_by_id(self, vector_id: str) -> Optional[VectorDocument]:
        try:
            result = self._client.data_object.get_by_id(
                vector_id, self._config.collection_name
            )

            if result:
                return VectorDocument(
                    id=vector_id,
                    vector=[],  # Vector not returned
                    content=result.get("properties", {}).get("content", ""),
                    metadata=result.get("properties", {}).get("metadata", {}),
                    document_id=result.get("properties", {}).get("document_id"),
                    chunk_index=result.get("properties", {}).get("chunk_index"),
                )

            return None

        except Exception as e:
            logger.error(f"Weaviate get vector by ID failed: {e}")
            return None

    async def delete_vectors(self, vector_ids: List[str]) -> BulkOperationResult:
        start_time = time.time()
        success_count = 0
        errors = []

        for vector_id in vector_ids:
            try:
                self._client.data_object.delete(vector_id, self._config.collection_name)
                success_count += 1
            except Exception as e:
                errors.append(f"Vector {vector_id}: {str(e)}")

        processing_time = (time.time() - start_time) * 1000

        return BulkOperationResult(
            success_count=success_count,
            failed_count=len(errors),
            total_count=len(vector_ids),
            processing_time_ms=processing_time,
            errors=errors,
        )

    async def delete_vectors_by_document_id(
        self, document_id: str
    ) -> BulkOperationResult:
        # TODO: Implement document ID-based deletion
        return BulkOperationResult(0, 0, 0, 0)

    async def update_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        try:
            self._client.data_object.update(
                uuid=vector_id,
                class_name=self._config.collection_name,
                data_object={"metadata": metadata},
            )
            return True
        except Exception as e:
            logger.error(f"Weaviate metadata update failed: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            # TODO: Implement collection statistics
            return {"total_vectors": 0, "collection_name": self._config.collection_name}
        except Exception as e:
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        try:
            if self._client_version == "v4":
                # v4 client health check
                if self._client.is_ready():
                    return {
                        "status": "healthy",
                        "provider": "weaviate",
                        "version": "v4",
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "weaviate",
                        "error": "v4 Client not ready",
                    }
            else:
                # v3 client health check
                try:
                    self._client.schema.get()
                    return {
                        "status": "healthy",
                        "provider": "weaviate",
                        "version": "v3",
                    }
                except Exception as v3_error:
                    return {
                        "status": "unhealthy",
                        "provider": "weaviate",
                        "error": f"v3 health check failed: {v3_error}",
                    }
        except Exception as e:
            return {"status": "unhealthy", "provider": "weaviate", "error": str(e)}

    @property
    def service_name(self) -> str:
        return f"WeaviateVectorStore[{self._config.collection_name}]"

    @property
    def config(self) -> VectorStoreConfig:
        return self._config


# =================================
# Document Pipeline Implementation
# =================================


class DocumentPipelineService(IDocumentPipeline):
    """文档处理管道Service implementation"""

    def __init__(
        self,
        config: PipelineConfig,
        file_loader: IFileLoader,
        document_processor: IDocumentProcessor,
        embedding_service: IEmbeddingService,
        vector_store: IVectorStore,
    ):
        self._config = config
        self._file_loader = file_loader
        self._document_processor = document_processor
        self._embedding_service = embedding_service
        self._vector_store = vector_store

        # Progress tracking
        self._active_processes: Dict[str, ProcessingProgress] = {}
        self._processing_semaphore = asyncio.Semaphore(config.max_concurrent_chunks)

    async def initialize(self) -> None:
        await self._embedding_service.initialize()
        await self._vector_store.initialize()
        logger.info("文档处理管道初始化完成")

    async def cleanup(self) -> None:
        await self._embedding_service.cleanup()
        await self._vector_store.cleanup()

    async def process_document(
        self, request: DocumentProcessingRequest
    ) -> DocumentProcessingResult:
        request_id = str(uuid4())
        start_time = time.time()
        stage_results = []

        try:
            # Update progress
            await self._update_progress(
                request_id, ProcessingStage.FILE_LOADING, 0, PipelineStatus.RUNNING
            )

            # Stage 1: File Loading
            stage_start = time.time()
            file_load_request = FileLoadRequest(
                file_path=request.file_path,
                content_type=request.content_type,
            )
            document = await self._file_loader.load_document(h)
            stage_time = (time.time() - stage_start) * 1000

            stage_results.append(
                ProcessingStageResult(
                    stage=ProcessingStage.FILE_LOADING,
                    status=PipelineStatus.COMPLETED,
                    processing_time_ms=stage_time,
                    items_processed=1,
                )
            )

            # Update progress
            await self._update_progress(
                request_id, ProcessingStage.TEXT_CHUNKING, 25, PipelineStatus.RUNNING
            )

            # Stage 2: Document Processing (Chunking)
            stage_start = time.time()
            processing_result = await self._document_processor.process_document(
                document
            )
            chunks = processing_result.chunks
            stage_time = (time.time() - stage_start) * 1000

            stage_results.append(
                ProcessingStageResult(
                    stage=ProcessingStage.TEXT_CHUNKING,
                    status=PipelineStatus.COMPLETED,
                    processing_time_ms=stage_time,
                    items_processed=len(chunks),
                )
            )

            embedded_chunks = 0
            stored_vectors = 0

            if self._config.enable_embeddings and chunks:
                # Update progress
                await self._update_progress(
                    request_id,
                    ProcessingStage.EMBEDDING_GENERATION,
                    50,
                    PipelineStatus.RUNNING,
                )

                # Stage 3: Embedding Generation
                stage_start = time.time()
                chunk_texts = [chunk.content for chunk in chunks]
                embedding_result = await self._embedding_service.generate_embeddings(
                    chunk_texts
                )
                embedded_chunks = len(embedding_result.vectors)
                stage_time = (time.time() - stage_start) * 1000

                stage_results.append(
                    ProcessingStageResult(
                        stage=ProcessingStage.EMBEDDING_GENERATION,
                        status=PipelineStatus.COMPLETED,
                        processing_time_ms=stage_time,
                        items_processed=embedded_chunks,
                    )
                )

                if self._config.enable_vector_storage:
                    # Update progress
                    await self._update_progress(
                        request_id,
                        ProcessingStage.VECTOR_STORAGE,
                        75,
                        PipelineStatus.RUNNING,
                    )

                    # Stage 4: Vector Storage
                    stage_start = time.time()
                    vector_docs = []

                    for i, (chunk, vector) in enumerate(
                        zip(chunks, embedding_result.vectors)
                    ):
                        vector_doc = VectorDocument(
                            id=f"{document.id}_chunk_{i}",
                            vector=vector,
                            content=chunk.content,
                            metadata={
                                **chunk.metadata,
                                "document_title": document.title,
                                "file_path": request.file_path,
                                "topic_id": request.topic_id,
                            },
                            document_id=document.id,
                            chunk_index=i,
                        )
                        vector_docs.append(vector_doc)

                    storage_result = await self._vector_store.upsert_vectors(
                        vector_docs
                    )
                    stored_vectors = storage_result.success_count
                    stage_time = (time.time() - stage_start) * 1000

                    stage_results.append(
                        ProcessingStageResult(
                            stage=ProcessingStage.VECTOR_STORAGE,
                            status=PipelineStatus.COMPLETED,
                            processing_time_ms=stage_time,
                            items_processed=stored_vectors,
                        )
                    )

            # Update progress to completed
            await self._update_progress(
                request_id,
                ProcessingStage.VECTOR_STORAGE,
                100,
                PipelineStatus.COMPLETED,
            )

            total_time = (time.time() - start_time) * 1000

            return DocumentProcessingResult(
                request_id=request_id,
                file_id=request.file_id,
                status=PipelineStatus.COMPLETED,
                document_id=document.id,
                total_chunks=len(chunks),
                embedded_chunks=embedded_chunks,
                stored_vectors=stored_vectors,
                total_processing_time_ms=total_time,
                stage_results=stage_results,
                metadata={
                    "pipeline": self.pipeline_name,
                    "config": self._config.__dict__,
                    "document_metadata": document.metadata,
                },
            )

        except Exception as e:
            total_time = (time.time() - start_time) * 1000

            return DocumentProcessingResult(
                request_id=request_id,
                file_id=request.file_id,
                status=PipelineStatus.FAILED,
                total_processing_time_ms=total_time,
                stage_results=stage_results,
                error_message=str(e),
                metadata={"pipeline": self.pipeline_name},
            )
        finally:
            # Clean up progress tracking
            self._active_processes.pop(request_id, None)

    async def process_documents_batch(
        self, requests: List[DocumentProcessingRequest]
    ) -> AsyncIterator[DocumentProcessingResult]:
        for request in requests:
            result = await self.process_document(request)
            yield result

    async def get_processing_status(
        self, request_id: str
    ) -> Optional[ProcessingProgress]:
        return self._active_processes.get(request_id)

    async def cancel_processing(self, request_id: str) -> bool:
        if request_id in self._active_processes:
            progress = self._active_processes[request_id]
            progress.current_status = PipelineStatus.CANCELLED
            return True
        return False

    async def retry_failed_processing(
        self, request_id: str
    ) -> DocumentProcessingResult:
        raise NotImplementedError("Retry functionality not implemented yet")

    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        return {
            "active_processes": len(self._active_processes),
            "pipeline_name": self.pipeline_name,
            "config": self._config.__dict__,
        }

    async def health_check(self) -> Dict[str, Any]:
        components = {
            "file_loader": (
                await self._file_loader.health_check()
                if hasattr(self._file_loader, "health_check")
                else {"status": "unknown"}
            ),
            "document_processor": (
                await self._document_processor.health_check()
                if hasattr(self._document_processor, "health_check")
                else {"status": "unknown"}
            ),
            "embedding_service": await self._embedding_service.health_check(),
            "vector_store": await self._vector_store.health_check(),
        }

        overall_healthy = all(
            comp.get("status") == "healthy" for comp in components.values()
        )

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "pipeline": self.pipeline_name,
            "components": components,
        }

    async def _update_progress(
        self,
        request_id: str,
        stage: ProcessingStage,
        percentage: float,
        status: PipelineStatus,
    ):
        """Update processing progress"""
        progress = ProcessingProgress(
            request_id=request_id,
            current_stage=stage,
            progress_percentage=percentage,
            current_status=status,
        )
        self._active_processes[request_id] = progress

    @property
    def pipeline_name(self) -> str:
        return "DocumentPipelineService"

    @property
    def config(self) -> PipelineConfig:
        return self._config

    @property
    def supported_file_types(self) -> List[str]:
        return [".pdf", ".txt", ".md", ".docx", ".html"]


# =================================
# Service Factory Functions
# =================================


def create_embedding_service(
    provider: EmbeddingProvider, ai_config=None, **kwargs
) -> IEmbeddingService:
    """Create embedding service instance with AI configuration support"""

    if provider == EmbeddingProvider.OPENAI:
        # Use AI config if provided, otherwise use defaults or kwargs
        if ai_config:
            openai_config = ai_config.embedding.openai
            model_name = kwargs.pop("model_name", openai_config.embedding_model)
            api_key = kwargs.pop("api_key", openai_config.api_key)
            dimension = kwargs.pop("dimension", 1536)
        else:
            # Fallback to defaults if no AI config
            model_name = kwargs.pop("model_name", "text-embedding-ada-002")
            dimension = kwargs.pop("dimension", 1536)
            api_key = kwargs.pop("api_key", None)

        config = EmbeddingConfig(
            provider=provider,
            model_name=model_name,
            dimension=dimension,
            api_key=api_key,
            **kwargs,
        )
        return OpenAIEmbeddingService(config)

    elif provider == EmbeddingProvider.HUGGINGFACE:
        # Use AI config if provided, otherwise use defaults or kwargs
        if ai_config:
            hf_config = ai_config.embedding.huggingface
            model_name = kwargs.pop("model_name", hf_config.embedding_model)
            dimension = kwargs.pop("dimension", 384)
        else:
            # Fallback to defaults if no AI config
            model_name = kwargs.pop(
                "model_name", "sentence-transformers/all-MiniLM-L6-v2"
            )
            dimension = kwargs.pop("dimension", 384)

        config = EmbeddingConfig(
            provider=provider, model_name=model_name, dimension=dimension, **kwargs
        )
        return HuggingFaceEmbeddingService(config)

    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def create_vector_store(provider: VectorStoreProvider, **kwargs) -> IVectorStore:
    """创建向量存储实例"""

    if provider == VectorStoreProvider.WEAVIATE:
        # Extract known parameters to avoid duplicate keyword arguments
        connection_string = kwargs.pop("connection_string", "http://localhost:8080")
        collection_name = kwargs.pop("collection_name", "documents")
        dimension = kwargs.pop("dimension", 1536)
        enable_auto_vectorization = kwargs.pop("enable_auto_vectorization", False)
        description = kwargs.pop("description", f"RAG文档集合: {collection_name}")

        config = VectorStoreConfig(
            provider=provider,
            connection_string=connection_string,
            collection_name=collection_name,
            dimension=dimension,
            enable_auto_vectorization=enable_auto_vectorization,
            description=description,
            **kwargs,
        )
        return WeaviateVectorStore(config)

    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")


def create_document_pipeline(
    file_loader: IFileLoader,
    document_processor: IDocumentProcessor,
    embedding_service: IEmbeddingService,
    vector_store: IVectorStore,
    **kwargs,
) -> IDocumentPipeline:
    """创建文档处理管道实例"""

    config = PipelineConfig(**kwargs)
    return DocumentPipelineService(
        config=config,
        file_loader=file_loader,
        document_processor=document_processor,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

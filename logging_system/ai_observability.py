"""
AI-Native Observability Integration

Integrates Pydantic Logfire for AI workload monitoring, LLM call tracing,
and enhanced observability for RAG operations.
"""

import os
from typing import Any, Dict, Optional
from contextlib import contextmanager

try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from logging_system.config import LoggingConfig


class LogfireIntegration:
    """Pydantic Logfire integration for AI-native observability"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.enabled = LOGFIRE_AVAILABLE and os.getenv('LOGFIRE_TOKEN') is not None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize Logfire integration"""
        if not self.enabled:
            return False
            
        try:
            # Configure Logfire
            logfire.configure(
                service_name=self.config.app_name,
                service_version=self.config.version,
                environment=self.config.environment,
                # Send traces to local OTEL collector or directly to Logfire
                send_to_logfire=True,
            )
            
            self._initialized = True
            return True
            
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to initialize Logfire: {e}\n")
            self.enabled = False
            return False
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application with Logfire"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            logfire.instrument_fastapi(app)
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to instrument FastAPI with Logfire: {e}\n")
    
    def instrument_requests(self):
        """Instrument HTTP requests"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            logfire.instrument_requests()
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to instrument requests with Logfire: {e}\n")
    
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy for database monitoring"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            logfire.instrument_sqlalchemy(engine=engine)
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to instrument SQLAlchemy with Logfire: {e}\n")
    
    def instrument_redis(self):
        """Instrument Redis for cache monitoring"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            logfire.instrument_redis()
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to instrument Redis with Logfire: {e}\n")
    
    @contextmanager
    def span(self, name: str, **kwargs):
        """Create a custom span for monitoring operations"""
        if not self.enabled or not self._initialized:
            yield None
            return
            
        try:
            with logfire.span(name, **kwargs) as span:
                yield span
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to create Logfire span: {e}\n")
            yield None
    
    def log_llm_call(
        self, 
        model: str, 
        prompt: str, 
        response: str, 
        tokens_used: Optional[int] = None,
        duration_ms: Optional[float] = None,
        **metadata
    ):
        """Log LLM API call with structured data"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            with logfire.span('llm_call') as span:
                span.set_attribute('model', model)
                span.set_attribute('prompt_length', len(prompt))
                span.set_attribute('response_length', len(response))
                
                if tokens_used:
                    span.set_attribute('tokens_used', tokens_used)
                if duration_ms:
                    span.set_attribute('duration_ms', duration_ms)
                    
                # Add custom metadata
                for key, value in metadata.items():
                    span.set_attribute(f'metadata.{key}', value)
                    
                # Log the actual content (be careful with sensitive data)
                logfire.info(
                    'LLM Call',
                    model=model,
                    prompt_preview=prompt[:200] + '...' if len(prompt) > 200 else prompt,
                    response_preview=response[:200] + '...' if len(response) > 200 else response,
                    tokens_used=tokens_used,
                    duration_ms=duration_ms,
                    **metadata
                )
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to log LLM call with Logfire: {e}\n")
    
    def log_rag_operation(
        self,
        operation: str,
        query: str,
        num_results: int,
        duration_ms: Optional[float] = None,
        vector_store: Optional[str] = None,
        **metadata
    ):
        """Log RAG operations (search, embedding, etc.)"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            with logfire.span(f'rag_{operation}') as span:
                span.set_attribute('operation', operation)
                span.set_attribute('query_length', len(query))
                span.set_attribute('num_results', num_results)
                
                if duration_ms:
                    span.set_attribute('duration_ms', duration_ms)
                if vector_store:
                    span.set_attribute('vector_store', vector_store)
                    
                # Add custom metadata
                for key, value in metadata.items():
                    span.set_attribute(f'metadata.{key}', value)
                    
                logfire.info(
                    f'RAG {operation}',
                    operation=operation,
                    query=query[:100] + '...' if len(query) > 100 else query,
                    num_results=num_results,
                    duration_ms=duration_ms,
                    vector_store=vector_store,
                    **metadata
                )
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to log RAG operation with Logfire: {e}\n")
    
    def log_document_processing(
        self,
        file_name: str,
        file_size: int,
        processing_stage: str,
        duration_ms: Optional[float] = None,
        chunks_created: Optional[int] = None,
        **metadata
    ):
        """Log document processing operations"""
        if not self.enabled or not self._initialized:
            return
            
        try:
            with logfire.span('document_processing') as span:
                span.set_attribute('file_name', file_name)
                span.set_attribute('file_size', file_size)
                span.set_attribute('processing_stage', processing_stage)
                
                if duration_ms:
                    span.set_attribute('duration_ms', duration_ms)
                if chunks_created:
                    span.set_attribute('chunks_created', chunks_created)
                    
                # Add custom metadata
                for key, value in metadata.items():
                    span.set_attribute(f'metadata.{key}', value)
                    
                logfire.info(
                    'Document Processing',
                    file_name=file_name,
                    file_size=file_size,
                    processing_stage=processing_stage,
                    duration_ms=duration_ms,
                    chunks_created=chunks_created,
                    **metadata
                )
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to log document processing with Logfire: {e}\n")


# Global instance
_logfire_integration: Optional[LogfireIntegration] = None


def get_logfire_integration() -> Optional[LogfireIntegration]:
    """Get the global Logfire integration instance"""
    return _logfire_integration


def setup_logfire_integration(config: LoggingConfig) -> bool:
    """Setup global Logfire integration"""
    global _logfire_integration
    
    _logfire_integration = LogfireIntegration(config)
    return _logfire_integration.initialize()


# Convenience functions
def log_llm_call(model: str, prompt: str, response: str, **kwargs):
    """Convenience function to log LLM calls"""
    if _logfire_integration:
        _logfire_integration.log_llm_call(model, prompt, response, **kwargs)


def log_rag_operation(operation: str, query: str, num_results: int, **kwargs):
    """Convenience function to log RAG operations"""
    if _logfire_integration:
        _logfire_integration.log_rag_operation(operation, query, num_results, **kwargs)


def log_document_processing(file_name: str, file_size: int, processing_stage: str, **kwargs):
    """Convenience function to log document processing"""
    if _logfire_integration:
        _logfire_integration.log_document_processing(file_name, file_size, processing_stage, **kwargs)


@contextmanager
def trace_span(name: str, **kwargs):
    """Convenience function to create tracing spans"""
    if _logfire_integration:
        with _logfire_integration.span(name, **kwargs) as span:
            yield span
    else:
        yield None
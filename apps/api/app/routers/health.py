"""Health check endpoints for monitoring and readiness probes."""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Detailed Health Check")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Comprehensive health check for all system components.
    
    Returns detailed status of:
    - Application initialization
    - LLM and Embeddings
    - Vector Store
    - Redis Cache
    - Reranker
    - Database
    - LangSmith
    - Prometheus
    
    Returns:
        Dictionary with overall status and component details.
    """
    try:
        # Get application state
        rag_state = request.app.state.rag
        
        health_status = {
            "status": "healthy",
            "version": "0.3.0",
            "environment": rag_state.settings.app_env if rag_state.settings else "unknown",
            "components": {}
        }
        
        # Check if system is initialized
        if not rag_state.is_initialized:
            health_status["status"] = "degraded"
            health_status["components"]["system"] = {
                "status": "not_initialized",
                "message": "System initialization incomplete"
            }
            return health_status
        
        # Check LLM
        health_status["components"]["llm"] = {
            "status": "up" if rag_state.llm else "down",
            "provider": rag_state.settings.llm.provider if rag_state.settings else None,
            "model": rag_state.settings.llm.model if rag_state.settings else None,
        }
        if not rag_state.llm:
            health_status["status"] = "degraded"
        
        # Check Embeddings
        health_status["components"]["embeddings"] = {
            "status": "up" if rag_state.embeddings else "down",
            "provider": rag_state.settings.embedding.provider if rag_state.settings else None,
            "model": rag_state.settings.embedding.model if rag_state.settings else None,
        }
        if not rag_state.embeddings:
            health_status["status"] = "degraded"
        
        # Check Vector Store
        health_status["components"]["vector_store"] = {
            "status": "up" if rag_state.vector_store else "empty",
            "path": rag_state.settings.vector_store_path if rag_state.settings else None,
        }
        if not rag_state.vector_store:
            health_status["components"]["vector_store"]["message"] = "No documents indexed yet"
        
        # Check Redis (if enabled)
        if rag_state.settings and rag_state.settings.cache.enabled:
            if rag_state.redis_client:
                try:
                    await rag_state.redis_client.ping()
                    health_status["components"]["redis"] = {
                        "status": "up",
                        "url": rag_state.settings.cache.redis_url,
                    }
                except Exception as e:
                    health_status["components"]["redis"] = {
                        "status": "down",
                        "error": str(e)
                    }
                    health_status["status"] = "degraded"
            else:
                health_status["components"]["redis"] = {
                    "status": "down",
                    "message": "Redis client not initialized"
                }
                health_status["status"] = "degraded"
        else:
            health_status["components"]["redis"] = {
                "status": "disabled"
            }
        
        # Check Reranker (if enabled)
        if rag_state.settings and rag_state.settings.reranker.enabled:
            health_status["components"]["reranker"] = {
                "status": "up" if rag_state.reranker else "down",
                "type": rag_state.settings.reranker.type,
                "model": rag_state.settings.reranker.model,
            }
            if not rag_state.reranker:
                health_status["components"]["reranker"]["message"] = "Reranker not implemented yet"
        else:
            health_status["components"]["reranker"] = {
                "status": "disabled"
            }
        
        # Check Database
        try:
            from rag_core.storage.database import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            health_status["components"]["database"] = {
                "status": "up",
                "type": "PostgreSQL"
            }
            db.close()
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "down",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Check LangSmith
        if rag_state.settings and rag_state.settings.observability.langsmith_enabled:
            health_status["components"]["langsmith"] = {
                "status": "enabled",
                "project": rag_state.settings.observability.langsmith_project
            }
        else:
            health_status["components"]["langsmith"] = {
                "status": "disabled"
            }
        
        # Check Prometheus
        if rag_state.prometheus_registry:
            health_status["components"]["prometheus"] = {
                "status": "enabled",
                "port": rag_state.settings.observability.prometheus_port if rag_state.settings else None
            }
        else:
            health_status["components"]["prometheus"] = {
                "status": "disabled"
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/ready", summary="Readiness Probe")
async def readiness_check(request: Request) -> Dict[str, str]:
    """
    Kubernetes readiness probe.
    
    Checks if the application is ready to serve traffic.
    Returns 200 if ready, 503 if not.
    
    Required components for readiness:
    - System initialized
    - LLM loaded
    - Embeddings loaded
    - Database accessible
    
    Returns:
        Simple status message.
    
    Raises:
        HTTPException: 503 if not ready.
    """
    try:
        rag_state = request.app.state.rag
        
        # Check critical components
        if not rag_state.is_initialized:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        if not rag_state.llm:
            raise HTTPException(status_code=503, detail="LLM not loaded")
        
        if not rag_state.embeddings:
            raise HTTPException(status_code=503, detail="Embeddings not loaded")
        
        # Check database
        try:
            from rag_core.storage.database import get_db
            db = next(get_db())
            db.execute("SELECT 1")
            db.close()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database not accessible: {e}")
        
        return {"status": "ready"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/live", summary="Liveness Probe")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    
    Simple check to verify the application is alive.
    Always returns 200 if the application is running.
    
    Returns:
        Simple status message.
    """
    return {"status": "alive"}


@router.get("/startup", summary="Startup Check")
async def startup_check(request: Request) -> Dict[str, Any]:
    """
    Kubernetes startup probe.
    
    Checks if the application has completed initialization.
    Used to determine when the container is ready for readiness checks.
    
    Returns:
        Initialization status and progress.
    
    Raises:
        HTTPException: 503 if still starting up.
    """
    try:
        rag_state = request.app.state.rag
        
        if not rag_state.is_initialized:
            # Return detailed initialization status
            status = rag_state.get_status()
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "starting",
                    "initialized": False,
                    "components": status.get("components", {})
                }
            )
        
        return {
            "status": "started",
            "initialized": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/status", summary="System Status")
async def system_status(request: Request) -> Dict[str, Any]:
    """
    Get detailed system status.
    
    Similar to /health but with more technical details.
    Useful for debugging and monitoring dashboards.
    
    Returns:
        Detailed system status including all components.
    """
    try:
        rag_state = request.app.state.rag
        status = rag_state.get_status()
        
        # Add configuration details
        if rag_state.settings:
            status["configuration"] = {
                "app_env": rag_state.settings.app_env,
                "llm_provider": rag_state.settings.llm.provider,
                "llm_model": rag_state.settings.llm.model,
                "embedding_provider": rag_state.settings.embedding.provider,
                "embedding_model": rag_state.settings.embedding.model,
                "cache_enabled": rag_state.settings.cache.enabled,
                "reranker_enabled": rag_state.settings.reranker.enabled,
                "langsmith_enabled": rag_state.settings.observability.langsmith_enabled,
                "prometheus_enabled": rag_state.settings.observability.prometheus_enabled,
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "initialized": False
        }


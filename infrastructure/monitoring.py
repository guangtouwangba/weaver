"""
Infrastructure monitoring and health checking.

Provides comprehensive monitoring for all infrastructure components
including health checks, metrics collection, and alerting.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import json

from .config import InfrastructureConfig
from .database.config import check_database_connection
from .messaging.redis_broker import RedisMessageBroker
from .storage.minio_storage import MinIOStorage

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'response_time_ms': self.response_time_ms,
            'details': self.details
        }


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    components: List[HealthCheckResult] = field(default_factory=list)
    
    @property
    def healthy_components(self) -> int:
        """Count of healthy components."""
        return sum(1 for c in self.components if c.status == HealthStatus.HEALTHY)
    
    @property
    def total_components(self) -> int:
        """Total number of components."""
        return len(self.components)
    
    @property
    def health_percentage(self) -> float:
        """Percentage of healthy components."""
        if self.total_components == 0:
            return 0.0
        return (self.healthy_components / self.total_components) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'healthy_components': self.healthy_components,
            'total_components': self.total_components,
            'health_percentage': self.health_percentage,
            'components': [c.to_dict() for c in self.components]
        }


class HealthChecker:
    """
    Health checker for infrastructure components.
    
    Performs health checks on all infrastructure components and
    provides aggregated health status.
    """
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self._health_checks: Dict[str, Callable] = {}
        self._last_check: Optional[SystemHealth] = None
        self._check_interval = config.monitoring.health_check_interval
        self._check_timeout = config.monitoring.health_check_timeout
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """Register default health checks for infrastructure components."""
        self._health_checks.update({
            'database': self._check_database_health,
            'messaging': self._check_messaging_health,
            'storage': self._check_storage_health,
            'cache': self._check_cache_health
        })
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """Register a custom health check."""
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def _time_check(self, check_func: Callable, component: str) -> HealthCheckResult:
        """Execute a health check with timing."""
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                check_func(),
                timeout=self._check_timeout.total_seconds()
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.response_time_ms = response_time
                return result
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                return HealthCheckResult(
                    component=component,
                    status=status,
                    message="OK" if result else "Check failed",
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    message=str(result),
                    response_time_ms=response_time
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Timeout after {self._check_timeout.total_seconds()}s",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_database_health(self) -> HealthCheckResult:
        """Check database health."""
        try:
            is_healthy = check_database_connection()
            
            if is_healthy:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    details={
                        'host': self.config.database.host,
                        'port': self.config.database.port,
                        'database': self.config.database.database
                    }
                )
            else:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed"
                )
                
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check error: {str(e)}"
            )
    
    async def _check_messaging_health(self) -> HealthCheckResult:
        """Check messaging system health."""
        try:
            broker = RedisMessageBroker(
                redis_url=self.config.messaging.redis.url,
                database=self.config.messaging.redis.database
            )
            
            is_healthy = await broker.health_check()
            
            if is_healthy:
                return HealthCheckResult(
                    component="messaging",
                    status=HealthStatus.HEALTHY,
                    message="Redis messaging broker healthy",
                    details={
                        'host': self.config.messaging.redis.host,
                        'port': self.config.messaging.redis.port,
                        'database': self.config.messaging.redis.database
                    }
                )
            else:
                return HealthCheckResult(
                    component="messaging",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis messaging broker unhealthy"
                )
                
        except Exception as e:
            return HealthCheckResult(
                component="messaging",
                status=HealthStatus.UNHEALTHY,
                message=f"Messaging check error: {str(e)}"
            )
    
    async def _check_storage_health(self) -> HealthCheckResult:
        """Check storage system health."""
        try:
            storage = MinIOStorage(**self.config.storage.minio_config)
            is_healthy = await storage.health_check()
            
            if is_healthy:
                # Get additional storage info
                buckets = await storage.list_buckets()
                return HealthCheckResult(
                    component="storage",
                    status=HealthStatus.HEALTHY,
                    message="MinIO storage healthy",
                    details={
                        'endpoint': self.config.storage.endpoint,
                        'buckets_count': len(buckets),
                        'buckets': buckets[:5]  # First 5 buckets
                    }
                )
            else:
                return HealthCheckResult(
                    component="storage",
                    status=HealthStatus.UNHEALTHY,
                    message="MinIO storage unhealthy"
                )
                
        except Exception as e:
            return HealthCheckResult(
                component="storage",
                status=HealthStatus.UNHEALTHY,
                message=f"Storage check error: {str(e)}"
            )
    
    async def _check_cache_health(self) -> HealthCheckResult:
        """Check cache system health."""
        try:
            # For now, reuse Redis check since cache uses Redis
            import redis.asyncio as redis
            
            r = redis.from_url(self.config.cache.redis.url)
            await r.ping()
            await r.close()
            
            return HealthCheckResult(
                component="cache",
                status=HealthStatus.HEALTHY,
                message="Redis cache healthy",
                details={
                    'host': self.config.cache.redis.host,
                    'port': self.config.cache.redis.port,
                    'database': self.config.cache.redis.database
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="cache",
                status=HealthStatus.UNHEALTHY,
                message=f"Cache check error: {str(e)}"
            )
    
    async def check_all(self) -> SystemHealth:
        """Perform health checks on all registered components."""
        logger.debug("Starting health checks for all components")
        
        # Run all health checks concurrently
        check_tasks = [
            self._time_check(check_func, component)
            for component, check_func in self._health_checks.items()
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component = list(self._health_checks.keys())[i]
                health_results.append(HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(result)}"
                ))
            else:
                health_results.append(result)
        
        # Determine overall system health
        unhealthy_count = sum(1 for r in health_results if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in health_results if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count == 0 and degraded_count == 0:
            overall_status = HealthStatus.HEALTHY
        elif unhealthy_count == 0:
            overall_status = HealthStatus.DEGRADED
        elif unhealthy_count < len(health_results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        system_health = SystemHealth(
            status=overall_status,
            components=health_results
        )
        
        self._last_check = system_health
        
        logger.info(
            f"Health check completed: {system_health.healthy_components}/"
            f"{system_health.total_components} components healthy"
        )
        
        return system_health
    
    async def get_last_health_check(self) -> Optional[SystemHealth]:
        """Get the result of the last health check."""
        return self._last_check
    
    async def start_background_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._running:
            logger.warning("Health monitoring already running")
            return
        
        self._running = True
        self._background_task = asyncio.create_task(self._background_monitor())
        logger.info(f"Started background health monitoring (interval: {self._check_interval})")
    
    async def stop_background_monitoring(self) -> None:
        """Stop background health monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped background health monitoring")
    
    async def _background_monitor(self) -> None:
        """Background monitoring task."""
        while self._running:
            try:
                health = await self.check_all()
                
                # Log unhealthy components
                for component in health.components:
                    if component.status != HealthStatus.HEALTHY:
                        logger.warning(
                            f"Component {component.component} is {component.status.value}: "
                            f"{component.message}"
                        )
                
                # Wait for next check
                await asyncio.sleep(self._check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background health monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


class MetricsCollector:
    """
    Metrics collection for infrastructure components.
    
    Collects and exposes metrics in Prometheus format for monitoring
    and alerting purposes.
    """
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self._metrics: Dict[str, Any] = {}
        self._enabled = config.monitoring.enable_metrics
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        if not self._enabled:
            return
        
        timestamp = datetime.utcnow()
        metric_data = {
            'value': value,
            'timestamp': timestamp,
            'labels': labels or {}
        }
        
        if name not in self._metrics:
            self._metrics[name] = []
        
        self._metrics[name].append(metric_data)
        
        # Keep only recent metrics (last hour)
        cutoff = timestamp - timedelta(hours=1)
        self._metrics[name] = [
            m for m in self._metrics[name] 
            if m['timestamp'] > cutoff
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self._metrics.copy()
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        if not self._enabled:
            return ""
        
        lines = []
        
        for metric_name, metric_data in self._metrics.items():
            if not metric_data:
                continue
            
            # Get latest value
            latest = metric_data[-1]
            
            # Format labels
            label_str = ""
            if latest['labels']:
                label_pairs = [f'{k}="{v}"' for k, v in latest['labels'].items()]
                label_str = "{" + ",".join(label_pairs) + "}"
            
            lines.append(f"{metric_name}{label_str} {latest['value']}")
        
        return "\n".join(lines)


class AlertManager:
    """
    Alert manager for infrastructure monitoring.
    
    Handles alerting based on health check results and metrics thresholds.
    """
    
    def __init__(self, config: InfrastructureConfig):
        self.config = config
        self._enabled = config.monitoring.enable_alerts
        self._webhook_url = config.monitoring.alert_webhook_url
        self._alert_history: List[Dict[str, Any]] = []
    
    async def check_alerts(self, health: SystemHealth) -> None:
        """Check for alert conditions based on health status."""
        if not self._enabled:
            return
        
        # Check for unhealthy components
        for component in health.components:
            if component.status == HealthStatus.UNHEALTHY:
                await self._send_alert(
                    severity="error",
                    title=f"Component {component.component} is unhealthy",
                    message=component.message,
                    component=component.component
                )
            elif component.status == HealthStatus.DEGRADED:
                await self._send_alert(
                    severity="warning",
                    title=f"Component {component.component} is degraded",
                    message=component.message,
                    component=component.component
                )
        
        # Check overall system health
        if health.status == HealthStatus.UNHEALTHY:
            await self._send_alert(
                severity="critical",
                title="System is unhealthy",
                message=f"Only {health.healthy_components}/{health.total_components} components healthy",
                component="system"
            )
    
    async def _send_alert(
        self,
        severity: str,
        title: str,
        message: str,
        component: str
    ) -> None:
        """Send an alert notification."""
        alert_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'title': title,
            'message': message,
            'component': component,
            'environment': self.config.environment
        }
        
        # Add to history
        self._alert_history.append(alert_data)
        
        # Keep only recent alerts (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._alert_history = [
            alert for alert in self._alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff
        ]
        
        # Send webhook if configured
        if self._webhook_url:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        self._webhook_url,
                        json=alert_data,
                        timeout=10.0
                    )
                logger.info(f"Sent alert: {title}")
            except Exception as e:
                logger.error(f"Failed to send alert webhook: {e}")
        else:
            logger.warning(f"Alert would be sent: {title} - {message}")
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        return self._alert_history.copy()


# Global monitoring instances
_health_checker: Optional[HealthChecker] = None
_metrics_collector: Optional[MetricsCollector] = None
_alert_manager: Optional[AlertManager] = None


def get_health_checker(config: Optional[InfrastructureConfig] = None) -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        from .config import get_config
        _health_checker = HealthChecker(config or get_config())
    return _health_checker


def get_metrics_collector(config: Optional[InfrastructureConfig] = None) -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        from .config import get_config
        _metrics_collector = MetricsCollector(config or get_config())
    return _metrics_collector


def get_alert_manager(config: Optional[InfrastructureConfig] = None) -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        from .config import get_config
        _alert_manager = AlertManager(config or get_config())
    return _alert_manager
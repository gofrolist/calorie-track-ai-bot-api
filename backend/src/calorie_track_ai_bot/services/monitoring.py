"""
Performance Monitoring Service

Provides comprehensive application performance monitoring including:
- System resource monitoring (CPU, memory, disk)
- Application metrics collection
- Performance benchmarking
- Health check metrics
- Real-time monitoring endpoints
"""

import asyncio
import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import psutil
import structlog

logger = structlog.get_logger(__name__)

INLINE_ACK_SLA_MS = 3000
INLINE_RESULT_SLA_MS = 12000


def record_inline_metadata(
    *,
    job_id: str,
    trigger_type: str,
    chat_type: str,
    consent: dict[str, Any],
    retention: dict[str, Any],
) -> None:
    """Record inline consent and retention metadata for telemetry consumption."""
    safe_consent = {
        "granted": consent.get("granted"),
        "scope": consent.get("scope"),
        "reference": consent.get("reference"),
        "retention_hours": consent.get("retention_hours"),
        "captured_at": consent.get("captured_at"),
    }
    safe_retention = {
        "expires_in_hours": retention.get("expires_in_hours"),
    }

    logger.info(
        "inline.metadata",
        job_id=job_id,
        trigger_type=trigger_type,
        chat_type=chat_type,
        consent=safe_consent,
        retention=safe_retention,
    )


class InlineTriggerMetrics:
    def __init__(self, window: int):
        self.ack_latencies: deque[int] = deque(maxlen=window)
        self.result_latencies: deque[int] = deque(maxlen=window)
        self.accuracy_deltas: deque[float] = deque(maxlen=window)
        self.permission_blocks: int = 0
        self.failure_reasons: dict[str, int] = {}


@dataclass
class InlineTelemetrySnapshot:
    trigger_type: str
    ack_p95_ms: float
    result_p95_ms: float
    avg_accuracy_delta_pct: float
    permission_blocks: int
    permission_blocks_by_chat: dict[str, int]
    sample_size: int
    failure_reasons: dict[str, int]


class InlineTelemetry:
    def __init__(self, window: int = 200):
        self._window = window
        self._lock = threading.RLock()
        self._metrics: dict[str, InlineTriggerMetrics] = {}
        self._permission_blocks_by_chat: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def _get_metrics(self, trigger_type: str) -> InlineTriggerMetrics:
        metrics = self._metrics.get(trigger_type)
        if metrics is None:
            metrics = InlineTriggerMetrics(self._window)
            self._metrics[trigger_type] = metrics
        return metrics

    def record_ack_latency(self, trigger_type: str, latency_ms: int) -> None:
        with self._lock:
            self._get_metrics(trigger_type).ack_latencies.append(latency_ms)
            self._get_metrics("__all__").ack_latencies.append(latency_ms)

        logger.info(
            "inline.telemetry.ack_latency", trigger_type=trigger_type, latency_ms=latency_ms
        )
        if latency_ms > INLINE_ACK_SLA_MS:
            logger.warning(
                "inline.telemetry.ack_sla_breach",
                trigger_type=trigger_type,
                latency_ms=latency_ms,
                sla_ms=INLINE_ACK_SLA_MS,
            )

    def record_result_latency(self, trigger_type: str, latency_ms: int) -> None:
        with self._lock:
            self._get_metrics(trigger_type).result_latencies.append(latency_ms)
            self._get_metrics("__all__").result_latencies.append(latency_ms)

        logger.info(
            "inline.telemetry.result_latency", trigger_type=trigger_type, latency_ms=latency_ms
        )
        if latency_ms > INLINE_RESULT_SLA_MS:
            logger.warning(
                "inline.telemetry.result_sla_breach",
                trigger_type=trigger_type,
                latency_ms=latency_ms,
                sla_ms=INLINE_RESULT_SLA_MS,
            )

    def record_accuracy_delta(self, trigger_type: str, delta_pct: float) -> None:
        with self._lock:
            self._get_metrics(trigger_type).accuracy_deltas.append(delta_pct)
            self._get_metrics("__all__").accuracy_deltas.append(delta_pct)

        logger.info("inline.telemetry.accuracy", trigger_type=trigger_type, delta_pct=delta_pct)

    def record_permission_block(self, trigger_type: str, chat_type: str) -> None:
        with self._lock:
            self._get_metrics(trigger_type).permission_blocks += 1
            self._get_metrics("__all__").permission_blocks += 1
            self._permission_blocks_by_chat[trigger_type][chat_type] += 1
            self._permission_blocks_by_chat["__all__"][chat_type] += 1

        logger.warning(
            "inline.telemetry.permission_block",
            trigger_type=trigger_type,
            chat_type=chat_type,
        )

    def record_failure(self, trigger_type: str, reason: str) -> None:
        with self._lock:
            metrics = self._get_metrics(trigger_type)
            metrics.failure_reasons[reason] = metrics.failure_reasons.get(reason, 0) + 1
            all_metrics = self._get_metrics("__all__")
            all_metrics.failure_reasons[reason] = all_metrics.failure_reasons.get(reason, 0) + 1

        logger.error(
            "inline.telemetry.failure",
            trigger_type=trigger_type,
            reason=reason,
        )

    def snapshot(self, trigger_type: str | None = None) -> InlineTelemetrySnapshot:
        key = trigger_type or "__all__"
        with self._lock:
            metrics = self._metrics.get(key)
            if metrics is None:
                metrics = InlineTriggerMetrics(self._window)
                self._metrics[key] = metrics
            ack_values = list(metrics.ack_latencies)
            result_values = list(metrics.result_latencies)
            accuracy_values = list(metrics.accuracy_deltas)
            permission_blocks = metrics.permission_blocks
            blocks_by_chat = dict(self._permission_blocks_by_chat.get(key, {}))

        return InlineTelemetrySnapshot(
            trigger_type=key,
            ack_p95_ms=_percentile(ack_values, 0.95),
            result_p95_ms=_percentile(result_values, 0.95),
            avg_accuracy_delta_pct=(sum(accuracy_values) / len(accuracy_values))
            if accuracy_values
            else 0.0,
            permission_blocks=permission_blocks,
            permission_blocks_by_chat=blocks_by_chat,
            sample_size=len(ack_values),
            failure_reasons=dict(metrics.failure_reasons),
        )


def _percentile(values: Sequence[int | float], percentile: float) -> float:
    if not values:
        return 0.0
    data = sorted(float(v) for v in values)
    if len(data) <= 2:
        return data[-1]

    index = (len(data) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return data[int(index)]
    lower_value = data[lower]
    upper_value = data[upper]
    return lower_value + (upper_value - lower_value) * (index - lower)


_inline_telemetry = InlineTelemetry()


def record_inline_ack_latency(trigger_type: str, latency_ms: int) -> None:
    _inline_telemetry.record_ack_latency(trigger_type, latency_ms)


def record_inline_result_latency(trigger_type: str, latency_ms: int) -> None:
    _inline_telemetry.record_result_latency(trigger_type, latency_ms)


def record_inline_accuracy_delta(trigger_type: str, delta_pct: float) -> None:
    _inline_telemetry.record_accuracy_delta(trigger_type, delta_pct)


def record_inline_permission_block_event(trigger_type: str, chat_type: str) -> None:
    _inline_telemetry.record_permission_block(trigger_type, chat_type)


def get_inline_metrics_snapshot(trigger_type: str | None = None) -> InlineTelemetrySnapshot:
    return _inline_telemetry.snapshot(trigger_type)


def record_inline_failure_event(trigger_type: str, reason: str) -> None:
    _inline_telemetry.record_failure(trigger_type, reason)


@dataclass
class SystemMetrics:
    """System resource metrics."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: list[float]
    process_count: int


@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""

    timestamp: str
    active_requests: int
    total_requests: int
    error_rate_percent: float
    avg_response_time_ms: float
    cache_hit_rate_percent: float
    database_connections: int
    queue_size: int
    worker_status: str


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result."""

    operation: str
    duration_ms: float
    success: bool
    timestamp: str
    metadata: dict[str, Any] | None = None


class MetricsCollector:
    """Collects and aggregates system and application metrics."""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.system_metrics: deque[SystemMetrics] = deque(maxlen=history_size)
        self.app_metrics: deque[ApplicationMetrics] = deque(maxlen=history_size)
        self.benchmarks: deque[PerformanceBenchmark] = deque(maxlen=history_size)

        # Request tracking
        self._active_requests = 0
        self._total_requests = 0
        self._request_times: deque[float] = deque(maxlen=100)
        self._error_count = 0

        # Cache metrics
        self._cache_hits = 0
        self._cache_misses = 0

        # Thread safety
        self._lock = threading.RLock()

        logger.info("MetricsCollector initialized", history_size=history_size)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics - use non-blocking approach for better performance
            cpu_percent_raw = psutil.cpu_percent(interval=None)  # Non-blocking
            # Handle both single value and list returns from cpu_percent
            cpu_percent = (
                float(cpu_percent_raw)
                if isinstance(cpu_percent_raw, int | float)
                else float(cpu_percent_raw[0])
                if isinstance(cpu_percent_raw, list) and cpu_percent_raw
                else 0.0
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = float(memory.used) / 1024 / 1024
            memory_available_mb = float(memory.available) / 1024 / 1024

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_usage_percent = (float(disk.used) / float(disk.total)) * 100
            disk_free_gb = float(disk.free) / 1024 / 1024 / 1024

            # Network metrics
            try:
                net_io = psutil.net_io_counters()
                # Handle potential None return from net_io_counters
                if (
                    net_io is not None
                    and hasattr(net_io, "bytes_sent")
                    and hasattr(net_io, "bytes_recv")
                ):
                    network_bytes_sent = int(getattr(net_io, "bytes_sent", 0))
                    network_bytes_recv = int(getattr(net_io, "bytes_recv", 0))
                else:
                    network_bytes_sent = 0
                    network_bytes_recv = 0
            except (AttributeError, OSError):
                # Fallback if network monitoring is unavailable
                network_bytes_sent = 0
                network_bytes_recv = 0

            # Load average (Unix-like systems)
            try:
                load_avg_raw = psutil.getloadavg()
                load_avg = [float(x) for x in load_avg_raw] if load_avg_raw else [0.0, 0.0, 0.0]
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]  # Fallback for Windows

            # Process count - use cached approach for better performance
            try:
                process_count = len(psutil.pids())
            except (OSError, psutil.NoSuchProcess):
                # Fallback to a reasonable estimate if process enumeration fails
                process_count = 100  # Reasonable default for most systems

            metrics = SystemMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=float(memory.percent),
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                load_average=load_avg,
                process_count=process_count,
            )

            with self._lock:
                self.system_metrics.append(metrics)

            return metrics

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
            raise

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect current application metrics."""
        try:
            with self._lock:
                # Calculate error rate
                error_rate = (self._error_count / max(self._total_requests, 1)) * 100

                # Calculate average response time
                avg_response_time = (
                    sum(self._request_times) / len(self._request_times)
                    if self._request_times
                    else 0.0
                )

                # Calculate cache hit rate
                total_cache_ops = self._cache_hits + self._cache_misses
                cache_hit_rate = (
                    (self._cache_hits / total_cache_ops) * 100 if total_cache_ops > 0 else 0.0
                )

                metrics = ApplicationMetrics(
                    timestamp=datetime.now(UTC).isoformat(),
                    active_requests=self._active_requests,
                    total_requests=self._total_requests,
                    error_rate_percent=error_rate,
                    avg_response_time_ms=avg_response_time,
                    cache_hit_rate_percent=cache_hit_rate,
                    database_connections=0,  # TODO: Implement database connection tracking
                    queue_size=0,  # TODO: Implement queue size tracking
                    worker_status="unknown",  # TODO: Implement worker status tracking
                )

                self.app_metrics.append(metrics)
                return metrics

        except Exception as e:
            logger.error("Failed to collect application metrics", error=str(e))
            raise

    def record_request_start(self) -> str:
        """Record the start of a request. Returns correlation ID."""
        correlation_id = f"req_{time.time_ns()}"
        with self._lock:
            self._active_requests += 1
            self._total_requests += 1

        logger.debug("Request started", correlation_id=correlation_id)
        return correlation_id

    def record_request_end(self, correlation_id: str, duration_ms: float, success: bool = True):
        """Record the end of a request."""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            self._request_times.append(duration_ms)

            if not success:
                self._error_count += 1

        logger.debug(
            "Request completed",
            correlation_id=correlation_id,
            duration_ms=duration_ms,
            success=success,
        )

    def record_cache_hit(self):
        """Record a cache hit."""
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        with self._lock:
            self._cache_misses += 1

    def record_benchmark(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        """Record a performance benchmark."""
        benchmark = PerformanceBenchmark(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            timestamp=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )

        with self._lock:
            self.benchmarks.append(benchmark)

        logger.info(
            "Performance benchmark recorded",
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            metadata=metadata,
        )

    def get_recent_system_metrics(self, count: int = 10) -> list[SystemMetrics]:
        """Get recent system metrics."""
        with self._lock:
            return list(self.system_metrics)[-count:]

    def get_recent_app_metrics(self, count: int = 10) -> list[ApplicationMetrics]:
        """Get recent application metrics."""
        with self._lock:
            return list(self.app_metrics)[-count:]

    def get_recent_benchmarks(self, count: int = 50) -> list[PerformanceBenchmark]:
        """Get recent performance benchmarks."""
        with self._lock:
            return list(self.benchmarks)[-count:]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of current metrics."""
        try:
            system_metrics = self.collect_system_metrics()
            app_metrics = self.collect_application_metrics()

            recent_benchmarks = self.get_recent_benchmarks(10)
            avg_benchmark_time = (
                sum(b.duration_ms for b in recent_benchmarks) / len(recent_benchmarks)
                if recent_benchmarks
                else 0.0
            )

            return {
                "system": asdict(system_metrics),
                "application": asdict(app_metrics),
                "performance": {
                    "avg_benchmark_time_ms": avg_benchmark_time,
                    "total_benchmarks": len(self.benchmarks),
                    "recent_benchmarks": len(recent_benchmarks),
                },
                "health_status": self._assess_health(),
            }

        except Exception as e:
            logger.error("Failed to generate metrics summary", error=str(e))
            return {"error": str(e)}

    def _assess_health(self) -> str:
        """Assess overall system health based on metrics."""
        try:
            # Get latest metrics
            if not self.system_metrics or not self.app_metrics:
                return "insufficient_data"

            latest_system = self.system_metrics[-1]
            latest_app = self.app_metrics[-1]

            # Health criteria
            cpu_healthy = latest_system.cpu_percent < 80
            memory_healthy = latest_system.memory_percent < 85
            disk_healthy = latest_system.disk_usage_percent < 90
            response_time_healthy = latest_app.avg_response_time_ms < 1000
            error_rate_healthy = latest_app.error_rate_percent < 5

            if all(
                [
                    cpu_healthy,
                    memory_healthy,
                    disk_healthy,
                    response_time_healthy,
                    error_rate_healthy,
                ]
            ):
                return "healthy"
            elif latest_system.cpu_percent > 95 or latest_system.memory_percent > 95:
                return "critical"
            else:
                return "warning"

        except Exception as e:
            logger.error("Failed to assess health", error=str(e))
            return "unknown"


class PerformanceMonitor:
    """Main performance monitoring service."""

    def __init__(self, collection_interval: float = 30.0):
        self.collection_interval = collection_interval
        self.metrics_collector = MetricsCollector()
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

        logger.info("PerformanceMonitor initialized", collection_interval=collection_interval)

    async def start_monitoring(self):
        """Start continuous monitoring."""
        if self._running:
            logger.warning("Monitoring already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self._running:
            return

        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self._running:
                try:
                    # Collect metrics
                    self.metrics_collector.collect_system_metrics()
                    self.metrics_collector.collect_application_metrics()

                    # Wait for next collection
                    await asyncio.sleep(self.collection_interval)

                except Exception as e:
                    logger.error("Error in monitoring loop", error=str(e))
                    await asyncio.sleep(5)  # Brief pause before retrying

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error("Monitoring loop failed", error=str(e))

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get current metrics summary."""
        return self.metrics_collector.get_summary()

    def record_request_metrics(self, duration_ms: float, success: bool = True):
        """Record request performance metrics."""
        correlation_id = self.metrics_collector.record_request_start()
        self.metrics_collector.record_request_end(correlation_id, duration_ms, success)

    def benchmark_operation(self, operation_name: str):
        """Context manager for benchmarking operations."""
        return PerformanceBenchmarkContext(self.metrics_collector, operation_name)


class PerformanceBenchmarkContext:
    """Context manager for performance benchmarking."""

    def __init__(self, metrics_collector: MetricsCollector, operation_name: str):
        self.metrics_collector = metrics_collector
        self.operation_name = operation_name
        self.start_time = 0.0
        self.metadata: dict[str, Any] = {}

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        success = exc_type is None

        if exc_type:
            self.metadata["error"] = str(exc_val)

        self.metrics_collector.record_benchmark(
            operation=self.operation_name,
            duration_ms=duration_ms,
            success=success,
            metadata=self.metadata,
        )

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the benchmark."""
        self.metadata[key] = value


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


async def get_performance_summary() -> dict[str, Any]:
    """Get current performance summary."""
    return performance_monitor.get_metrics_summary()


async def start_performance_monitoring():
    """Start performance monitoring service."""
    await performance_monitor.start_monitoring()


async def stop_performance_monitoring():
    """Stop performance monitoring service."""
    await performance_monitor.stop_monitoring()


def benchmark_operation(operation_name: str):
    """Decorator for benchmarking function performance."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                with performance_monitor.benchmark_operation(operation_name) as benchmark:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        benchmark.add_metadata("error_type", type(e).__name__)
                        raise

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                with performance_monitor.benchmark_operation(operation_name) as benchmark:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        benchmark.add_metadata("error_type", type(e).__name__)
                        raise

            return sync_wrapper

    return decorator


# Export main components
__all__ = [
    "ApplicationMetrics",
    "MetricsCollector",
    "PerformanceBenchmark",
    "PerformanceMonitor",
    "SystemMetrics",
    "benchmark_operation",
    "get_performance_summary",
    "performance_monitor",
    "start_performance_monitoring",
    "stop_performance_monitoring",
]

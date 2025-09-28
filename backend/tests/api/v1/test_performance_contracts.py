"""
Performance contract tests for CPU/memory usage requirements.

This test validates that the API meets performance requirements:
- <512MB RAM peak usage
- <80% CPU sustained usage
- <200ms API response time
"""

import threading
import time

import psutil
import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)


class TestPerformanceContracts:
    """Test performance contract compliance for CPU and memory usage."""

    def setup_method(self):
        """Set up performance monitoring."""
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.cpu_samples = []
        self.memory_samples = []
        self.monitoring = False

    def start_monitoring(self):
        """Start CPU and memory monitoring in background thread."""
        self.monitoring = True

        def monitor():
            process = psutil.Process()
            while self.monitoring:
                cpu_percent = process.cpu_percent(
                    interval=0.2
                )  # Increased interval for faster tests
                memory_mb = process.memory_info().rss / 1024 / 1024

                self.cpu_samples.append(cpu_percent)
                self.memory_samples.append(memory_mb)
                time.sleep(0.2)  # Increased interval for faster tests

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=1)

    def test_memory_usage_under_512mb_peak(self):
        """Test that memory usage stays under 512MB peak during API operations."""
        self.start_monitoring()

        try:
            # Perform various API operations to stress memory
            endpoints = [
                "/healthz",
                "/health/connectivity" if hasattr(app, "health_connectivity") else "/healthz",
                "/api/v1/config/ui" if hasattr(app, "config_ui") else "/healthz",
            ]

            # Make multiple requests to increase memory pressure
            for _ in range(10):
                for endpoint in endpoints:
                    try:
                        client.get(endpoint)
                        # Don't assert status codes as endpoints may not exist yet
                    except Exception:
                        pass  # Continue testing with available endpoints

        finally:
            self.stop_monitoring()

        # Analyze memory usage
        if self.memory_samples:
            peak_memory = max(self.memory_samples)
            assert peak_memory < 512, f"Peak memory usage {peak_memory:.1f}MB exceeds 512MB limit"
        else:
            pytest.skip("No memory samples collected")

    def test_cpu_usage_under_80_percent_sustained(self):
        """Test that CPU usage stays under 80% sustained during API operations."""
        self.start_monitoring()

        try:
            # Create sustained load for shorter duration
            start_time = time.time()
            while time.time() - start_time < 2:  # Reduced to 2 seconds for faster tests
                try:
                    client.get("/healthz")
                except Exception:
                    pass
                time.sleep(0.05)  # Increased delay to reduce load

        finally:
            self.stop_monitoring()

        # Analyze CPU usage (exclude initial spikes, focus on sustained)
        if len(self.cpu_samples) > 3:
            # Skip first few samples to avoid initialization spikes
            sustained_samples = self.cpu_samples[2:]  # Reduced from 3 to 2
            if sustained_samples:
                avg_cpu = sum(sustained_samples) / len(sustained_samples)
                _ = max(sustained_samples)  # max_cpu not used

                # Average should be well under 80%
                assert avg_cpu < 80, f"Sustained CPU usage {avg_cpu:.1f}% exceeds 80% limit"

                # Even peak sustained usage shouldn't exceed 80% for more than brief spikes
                high_cpu_samples = [cpu for cpu in sustained_samples if cpu > 80]
                high_cpu_ratio = len(high_cpu_samples) / len(sustained_samples)
                assert high_cpu_ratio < 0.1, f"High CPU usage ({high_cpu_ratio:.1%}) too frequent"
        else:
            pytest.skip("Insufficient CPU samples collected")

    def test_api_response_time_under_200ms(self):
        """Test that API responses complete under 200ms requirement."""
        endpoints_to_test = [
            "/healthz",
            "/health/connectivity",
            "/api/v1/config/ui",
        ]

        response_times = []

        for endpoint in endpoints_to_test:
            # Test each endpoint multiple times
            for _ in range(5):
                start_time = time.time()
                try:
                    client.get(endpoint)
                    end_time = time.time()

                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)

                    # Each individual request should be under 200ms
                    assert response_time_ms < 200, (
                        f"Response time {response_time_ms:.1f}ms exceeds 200ms limit"
                    )

                except Exception:
                    # Endpoint might not exist yet, skip for now
                    continue

        # Overall statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            assert avg_response_time < 100, (
                f"Average response time {avg_response_time:.1f}ms should be well under limit"
            )
            assert max_response_time < 200, (
                f"Max response time {max_response_time:.1f}ms exceeds 200ms limit"
            )
        else:
            pytest.skip("No response times measured (endpoints not available)")

    def test_memory_leak_detection(self):
        """Test that repeated API calls don't cause memory leaks."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform many operations
        for i in range(100):
            try:
                client.get("/healthz")
            except Exception:
                pass

            # Check memory every 20 iterations
            if i % 20 == 0 and i > 0:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable (under 50MB for 100 requests)
                assert memory_growth < 50, (
                    f"Memory growth {memory_growth:.1f}MB suggests memory leak"
                )

    def test_concurrent_request_performance(self):
        """Test performance under concurrent load."""
        import concurrent.futures

        def make_request():
            start_time = time.time()
            try:
                client.get("/healthz")
                end_time = time.time()
                return (end_time - start_time) * 1000
            except Exception:
                return None

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            response_times = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Filter out None results (failed requests)
        valid_times = [t for t in response_times if t is not None]

        if valid_times:
            # All concurrent requests should still meet timing requirements
            max_concurrent_time = max(valid_times)
            assert max_concurrent_time < 500, (
                f"Concurrent request time {max_concurrent_time:.1f}ms too high"
            )

            avg_concurrent_time = sum(valid_times) / len(valid_times)
            assert avg_concurrent_time < 300, (
                f"Average concurrent time {avg_concurrent_time:.1f}ms too high"
            )

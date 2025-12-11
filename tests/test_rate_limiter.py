"""Tests for the rate limiter module."""

import asyncio
import time

import pytest

from scripts.ingestion.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test suite for the RateLimiter class."""

    @pytest.mark.asyncio
    async def test_acquire_single_token(self):
        """Test acquiring a single token when rate limit is not exceeded."""
        rate_limiter = RateLimiter(rate=10, capacity=10)
        start_time = time.monotonic()
        await rate_limiter.acquire()
        elapsed = time.monotonic() - start_time
        assert elapsed < 0.1  # Should be almost immediate

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that the rate limiter enforces the rate limit."""
        rate = 5  # 5 tokens per second
        capacity = 5
        rate_limiter = RateLimiter(rate=rate, capacity=capacity)

        # Consume all tokens
        for _ in range(capacity):
            await rate_limiter.acquire()

        # Next acquire should be rate limited
        start_time = time.monotonic()
        await rate_limiter.acquire()
        elapsed = time.monotonic() - start_time

        # Should have waited approximately 1/rate seconds
        assert 0.15 <= elapsed <= 0.25  # 0.2s ± 0.05s

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        """Test that the rate limiter works with concurrent acquires."""
        rate_limiter = RateLimiter(rate=10, capacity=10)

        # Start multiple coroutines that all try to acquire tokens
        tasks = [rate_limiter.acquire() for _ in range(5)]
        start_time = time.monotonic()
        await asyncio.gather(*tasks)
        elapsed = time.monotonic() - start_time

        # All should complete almost immediately
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """Test that the rate limiter respects the capacity limit."""
        rate_limiter = RateLimiter(rate=1, capacity=2)

        # Acquire all available tokens
        await rate_limiter.acquire()
        await rate_limiter.acquire()

        # Next acquire should be rate limited
        start_time = time.monotonic()
        acquire_task = asyncio.create_task(rate_limiter.acquire())

        # Wait a bit to ensure the task is waiting
        await asyncio.sleep(0.1)
        assert not acquire_task.done()

        # After 1 second, the task should complete
        await asyncio.wait_for(acquire_task, timeout=1.1)
        elapsed = time.monotonic() - start_time

        # Should have waited approximately 1 second
        assert 0.9 <= elapsed <= 1.1

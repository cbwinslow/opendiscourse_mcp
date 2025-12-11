"""Rate limiting utility for controlling request rates."""
import asyncio
import time
from collections import deque
from typing import Deque


class RateLimiter:
    """Rate limiter with token bucket algorithm."""
    
    def __init__(self, rate: int, capacity: int):
        self.rate: int = rate  # tokens per second
        self.capacity: int = capacity  # max tokens
        self.tokens = capacity
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()
        self._waiters: Deque[asyncio.Future] = deque()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        while True:
            async with self._lock:
                now = time.monotonic()
                # Add new tokens
                if self.tokens < self.capacity:
                    self.tokens = min(
                        self.capacity,
                        self.tokens + (now - self.updated_at) * self.rate
                    )
                    self.updated_at = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Not enough tokens, wait
                fut: asyncio.Future = asyncio.Future()
                self._waiters.append(fut)
            
            try:
                await fut
            except asyncio.CancelledError:
                fut.cancel()
                raise

    async def release(self) -> None:
        """Release a waiter if any."""
        async with self._lock:
            if self._waiters:
                self._waiters.popleft().set_result(None)

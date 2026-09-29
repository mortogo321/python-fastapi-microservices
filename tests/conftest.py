"""Shared test fakes and fixtures (no live Redis needed)."""

from typing import Any

import pytest

from app.libs import redis as redis_module
from app.libs.config import settings


class FakeRedis:
    """Minimal in-memory async Redis stand-in for hash + stream ops."""

    def __init__(self, ping_error: Exception | None = None) -> None:
        self.hashes: dict[str, dict[str, str]] = {}
        self.streams: dict[str, list[dict[str, Any]]] = {}
        self.ping_error = ping_error

    async def ping(self) -> bool:
        if self.ping_error is not None:
            raise self.ping_error
        return True

    async def hset(self, key: str, mapping: dict[str, str] | None = None, **kwargs: str) -> int:
        store = self.hashes.setdefault(key, {})
        data = dict(mapping or {})
        data.update(kwargs)
        store.update(data)
        return len(data)

    async def hgetall(self, key: str) -> dict[str, str]:
        return dict(self.hashes.get(key, {}))

    async def scan_iter(self, pattern: str) -> Any:
        prefix = pattern.removesuffix("*")
        for key in list(self.hashes.keys()):
            if key.startswith(prefix):
                yield key

    async def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if key in self.hashes:
                del self.hashes[key]
                removed += 1
        return removed

    async def xadd(self, stream: str, fields: dict[str, Any]) -> str:
        entries = self.streams.setdefault(stream, [])
        entry_id = f"0-{len(entries) + 1}"
        entries.append(dict(fields))
        return entry_id

    async def aclose(self) -> None:
        return None


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def wired_redis(fake_redis: FakeRedis) -> FakeRedis:
    """Wire the fake into the global client used by both services."""
    redis_module.redis_client._client = fake_redis  # type: ignore[assignment]
    yield fake_redis
    redis_module.redis_client._client = None


@pytest.fixture(autouse=True)
def _fast_order_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep background completion instant in tests."""
    monkeypatch.setattr(settings, "order_complete_delay_seconds", 0.0)

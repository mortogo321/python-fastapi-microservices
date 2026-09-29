import json
from typing import Any, TypeVar
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel

from app.libs.config import settings

T = TypeVar("T", bound=BaseModel)


def _decode_value(value: str) -> Any:
    """Decode a Redis hash field back to a Python object (best effort)."""
    text = value.strip()
    if not text:
        return text
    if text[0] in ("{", "[", '"'):
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return value
    if text in ("true", "false"):
        return text == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return value


class RedisClient:
    """Modern async Redis client with Pydantic model support."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        password = settings.redis_password or None
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=password,
            db=settings.redis_db,
            decode_responses=settings.redis_decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    @staticmethod
    def _to_hash(model: BaseModel) -> dict[str, str]:
        """Serialize a model to a Redis-hash mapping (pk excluded)."""
        data = model.model_dump(mode="json", exclude={"pk"})
        return {k: v if isinstance(v, str) else json.dumps(v) for k, v in data.items()}

    async def save_model(self, model: BaseModel, prefix: str) -> str:
        """Save a new Pydantic model to Redis as a hash. Returns the new pk."""
        pk = str(uuid4())
        key = f"{prefix}:{pk}"
        await self.client.hset(key, mapping=self._to_hash(model))  # type: ignore[arg-type]
        return pk

    async def update_model(self, pk: str, model: BaseModel, prefix: str) -> None:
        """Overwrite the stored hash for an existing pk (no new key)."""
        key = f"{prefix}:{pk}"
        await self.client.hset(key, mapping=self._to_hash(model))  # type: ignore[arg-type]

    async def get_model(self, pk: str, prefix: str, model_class: type[T]) -> T | None:
        """Retrieve a Pydantic model from Redis."""
        key = f"{prefix}:{pk}"
        data = await self.client.hgetall(key)
        if not data:
            return None
        parsed: dict[str, Any] = {}
        for raw_k, raw_v in data.items():
            k = raw_k.decode() if isinstance(raw_k, bytes) else str(raw_k)
            v = raw_v.decode() if isinstance(raw_v, bytes) else str(raw_v)
            parsed[k] = _decode_value(v)
        return model_class(**parsed)

    async def get_all_keys(self, prefix: str) -> list[str]:
        """Get all pks with the given prefix."""
        pattern = f"{prefix}:*"
        keys: list[str] = []
        async for key in self.client.scan_iter(pattern):
            name = key.decode() if isinstance(key, bytes) else str(key)
            pk = name.split(":", 1)[1] if ":" in name else name
            keys.append(pk)
        return keys

    async def delete_model(self, pk: str, prefix: str) -> int:
        """Delete a model from Redis. Returns number of keys removed."""
        key = f"{prefix}:{pk}"
        return int(await self.client.delete(key))

    async def xadd(self, stream_name: str, data: dict[str, Any]) -> str:
        """Add entry to Redis stream. Returns the entry ID."""
        string_data = {
            k: v if isinstance(v, (str, bytes)) else json.dumps(v) for k, v in data.items()
        }
        result: Any = await self.client.xadd(stream_name, string_data)  # type: ignore[arg-type]
        return result.decode() if isinstance(result, bytes) else str(result)


# Global Redis client instance
redis_client = RedisClient()

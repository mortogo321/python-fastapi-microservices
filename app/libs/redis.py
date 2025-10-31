import json
from typing import Any, TypeVar
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel

from app.libs.config import settings

T = TypeVar("T", bound=BaseModel)


class RedisClient:
    """Modern async Redis client with Pydantic model support."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=settings.redis_decode_responses,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def save_model(self, model: BaseModel, prefix: str) -> str:
        """Save a Pydantic model to Redis as a hash."""
        pk = str(uuid4())
        key = f"{prefix}:{pk}"
        data = model.model_dump()
        # Convert all values to strings for Redis hash
        string_data = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in data.items()}
        await self.client.hset(key, mapping=string_data)  # type: ignore
        return pk

    async def get_model(self, pk: str, prefix: str, model_class: type[T]) -> T | None:
        """Retrieve a Pydantic model from Redis."""
        key = f"{prefix}:{pk}"
        data = await self.client.hgetall(key)
        if not data:
            return None
        # Convert JSON strings back to Python objects
        parsed_data = {k: json.loads(v) if v.startswith(("{", "[", '"')) else v for k, v in data.items()}
        return model_class(**parsed_data)

    async def get_all_keys(self, prefix: str) -> list[str]:
        """Get all keys with the given prefix."""
        pattern = f"{prefix}:*"
        keys = []
        async for key in self.client.scan_iter(pattern):  # type: ignore
            # Extract the PK from the key
            pk = key.split(":", 1)[1] if ":" in key else key
            keys.append(pk)
        return keys

    async def delete_model(self, pk: str, prefix: str) -> int:
        """Delete a model from Redis."""
        key = f"{prefix}:{pk}"
        return await self.client.delete(key)  # type: ignore

    async def xadd(self, stream_name: str, data: dict[str, Any]) -> bytes:
        """Add entry to Redis stream."""
        # Convert all values to strings
        string_data = {k: json.dumps(v) if not isinstance(v, (str, bytes)) else v for k, v in data.items()}
        return await self.client.xadd(stream_name, string_data)  # type: ignore


# Global Redis client instance
redis_client = RedisClient()

import os
from typing import Any

import redis.asyncio as aioredis

_pool: aioredis.ConnectionPool | None = None


def get_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


def get_client() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=get_pool())


# Key helpers
def session_context_key(session_id: str) -> str:
    return f"session:{session_id}:context"


def token_blacklist_key(jti: str) -> str:
    return f"blacklist:token:{jti}"


def refresh_token_key(user_id: str, device_id: str) -> str:
    return f"refresh:{user_id}:{device_id}"


def agent_catalog_key() -> str:
    return "agent:catalog"


def kb_status_key(kb_id: str) -> str:
    return f"kb:{kb_id}:status"


# Convenience wrappers
async def get(key: str) -> str | None:
    async with get_client() as client:
        return await client.get(key)


async def set(key: str, value: Any, ex: int | None = None) -> None:
    async with get_client() as client:
        await client.set(key, value, ex=ex)


async def delete(*keys: str) -> None:
    async with get_client() as client:
        if keys:
            await client.delete(*keys)


async def expire(key: str, seconds: int) -> None:
    async with get_client() as client:
        await client.expire(key, seconds)


async def get_json(key: str) -> Any | None:
    import json
    value = await get(key)
    return json.loads(value) if value else None


async def set_json(key: str, value: Any, ex: int | None = None) -> None:
    import json
    await set(key, json.dumps(value), ex=ex)

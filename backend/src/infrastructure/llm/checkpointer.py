import os

from langgraph.checkpoint.redis.aio import AsyncRedisSaver


def get_checkpointer() -> AsyncRedisSaver:
    redis_url = (
        f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}"
    )
    return AsyncRedisSaver.from_conn_string(redis_url)

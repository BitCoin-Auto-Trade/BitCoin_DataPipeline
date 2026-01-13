import json
import redis
from shared.env import REDIS_HOST, REDIS_PORT


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def set_json(self, key: str, data: dict) -> None:
        self.client.set(key, json.dumps(data, ensure_ascii=False))
import json
import redis
from shared.utils.env import REDIS_HOST, REDIS_PORT


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def set_json(self, key: str, data: dict, ex: int) -> None:
        """JSON 문자열로 저장"""
        self.client.set(key, json.dumps(data, ensure_ascii=False), ex=ex)

    def set_hash(self, key: str, data: dict, ex: int) -> None:
        """Hash로 저장"""
        self.client.hset(key, mapping=data)
        if ex:
            self.client.expire(key, ex)
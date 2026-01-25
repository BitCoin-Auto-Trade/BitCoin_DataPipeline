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

    def set_json(self, key: str, data: dict, ex: int):
        self.client.set(key, json.dumps(data, ensure_ascii=False), ex=ex)

    def get_json(self, key: str):
        value = self.client.get(key)
        return json.loads(value)

    def set_hash(self, key: str, data: dict, ex: int):
        self.client.hset(key, mapping=data)
        if ex:
            self.client.expire(key, ex)

    def get_hash(self, key: str):
        return self.client.hgetall(key)

    def publish(self, channel: str, message: str):
        self.client.publish(channel, message)

    def subscribe(self, *channels):
        pubsub = self.client.pubsub()
        pubsub.subscribe(*channels)
        return pubsub

    def psubscribe(self, *patterns):
        pubsub = self.client.pubsub()
        pubsub.psubscribe(*patterns)
        return pubsub

    def rpush(self, key: str, value: str):
        self.client.rpush(key, value)

    def lrange(self, key: str, start: int, end: int) -> list:
        return self.client.lrange(key, start, end)

    def ltrim(self, key: str, start: int, end: int):
        self.client.ltrim(key, start, end)

    def llen(self, key: str) -> int:
        return self.client.llen(key)

    def delete(self, key: str):
        self.client.delete(key)

    def rename(self, key: str, new_key: str) -> bool:
        try:
            self.client.rename(key, new_key)
            return True
        except Exception:
            return False

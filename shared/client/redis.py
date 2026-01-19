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
        """JSON 문자열로 저장"""
        self.client.set(key, json.dumps(data, ensure_ascii=False), ex=ex)

    def get_json(self, key: str):
        """JSON 문자열을 dict로 가져오기"""
        value = self.client.get(key)
        return json.loads(value)

    def set_hash(self, key: str, data: dict, ex: int):
        """Hash로 저장"""
        self.client.hset(key, mapping=data)
        if ex:
            self.client.expire(key, ex)

    def get_hash(self, key: str):
        """Hash에서 가져오기"""
        value = self.client.hgetall(key)
        return value

    def publish(self, channel: str, message: str):
        """메시지 발행"""
        self.client.publish(channel, message)

    def subscribe(self, *channels):
        """채널 구독 (PubSub 객체 반환)"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(*channels)
        return pubsub

    def psubscribe(self, *patterns):
        """패턴 구독 (PubSub 객체 반환)"""
        pubsub = self.client.pubsub()
        pubsub.psubscribe(*patterns)
        return pubsub

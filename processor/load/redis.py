from utils import to_redis_hash


class RedisLoader:
    def __init__(self, redis, symbol):
        self.redis = redis
        self.symbol = symbol

    def save(self, data_type, data, ex=60):
        """core 테이블에 저장"""
        key = f"core:{data_type}:{self.symbol}"
        self.redis.set_hash(key, to_redis_hash(data.model_dump()), ex=ex)

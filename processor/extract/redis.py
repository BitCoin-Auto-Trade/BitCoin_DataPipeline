from utils import parse_redis_hash, now_ms
from shared.models.raw import (
    RawKline, RawAggTrade, RawOrderBook, RawSpotOrderBook, RawLiquidation
)


class RedisFetcher:
    def __init__(self, redis, symbol):
        self.redis = redis
        self.symbol = symbol

    def _get(self, market, data_type):
        key = f"raw:{market}:{data_type}:{self.symbol}"
        return parse_redis_hash(self.redis.get_hash(key))

    def get_timestamp(self, orderbook, market):
        """OrderBook timestamp (spot은 현재 시간)"""
        return now_ms() if market == "spot" else orderbook.transaction_time

    def get_kline(self, market):
        data = self._get(market, "kline")
        return RawKline(**data) if data else None

    def get_aggtrade(self, market):
        data = self._get(market, "aggtrade")
        return RawAggTrade(**data) if data else None

    def get_orderbook(self, market):
        data = self._get(market, "orderbook")
        if not data:
            return None
        return RawSpotOrderBook(**data) if market == "spot" else RawOrderBook(**data)

    def get_liquidation(self, market):
        data = self._get(market, "liquidation")
        return RawLiquidation(**data) if data else None

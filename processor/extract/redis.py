import json
import time
from typing import Optional, Union
from shared.client.redis import RedisClient
from shared.models.raw import RawKline, RawAggTrade, RawOrderBook, RawSpotOrderBook, RawLiquidation


class RedisFetcher:
    """Redis에서 실시간 Raw 데이터 조회"""

    def __init__(self, redis: RedisClient, symbol: str):
        self.redis = redis
        self.symbol = symbol

    def _parse_json(self, value: str):
        """JSON 문자열 파싱"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def _get_hash(self, market: str, data_type: str):
        """Redis Hash에서 데이터 조회"""
        key = f"raw:{market}:{data_type}:{self.symbol}"
        data = self.redis.get_hash(key)
        if not data:
            return None

        # JSON 필드 파싱
        for k, v in data.items():
            if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                data[k] = self._parse_json(v)
        return data

    def get_timestamp(self, orderbook: Union[RawOrderBook, RawSpotOrderBook], market: str):
        """OrderBook timestamp 조회 (spot은 현재 시간 사용)"""
        if market == "spot":
            return int(time.time() * 1000)
        return orderbook.transaction_time

    def get_kline(self, market: str):
        data = self._get_hash(market, "kline")
        return RawKline(**data) if data else None

    def get_aggtrade(self, market: str):
        data = self._get_hash(market, "aggtrade")
        return RawAggTrade(**data) if data else None

    def get_orderbook(self, market: str):
        data = self._get_hash(market, "orderbook")
        if not data:
            return None
        return RawSpotOrderBook(**data) if market == "spot" else RawOrderBook(**data)

    def get_liquidation(self, market: str):
        data = self._get_hash(market, "liquidation")
        return RawLiquidation(**data) if data else None

import asyncio
import json
import websockets
from typing import Literal
from shared.utils.constants import SYMBOLS
from shared.utils.logger import get_logger
from shared.models.raw import RawTicker


class BinanceWebsocketWorker:
    """Binance WebSocket Worker"""

    URLS = {
        "spot": "wss://stream.binance.com:9443/ws",
        "futures": "wss://fstream.binance.com/ws"
    }

    def __init__(self, market: Literal["spot", "futures"], redis, gcs):
        self.market = market
        self.redis = redis
        self.gcs = gcs
        self.logger = get_logger(market.capitalize())

    async def run(self):
        self.logger.info(f"Starting {self.market} Websocket worker...")

        streams = [f"{symbol}@ticker" for symbol in SYMBOLS]
        url = f"{self.URLS[self.market]}/{'/'.join(streams)}"

        while True:
            try:
                async with websockets.connect(url) as ws:
                    self.logger.info(f"Connected! Streaming {len(SYMBOLS)} symbols")

                    async for msg in ws:
                        try:
                            data = json.loads(msg)

                            # 멀티 스트림 응답 처리
                            if "data" in data:
                                data = data["data"]

                            if data.get("e") == "24hrTicker":
                                self._process_ticker(data)

                        except (json.JSONDecodeError, KeyError) as e:
                            self.logger.warning(f"Invalid data format: {e}")
                            continue

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Connection closed. Reconnecting in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

    def _process_ticker(self, data: dict):
        """Ticker 데이터 검증 및 Redis 저장"""
        try:
            ticker = RawTicker(
                market=self.market,
                symbol=data["s"],
                price=data["c"],
                high=data["h"],
                low=data["l"],
                volume=data["v"],
                timestamp=data["E"]
            )

            # Redis Hash에 저장 (TTL 60초)
            self.redis.set_hash(
                key=ticker.redis_key(),
                data=ticker.to_redis_hash(),
                ex=60
            )

            # 로그는 DEBUG 레벨로 (과다 로깅 방지)
            self.logger.debug(f"{ticker.symbol}: ${ticker.price}")

        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to process ticker: {e}")

import asyncio
import json
import websockets
from typing import Literal
from shared.utils.logger import get_logger
from shared.utils.constants import SYMBOL, BINANCE_WS_URLS
from shared.models.raw import RawKline, RawAggTrade, RawOrderBook, RawSpotOrderBook, RawLiquidation


class BinanceWebsocketWorker:
    """Binance WebSocket Worker"""

    def __init__(self, market: Literal["spot", "futures"], redis, gcs):
        self.market = market
        self.redis = redis
        self.gcs = gcs
        self.logger = get_logger(market.capitalize())

    def _get_streams(self) -> list:
        streams = [
            f"{SYMBOL}@kline_1m",
            f"{SYMBOL}@aggTrade",
            f"{SYMBOL}@depth20@100ms",
        ]
        if self.market == "futures":
            streams.append("!forceOrder@arr")
        return streams

    async def run(self):
        streams = self._get_streams()
        url = f"{BINANCE_WS_URLS[self.market]}/{'/'.join(streams)}"
        self.logger.info(f"Connecting to {len(streams)} streams...")

        while True:
            try:
                async with websockets.connect(url) as ws:
                    self.logger.info("Connected!")
                    async for msg in ws:
                        self._handle_message(msg)

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Connection closed. Reconnecting in 3s...")
                await asyncio.sleep(3)

    def _handle_message(self, msg: str):
        data = json.loads(msg)
        payload = data["data"] if "stream" in data else data
        event_type = payload.get("e")

        if event_type == "kline":
            self._process_kline(payload)
        elif event_type == "aggTrade":
            self._process_aggtrade(payload)
        elif event_type == "depthUpdate":
            self._process_orderbook(payload)
        elif "lastUpdateId" in payload:
            self._process_spot_orderbook(payload)
        elif event_type == "forceOrder":
            self._process_liquidation(payload)

    def _process_kline(self, data: dict):
        k = data["k"]
        raw = RawKline(**k)
        self.redis.set_hash(f"raw:{self.market}:kline:{SYMBOL}", raw.to_dict(), ex=30)
        if raw.is_closed:
            self.logger.debug(f"[KLINE] Close: {raw.close_price}")

    def _process_aggtrade(self, data: dict):
        raw = RawAggTrade(**data)
        self.redis.set_hash(f"raw:{self.market}:aggtrade:{SYMBOL}", raw.to_dict(), ex=30)
        side = "SELL" if raw.is_buyer_maker else "BUY"
        self.logger.debug(f"[TRADE] {side} {raw.quantity} @ {raw.price}")

    def _process_orderbook(self, data: dict):
        raw = RawOrderBook(**data)
        self.redis.set_hash(f"raw:{self.market}:orderbook:{SYMBOL}", raw.to_dict(), ex=30)
        self.logger.debug(f"[BOOK] Bid: {raw.bids[0][0]} | Ask: {raw.asks[0][0]}")

    def _process_spot_orderbook(self, data: dict):
        raw = RawSpotOrderBook(**data)
        self.redis.set_hash(f"raw:{self.market}:orderbook:{SYMBOL}", raw.to_dict(), ex=30)
        self.logger.debug(f"[BOOK] Bid: {raw.bids[0][0]} | Ask: {raw.asks[0][0]}")

    def _process_liquidation(self, data: dict):
        o = data["o"]
        raw = RawLiquidation(**o)
        self.redis.set_hash(f"raw:{self.market}:liquidation:{raw.symbol.lower()}", raw.to_dict(), ex=30)
        self.logger.debug(f"[LIQ] {raw.side} {raw.quantity} @ {raw.price}")

import asyncio
import json
import websockets
from typing import Literal
from shared.utils.logger import get_logger
from shared.utils.constants import SYMBOL, BINANCE_WS_URLS
from shared.models.raw import RawKline, RawAggTrade, RawOrderBook, RawSpotOrderBook, RawLiquidation


class BinanceWebsocketWorker:
    """Binance WebSocket 실시간 데이터 수집"""

    def __init__(self, market: Literal["spot", "futures"], redis):
        self.market = market
        self.redis = redis
        self.logger = get_logger(market.capitalize())

    def _get_streams(self):
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

        handlers = {
            "kline": self._process_kline,
            "aggTrade": self._process_aggtrade,
            "depthUpdate": self._process_orderbook,
            "forceOrder": self._process_liquidation,
        }

        if handler := handlers.get(event_type):
            handler(payload)
        elif "lastUpdateId" in payload:
            self._process_spot_orderbook(payload)

    def _publish(self, data_type: str, symbol: str = SYMBOL):
        self.redis.publish(f"data:{self.market}:{data_type}", symbol)

    def _push_queue(self, data_type: str, data: dict):
        key = f"queue:{self.market}:{data_type}"
        self.redis.rpush(key, json.dumps(data, ensure_ascii=False))

    def _save_and_queue(self, data_type: str, raw):
        data = raw.to_dict()
        self.redis.set_hash(f"raw:{self.market}:{data_type}:{SYMBOL}", data, ex=30)
        self._push_queue(data_type, data)

    def _process_kline(self, data: dict):
        raw = RawKline(**data["k"])
        self._save_and_queue("kline", raw)
        self._publish("kline")
        if raw.is_closed:
            self._publish("kline_closed")
            self.logger.debug(f"[KLINE] Close: {raw.close_price}")

    def _process_aggtrade(self, data: dict):
        raw = RawAggTrade(**data)
        self._save_and_queue("aggtrade", raw)
        self._publish("aggtrade")
        self.logger.debug(f"[TRADE] {'SELL' if raw.is_buyer_maker else 'BUY'} {raw.quantity} @ {raw.price}")

    def _process_orderbook(self, data: dict):
        raw = RawOrderBook(**data)
        self._save_and_queue("orderbook", raw)
        self._publish("orderbook")
        self.logger.debug(f"[BOOK] Bid: {raw.bids[0][0]} | Ask: {raw.asks[0][0]}")

    def _process_spot_orderbook(self, data: dict):
        raw = RawSpotOrderBook(**data)
        self._save_and_queue("orderbook", raw)
        self._publish("orderbook")
        self.logger.debug(f"[BOOK] Bid: {raw.bids[0][0]} | Ask: {raw.asks[0][0]}")

    def _process_liquidation(self, data: dict):
        raw = RawLiquidation(**data["o"])
        if raw.symbol.lower() != SYMBOL:
            return
        self._save_and_queue("liquidation", raw)
        self._publish("liquidation")
        self.logger.debug(f"[LIQ] {raw.side} {raw.quantity} @ {raw.price}")

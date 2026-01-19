import asyncio
from shared.utils.logger import setup_logger, get_logger
from shared.client.redis import RedisClient
from shared.client.gcs import GCSClient
from extract.redis import RedisFetcher
from extract.gcs import GCSFetcher
from transform.realtime import RealtimeTransformer
from transform.batch import BatchTransformer


class Processor:
    """이벤트 기반 데이터 처리기"""

    def __init__(self, symbol: str = "btcusdt"):
        self.symbol = symbol
        self.logger = get_logger("Processor")

        # 클라이언트
        self.redis = RedisClient()
        self.gcs = GCSClient()

        # Fetcher & Transformer
        redis_fetcher = RedisFetcher(self.redis, symbol)
        gcs_fetcher = GCSFetcher(self.gcs, symbol)
        self.realtime = RealtimeTransformer(redis_fetcher)
        self.batch = BatchTransformer(gcs_fetcher)

        # 상태
        self.prev_cvd = 0.0
        self.prev_oi = 0.0

    def _handle_aggtrade(self, market: str):
        """AggTrade -> CVD"""
        result = self.realtime.transform_cvd(market, self.prev_cvd)
        if result:
            self.prev_cvd = result.cvd
            self.logger.debug(f"[CVD] {result.cvd:.4f} delta={result.delta:.4f}")

    def _handle_orderbook(self, market: str):
        """OrderBook -> Imbalance, Spread, Wall"""
        imbalance = self.realtime.transform_book_imbalance(market)
        spread = self.realtime.transform_spread_analysis(market)
        wall = self.realtime.transform_wall_detection(market)

        if imbalance:
            self.logger.debug(f"[IMBALANCE] {imbalance.signal} ratio={imbalance.imbalance_ratio:.4f}")
        if spread:
            self.logger.debug(f"[SPREAD] {spread.liquidity_status} {spread.spread_percent:.6f}%")
        if wall and (wall.bid_walls or wall.ask_walls):
            self.logger.debug(f"[WALL] support={wall.strongest_support} resistance={wall.strongest_resistance}")

    def _handle_kline_closed(self, market: str):
        """Kline 완성 -> PriceVolSpike"""
        result = self.realtime.transform_price_vol_spike(market, avg_volume=0)
        if result:
            self.logger.info(f"[SPIKE] {result.signal} price={result.price_change_percent:.2f}%")

    def _handle_liquidation(self, market: str):
        """Liquidation -> LiqSpike"""
        result = self.realtime.transform_liq_spike(market, avg_liq_1h=0)
        if result:
            self.logger.info(f"[LIQ] {result.signal} value={result.current_liq_value:.2f}")

    def _process_message(self, channel: str):
        """Pub/Sub 메시지 처리"""
        parts = channel.split(":")
        if len(parts) != 3:
            return

        _, market, data_type = parts

        handlers = {
            "aggtrade": self._handle_aggtrade,
            "orderbook": self._handle_orderbook,
            "kline_closed": self._handle_kline_closed,
            "liquidation": self._handle_liquidation,
        }

        handler = handlers.get(data_type)
        if handler:
            handler(market)

    async def run_realtime(self):
        """실시간 데이터 처리 (Redis Pub/Sub)"""
        pubsub = self.redis.psubscribe("data:*")
        self.logger.info("Subscribed to data:* channels")

        while True:
            message = pubsub.get_message(timeout=0.1)
            if message and message["type"] == "pmessage":
                self._process_message(message["channel"])
            await asyncio.sleep(0.01)

    async def run_batch(self):
        """배치 데이터 처리 (GCS 주기적 폴링)"""
        redis_fetcher = RedisFetcher(self.redis, self.symbol)

        while True:
            # 가격 변화율 계산
            kline = redis_fetcher.get_kline("futures")
            price_chg = 0.0
            if kline:
                price_chg = ((float(kline.close_price) - float(kline.open_price)) / float(kline.open_price)) * 100

            # OI Trend
            oi_trend = self.batch.transform_oi_trend(self.prev_oi, price_chg)
            if oi_trend:
                self.prev_oi = oi_trend.open_interest
                self.logger.info(f"[OI] {oi_trend.trend_signal} oi={oi_trend.open_interest:.0f}")

            # FR Heatmap
            fr = self.batch.transform_fr_heatmap()
            if fr:
                self.logger.info(f"[FR] {fr.heat_level} rate={fr.funding_rate:.6f}")

            # LS Divergence
            ls = self.batch.transform_ls_divergence(price_chg)
            if ls:
                self.logger.info(f"[LS] {ls.signal} ratio={ls.ls_ratio:.4f}")

            await asyncio.sleep(60)

    async def run(self):
        """메인 실행"""
        self.logger.info("Processor started")
        await asyncio.gather(
            self.run_realtime(),
            self.run_batch(),
        )


async def main():
    setup_logger("processor")
    processor = Processor(symbol="btcusdt")
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())

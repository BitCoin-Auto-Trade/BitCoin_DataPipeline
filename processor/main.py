import asyncio
from shared.utils.logger import setup_logger, get_logger
from shared.client.redis import RedisClient
from shared.client.gcs import GCSClient
from shared.worker.redis_to_gcs import RedisToGCSWorker
from extract.redis import RedisFetcher
from extract.gcs import GCSFetcher
from transform.realtime import RealtimeTransformer
from transform.batch import BatchTransformer
from load.redis import RedisLoader
from load.gcs import GCSLoader
from utils import calc_change_percent
from shared.utils.constants import CORE_DATA_TYPES, GCS_UPLOAD_INTERVAL


class Processor:
    """이벤트 기반 데이터 처리기"""

    def __init__(self, symbol="btcusdt"):
        self.symbol = symbol
        self.logger = get_logger("Processor")

        self.redis = RedisClient()
        self.gcs = GCSClient()

        self.realtime = RealtimeTransformer(RedisFetcher(self.redis, symbol))
        self.batch = BatchTransformer(GCSFetcher(self.gcs, symbol))
        self.redis_loader = RedisLoader(self.redis, symbol)
        self.gcs_loader = GCSLoader(self.gcs, symbol)

        self.core_gcs_worker = RedisToGCSWorker(
            name="CoreToGCS",
            redis=self.redis,
            gcs=self.gcs,
            data_types=CORE_DATA_TYPES,
            redis_key_prefix="queue:core",
            gcs_path_prefix="core",
            interval_seconds=GCS_UPLOAD_INTERVAL,
        )

        self.prev_cvd = 0.0
        self.prev_oi = 0.0
        self.price_change_pct = {}  # market별 최신 kline 가격변화율
        self.avg_volume = {}        # market별 거래량 EMA

    def _handle_aggtrade(self, market):
        price_chg = self.price_change_pct.get(market, 0.0)
        result = self.realtime.transform_cvd(market, self.prev_cvd, price_chg)
        if result:
            self.prev_cvd = result.cvd
            self.redis_loader.save("cvd", result)
            self.logger.debug(
                f"[CVD] {result.cvd:.4f} delta={result.delta:.4f}")

    def _handle_orderbook(self, market):
        if imbalance := self.realtime.transform_book_imbalance(market):
            self.redis_loader.save("book_imbalance", imbalance)
            self.logger.debug(
                f"[IMBALANCE] {imbalance.signal} ratio={imbalance.imbalance_ratio:.4f}")

        if spread := self.realtime.transform_spread_analysis(market):
            self.redis_loader.save("spread_analysis", spread)
            self.logger.debug(
                f"[SPREAD] {spread.liquidity_status} {spread.spread_percent:.6f}%")

        if wall := self.realtime.transform_wall_detection(market):
            self.redis_loader.save("wall_detection", wall)
            if wall.bid_walls or wall.ask_walls:
                self.logger.debug(
                    f"[WALL] support={wall.strongest_support} resistance={wall.strongest_resistance}")

    def _handle_kline_closed(self, market):
        kline = self.realtime.fetcher.get_kline(market)
        if kline:
            open_p = float(kline.open_price)
            close_p = float(kline.close_price)
            vol = float(kline.volume)
            self.price_change_pct[market] = calc_change_percent(close_p, open_p)
            # 거래량 EMA (alpha=0.1 ≈ 약 19봉 이동평균 가중치)
            prev_avg = self.avg_volume.get(market, 0.0)
            self.avg_volume[market] = vol if prev_avg == 0 else 0.1 * vol + 0.9 * prev_avg

        avg_vol = self.avg_volume.get(market, 0.0)
        if result := self.realtime.transform_price_vol_spike(market, avg_vol):
            self.redis_loader.save("price_vol_spike", result)
            self.logger.info(
                f"[SPIKE] {result.signal} price={result.price_change_percent:.2f}% vol_ratio={result.volume_ratio:.2f}")

    def _handle_liquidation(self, market):
        if result := self.realtime.transform_liq_spike(market):
            self.redis_loader.save("liq_spike", result)
            self.logger.info(
                f"[LIQ] {result.signal} value={result.current_liq_value:.2f}")

    def _process_message(self, channel):
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
        if handler := handlers.get(data_type):
            handler(market)

    async def run_realtime(self):
        pubsub = self.redis.psubscribe("data:*")
        self.logger.info("Subscribed to data:* channels")

        while True:
            msg = pubsub.get_message(timeout=0.1)
            if msg and msg["type"] == "pmessage":
                self._process_message(msg["channel"])
            await asyncio.sleep(0.01)

    async def run_batch(self):
        fetcher = RedisFetcher(self.redis, self.symbol)

        while True:
            kline = fetcher.get_kline("futures")
            price_chg = 0.0
            if kline:
                price_chg = calc_change_percent(
                    float(kline.close_price), float(kline.open_price))

            if oi := self.batch.transform_oi_trend(self.prev_oi, price_chg):
                self.prev_oi = oi.open_interest
                self.gcs_loader.save("oi_trend", oi)
                self.logger.info(
                    f"[OI] {oi.trend_signal} oi={oi.open_interest:.0f}")

            if fr := self.batch.transform_fr_heatmap():
                self.gcs_loader.save("fr_heatmap", fr)
                self.logger.info(
                    f"[FR] {fr.heat_level} rate={fr.funding_rate:.6f}")

            if ls := self.batch.transform_ls_divergence(price_chg):
                self.gcs_loader.save("ls_divergence", ls)
                self.logger.info(f"[LS] {ls.signal} ratio={ls.ls_ratio:.4f}")

            await asyncio.sleep(60)

    async def run(self):
        self.logger.info("Processor started")
        await asyncio.gather(
            self.run_realtime(),
            self.run_batch(),
            self.core_gcs_worker.run(),
        )


async def main():
    setup_logger("processor")
    await Processor().run()


if __name__ == "__main__":
    asyncio.run(main())

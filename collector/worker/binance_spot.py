import asyncio
from shared.env import BINANCE_APP_ACCESS_KEY, BINANCE_APP_SECRET_KEY


class BinanceSpotWorker:
    def __init__(self, redis, gcs):
        self.access_key = BINANCE_APP_ACCESS_KEY
        self.secret_key = BINANCE_APP_SECRET_KEY
        self.redis = redis
        self.gcs = gcs

    async def run(self):
        print(f"[BinanceSpotWorker] Started with key: {self.access_key[:10]}...")

        while True:
            try:
                # TODO: Binance Spot API 호출 및 데이터 수집
                print("[BinanceSpotWorker] Collecting data...")
                await asyncio.sleep(60)
            except Exception as e:
                print(f"[BinanceSpotWorker] Error: {e}")
                await asyncio.sleep(5)
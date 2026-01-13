import asyncio

from client.gcs import GCSClient
from client.redis import RedisClient

from worker.binance_futures import BinanceFuturesWorker
from worker.binance_spot import BinanceSpotWorker


async def main():
    # 1. 클라이언트 초기화
    redis = RedisClient()
    gcs = GCSClient()

    # 2. 워커 생성 (클라이언트를 주입)
    binance_futures = BinanceFuturesWorker(redis=redis, gcs=gcs)
    binance_spot = BinanceSpotWorker(redis=redis, gcs=gcs)

    # 3. 동시에 실행
    await asyncio.gather(
        binance_futures.run(),
        binance_spot.run()
    )


if __name__ == "__main__":
    asyncio.run(main())
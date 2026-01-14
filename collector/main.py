import asyncio
from shared.utils.logger import setup_logger
from client.gcs import GCSClient
from client.redis import RedisClient
from collector.worker.binance_ws import BinanceWebsocketWorker


async def main():
    setup_logger("collector")

    redis = RedisClient()
    gcs = GCSClient()  # GCS는 나중에 분단위 API 호출 데이터 저장용

    # Spot & Futures Ticker Worker
    spot_worker = BinanceWebsocketWorker(market="spot", redis=redis, gcs=gcs)
    futures_worker = BinanceWebsocketWorker(market="futures", redis=redis, gcs=gcs)

    await asyncio.gather(
        spot_worker.run(),
        futures_worker.run()
    )

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from shared.utils.logger import setup_logger
from client.gcs import GCSClient
from client.redis import RedisClient
from worker.binance_ws import BinanceWebsocketWorker
from worker.binance_rest import BinanceRestWorker


async def main():
    setup_logger("collector")

    redis = RedisClient()
    gcs = GCSClient()

    # WebSocket Workers
    spot_worker = BinanceWebsocketWorker(market="spot", redis=redis, gcs=gcs)
    futures_worker = BinanceWebsocketWorker(market="futures", redis=redis, gcs=gcs)

    # REST Worker
    rest_worker = BinanceRestWorker(gcs=gcs)

    await asyncio.gather(
        spot_worker.run(),
        futures_worker.run(),
        rest_worker.run(),
    )

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from shared.utils.logger import setup_logger
from shared.client.gcs import GCSClient
from shared.client.redis import RedisClient
from shared.worker.redis_to_gcs import RedisToGCSWorker
from worker.binance_ws import BinanceWebsocketWorker
from worker.binance_rest import BinanceRestWorker
from shared.utils.constants import RAW_DATA_TYPES


async def main():
    setup_logger("collector")

    redis = RedisClient()
    gcs = GCSClient()

    spot_ws = BinanceWebsocketWorker(market="spot", redis=redis)
    futures_ws = BinanceWebsocketWorker(market="futures", redis=redis)
    rest = BinanceRestWorker(gcs=gcs)

    spot_gcs = RedisToGCSWorker(
        name="RawToGCS-Spot",
        redis=redis,
        gcs=gcs,
        data_types=RAW_DATA_TYPES,
        redis_key_prefix="queue:spot",
        gcs_path_prefix="raw/spot",
    )
    futures_gcs = RedisToGCSWorker(
        name="RawToGCS-Futures",
        redis=redis,
        gcs=gcs,
        data_types=RAW_DATA_TYPES,
        redis_key_prefix="queue:futures",
        gcs_path_prefix="raw/futures",
    )

    await asyncio.gather(
        spot_ws.run(),
        futures_ws.run(),
        rest.run(),
        spot_gcs.run(),
        futures_gcs.run(),
    )

if __name__ == "__main__":
    asyncio.run(main())

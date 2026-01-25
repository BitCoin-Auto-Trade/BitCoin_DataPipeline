import asyncio
import json
import time
from datetime import datetime
from typing import List
import pandas as pd
from shared.utils.logger import get_logger
from shared.utils.constants import SYMBOL, KST


class RedisToGCSWorker:
    """Redis LIST 데이터를 Parquet으로 변환하여 GCS에 업로드하는 공통 워커"""

    def __init__(
        self,
        name: str,
        redis,
        gcs,
        data_types: List[str],
        redis_key_prefix: str,
        gcs_path_prefix: str,
        interval_seconds: int = 300,
    ):
        self.redis = redis
        self.gcs = gcs
        self.data_types = data_types
        self.redis_key_prefix = redis_key_prefix
        self.gcs_path_prefix = gcs_path_prefix
        self.interval = interval_seconds
        self.logger = get_logger(name)

    async def run(self):
        self.logger.info(f"Started! interval={self.interval}s")
        while True:
            for data_type in self.data_types:
                try:
                    await self._transfer(data_type)
                except Exception as e:
                    self.logger.error(f"[{data_type}] Transfer failed: {e}")
            await asyncio.sleep(self.interval)

    async def _transfer(self, data_type: str):
        key = f"{self.redis_key_prefix}:{data_type}"
        temp_key = f"{key}:processing:{int(time.time())}"

        if self.redis.llen(key) == 0:
            return

        if not self.redis.rename(key, temp_key):
            return

        data_list = self.redis.lrange(temp_key, 0, -1)
        if not data_list:
            self.redis.delete(temp_key)
            return

        records = [json.loads(d) for d in data_list]
        df = pd.DataFrame(records)

        now = datetime.now(KST)
        df["_ingested_at"] = now.isoformat()

        blob_name = (
            f"{self.gcs_path_prefix}/{data_type}/"
            f"year={now.strftime('%Y')}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
            f"{int(time.time())}_{SYMBOL}.parquet"
        )

        self.gcs.upload_parquet(blob_name, df)
        self.logger.info(f"[{data_type}] {len(records)} rows → {blob_name}")

        self.redis.delete(temp_key)

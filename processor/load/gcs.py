import time
from datetime import datetime
import pandas as pd
from shared.utils.constants import KST


class GCSLoader:
    def __init__(self, gcs, symbol):
        self.gcs = gcs
        self.symbol = symbol

    def save(self, data_type, data):
        now = datetime.now(KST)
        record = data.model_dump()
        record["_ingested_at"] = now.isoformat()
        df = pd.DataFrame([record])

        blob_name = (
            f"core/{data_type}/"
            f"year={now.strftime('%Y')}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
            f"{int(time.time())}_{self.symbol}.parquet"
        )
        self.gcs.upload_parquet(blob_name, df)

from datetime import datetime
from shared.utils.constants import KST
from shared.models.raw import RawFundingRate, RawOpenInterest, RawLongShortRatio


class GCSFetcher:
    def __init__(self, gcs, symbol):
        self.gcs = gcs
        self.symbol = symbol

    def _get(self, data_type):
        now = datetime.now(KST)
        prefix = (
            f"raw/futures/{data_type}/"
            f"year={now.strftime('%Y')}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
        )
        df = self.gcs.get_latest_parquet(prefix)
        if df is None or df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_open_interest(self):
        data = self._get("oi")
        return RawOpenInterest(**data) if data else None

    def get_funding_rate(self):
        data = self._get("funding")
        return RawFundingRate(**data) if data else None

    def get_ls_ratio(self):
        data = self._get("lsr")
        return RawLongShortRatio(**data) if data else None

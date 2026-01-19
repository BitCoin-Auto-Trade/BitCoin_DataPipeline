from typing import Optional
from shared.client.gcs import GCSClient
from shared.models.raw import RawFundingRate, RawOpenInterest, RawLongShortRatio


class GCSFetcher:
    """GCS에서 배치 Raw 데이터 조회"""

    def __init__(self, gcs: GCSClient, symbol: str):
        self.gcs = gcs
        self.symbol = symbol

    def _get_prefix(self, data_type: str):
        return f"raw/futures/{data_type}/{self.symbol}/"

    def get_open_interest(self):
        data = self.gcs.get_latest_json(self._get_prefix("oi"))
        return RawOpenInterest(**data) if data else None

    def get_funding_rate(self):
        data = self.gcs.get_latest_json(self._get_prefix("funding"))
        return RawFundingRate(**data) if data else None

    def get_ls_ratio(self):
        data = self.gcs.get_latest_json(self._get_prefix("lsr"))
        return RawLongShortRatio(**data) if data else None

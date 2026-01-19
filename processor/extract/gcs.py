from shared.models.raw import RawFundingRate, RawOpenInterest, RawLongShortRatio


class GCSFetcher:
    def __init__(self, gcs, symbol):
        self.gcs = gcs
        self.symbol = symbol

    def _get(self, data_type):
        prefix = f"raw/futures/{data_type}/{self.symbol}/"
        data = self.gcs.get_latest_json(prefix)
        return data

    def get_open_interest(self):
        data = self._get("oi")
        return RawOpenInterest(**data) if data else None

    def get_funding_rate(self):
        data = self._get("funding")
        return RawFundingRate(**data) if data else None

    def get_ls_ratio(self):
        data = self._get("lsr")
        return RawLongShortRatio(**data) if data else None

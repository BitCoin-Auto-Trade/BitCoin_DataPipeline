from utils import now_ms


class GCSLoader:
    def __init__(self, gcs, symbol):
        self.gcs = gcs
        self.symbol = symbol

    def save(self, data_type, data):
        """core 테이블에 저장"""
        blob_name = f"core/{data_type}/{self.symbol}/{now_ms()}.json"
        self.gcs.upload_json(blob_name, data.model_dump())

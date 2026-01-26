import json
import io
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
from shared.utils.env import GCP_PROJECT_ID, GCS_BUCKET, GCP_CREDENTIALS_PATH


class GCSClient:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            GCP_CREDENTIALS_PATH
        )
        self.client = storage.Client(
            project=GCP_PROJECT_ID, credentials=credentials)
        self.bucket = self.client.bucket(GCS_BUCKET)

    def upload_json(self, blob_name: str, data: dict):
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )

    def download_json(self, blob_name: str):
        blob = self.bucket.blob(blob_name)
        content = blob.download_as_text()
        return json.loads(content)

    def list_blobs(self, prefix: str, max_results: int):
        blobs = self.client.list_blobs(
            self.bucket, prefix=prefix, max_results=max_results)
        return sorted([b.name for b in blobs], reverse=True)

    def get_latest_json(self, prefix: str):
        blobs = self.list_blobs(prefix, max_results=1)
        if not blobs:
            return None
        return self.download_json(blobs[0])

    def upload_parquet(self, blob_name: str, df):
        blob = self.bucket.blob(blob_name)
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine='pyarrow', index=False)
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type='application/octet-stream')

    def download_parquet(self, blob_name: str):
        blob = self.bucket.blob(blob_name)
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        return pd.read_parquet(buffer, engine='pyarrow')

    def get_latest_parquet(self, prefix: str):
        blobs = self.list_blobs(prefix, max_results=1)
        if not blobs:
            return None
        return self.download_parquet(blobs[0])

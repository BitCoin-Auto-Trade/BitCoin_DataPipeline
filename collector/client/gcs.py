import json
from google.cloud import storage
from google.oauth2 import service_account
from shared.utils.env import GCP_PROJECT_ID, GCS_BUCKET, GCP_CREDENTIALS_PATH


class GCSClient:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            GCP_CREDENTIALS_PATH
        )
        self.client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
        self.bucket = self.client.bucket(GCS_BUCKET)

    def upload_json(self, blob_name: str, data: dict):
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        ) 
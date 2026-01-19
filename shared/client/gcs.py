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
        """JSON 데이터를 GCS에 업로드"""
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )

    def download_json(self, blob_name: str):
        """GCS에서 JSON 데이터를 다운로드"""
        blob = self.bucket.blob(blob_name)
        content = blob.download_as_text()
        return json.loads(content)

    def list_blobs(self, prefix: str, max_results: int):
        """특정 prefix로 시작하는 blob 목록 조회 (최신순 정렬)"""
        blobs = self.client.list_blobs(self.bucket, prefix=prefix, max_results=max_results)
        return sorted([b.name for b in blobs], reverse=True)

    def get_latest_json(self, prefix: str):
        """특정 prefix의 가장 최신 JSON 파일 가져오기"""
        blobs = self.list_blobs(prefix, max_results=1)
        if not blobs:
            return None
        return self.download_json(blobs[0])

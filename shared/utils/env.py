import os

# Binance API 설정
BINANCE_APP_ACCESS_KEY = os.getenv('BINANCE_APP_ACCESS_KEY')
BINANCE_APP_SECRET_KEY = os.getenv('BINANCE_APP_SECRET_KEY')

# Redis 설정
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# GCP 설정
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
GCS_BUCKET = os.getenv('GCS_BUCKET')
GCP_CREDENTIALS_PATH = os.getenv(
    'GOOGLE_APPLICATION_CREDENTIALS', '/app/gcp-key.json')

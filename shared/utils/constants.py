from zoneinfo import ZoneInfo

SYMBOL = "btcusdt"
KST = ZoneInfo("Asia/Seoul")

BINANCE_WS_URLS = {
    "spot": "wss://stream.binance.com:9443/ws",
    "futures": "wss://fstream.binance.com/ws",
}

BINANCE_REST_URL = "https://fapi.binance.com"

BINANCE_REST_ENDPOINTS = {
    "open_interest": "/fapi/v1/openInterest",
    "funding_rate": "/fapi/v1/premiumIndex",
    "long_short_ratio": "/futures/data/globalLongShortAccountRatio",
}

RAW_DATA_TYPES = ["kline", "aggtrade", "orderbook", "liquidation"]

CORE_DATA_TYPES = [
    "cvd", "book_imbalance", "spread_analysis",
    "wall_detection", "price_vol_spike", "liq_spike",
]

# intervals
GCS_UPLOAD_INTERVAL = 60

SYMBOL = "btcusdt"

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

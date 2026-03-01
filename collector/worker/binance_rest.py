import asyncio
from datetime import datetime
import aiohttp
import pandas as pd
from shared.utils.logger import get_logger
from shared.utils.constants import SYMBOL, KST, BINANCE_REST_URL, BINANCE_REST_ENDPOINTS
from shared.models.raw import RawOpenInterest, RawFundingRate, RawLongShortRatio


class BinanceRestWorker:
    """Binance REST API Worker"""

    def __init__(self, gcs):
        self.gcs = gcs
        self.logger = get_logger("REST")
        self._lsr_counter = 0

    async def run(self):
        async with aiohttp.ClientSession() as session:
            while True:
                await asyncio.gather(
                    self._fetch_open_interest(session),
                    self._fetch_funding_rate(session),
                    self._fetch_long_short_ratio(session),
                )
                await asyncio.sleep(60)

    async def _fetch(self, session: aiohttp.ClientSession, endpoint: str, extra_params: dict = None):
        url = f"{BINANCE_REST_URL}{endpoint}"
        params = {"symbol": SYMBOL.upper()}
        if extra_params:
            params.update(extra_params)
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                self.logger.error(f"API error: {resp.status}")
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
        return None

    def _save_to_gcs(self, data_type: str, data: dict):
        now = datetime.now(KST)
        data["_ingested_at"] = now.isoformat()
        df = pd.DataFrame([data])

        blob_name = (
            f"raw/futures/{data_type}/"
            f"symbol={SYMBOL}/"
            f"year={now.strftime('%Y')}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
            f"{now.strftime('%H:%M')}.parquet"
        )
        self.gcs.upload_parquet(blob_name, df)

    async def _fetch_open_interest(self, session: aiohttp.ClientSession):
        data = await self._fetch(session, BINANCE_REST_ENDPOINTS["open_interest"])
        if data:
            raw = RawOpenInterest(**data)
            self._save_to_gcs("oi", raw.to_dict())
            self.logger.debug(f"[OI] {raw.open_interest}")

    async def _fetch_funding_rate(self, session: aiohttp.ClientSession):
        data = await self._fetch(session, BINANCE_REST_ENDPOINTS["funding_rate"])
        if data:
            raw = RawFundingRate(**data)
            self._save_to_gcs("funding", raw.to_dict())
            self.logger.debug(f"[FR] {raw.funding_rate}")

    async def _fetch_long_short_ratio(self, session: aiohttp.ClientSession):
        data = await self._fetch(session, BINANCE_REST_ENDPOINTS["long_short_ratio"], {"period": "5m"})
        if data and len(data) > 0:
            raw = RawLongShortRatio(**data[0])
            self._save_to_gcs("lsr", raw.to_dict())
            self.logger.debug(f"[LSR] {raw.long_short_ratio}")

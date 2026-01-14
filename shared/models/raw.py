from pydantic import BaseModel, Field, AliasChoices, ConfigDict
from typing import List, Optional
import json


class BaseRaw(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    def to_dict(self) -> dict:
        return {k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v))
                for k, v in self.model_dump().items()}


class RawTicker(BaseRaw):
    """24hr Ticker (OHLCV)"""
    symbol: str = Field(alias="s")
    open_price: str = Field(alias="o")
    high_price: str = Field(alias="h")
    low_price: str = Field(alias="l")
    last_price: str = Field(alias="c")
    volume: str = Field(alias="v")
    timestamp: int = Field(alias="E")


class RawAggTrade(BaseRaw):
    """집계 체결 (Tick)"""
    symbol: str = Field(alias="s")
    price: str = Field(alias="p")
    quantity: str = Field(alias="q")
    is_buyer_maker: bool = Field(alias="m")
    timestamp: int = Field(alias="E")


class RawOrderBook(BaseRaw):
    """호가창 스냅샷 (L2 Depth)"""
    symbol: Optional[str] = None
    bids: List[List[str]] = Field(alias="b")
    asks: List[List[str]] = Field(alias="a")
    last_update_id: int = Field(alias="u")
    timestamp: int = Field(alias="E")


class RawLiquidation(BaseRaw):
    """강제 청산 (Futures Only)"""
    symbol: str = Field(validation_alias=AliasChoices("s", "o"))
    side: str = Field(validation_alias=AliasChoices("S", "o"))
    price: str = Field(validation_alias=AliasChoices("p", "o"))
    quantity: str = Field(validation_alias=AliasChoices("q", "o"))
    timestamp: int = Field(alias="E")


class RawMarkPrice(BaseRaw):
    """마크 가격 & 펀딩비 (Futures Only)"""
    symbol: str = Field(alias="s")
    mark_price: str = Field(alias="p")
    funding_rate: str = Field(alias="r")
    timestamp: int = Field(alias="E")


class RawOpenInterest(BaseRaw):
    """미체결 약정 (Futures Only)"""
    symbol: str = Field(alias="s")
    open_interest: str = Field(alias="o")
    timestamp: int = Field(alias="E")
import json
from typing import List
from pydantic import BaseModel, Field, ConfigDict


class BaseRaw(BaseModel):
    """Raw 데이터 기본 모델"""
    model_config = ConfigDict(populate_by_name=True)

    def to_dict(self):
        return {
            k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v))
            for k, v in self.model_dump().items()
        }


class RawKline(BaseRaw):
    """OHLCV (kline_1m) - WebSocket 'k' 내부 데이터"""
    symbol: str = Field(alias="s")
    interval: str = Field(alias="i")
    open_price: str = Field(alias="o")
    close_price: str = Field(alias="c")
    high_price: str = Field(alias="h")
    low_price: str = Field(alias="l")
    volume: str = Field(alias="v")
    quote_volume: str = Field(alias="q")
    taker_buy_volume: str = Field(alias="V")
    taker_buy_quote_volume: str = Field(alias="Q")
    num_trades: int = Field(alias="n")
    is_closed: bool = Field(alias="x")
    open_time: int = Field(alias="t")
    close_time: int = Field(alias="T")
    first_trade_id: int = Field(alias="f")
    last_trade_id: int = Field(alias="L")


class RawAggTrade(BaseRaw):
    """집계 체결 (aggTrade)"""
    symbol: str = Field(alias="s")
    agg_trade_id: int = Field(alias="a")
    price: str = Field(alias="p")
    quantity: str = Field(alias="q")
    first_trade_id: int = Field(alias="f")
    last_trade_id: int = Field(alias="l")
    timestamp: int = Field(alias="T")
    is_buyer_maker: bool = Field(alias="m")


class RawOrderBook(BaseRaw):
    """호가창 스냅샷 - Futures depthUpdate"""
    symbol: str = Field(alias="s")
    bids: List[List[str]] = Field(alias="b")
    asks: List[List[str]] = Field(alias="a")
    first_update_id: int = Field(alias="U")
    last_update_id: int = Field(alias="u")
    prev_update_id: int = Field(alias="pu")
    event_time: int = Field(alias="E")
    transaction_time: int = Field(alias="T")


class RawSpotOrderBook(BaseRaw):
    """호가창 스냅샷 - Spot"""
    last_update_id: int = Field(alias="lastUpdateId")
    bids: List[List[str]]
    asks: List[List[str]]


class RawLiquidation(BaseRaw):
    """강제 청산 (forceOrder) - 'o' 내부 데이터"""
    symbol: str = Field(alias="s")
    side: str = Field(alias="S")
    order_type: str = Field(alias="o")
    time_in_force: str = Field(alias="f")
    quantity: str = Field(alias="q")
    price: str = Field(alias="p")
    avg_price: str = Field(alias="ap")
    status: str = Field(alias="X")
    last_filled_qty: str = Field(alias="l")
    filled_qty: str = Field(alias="z")
    timestamp: int = Field(alias="T")


class RawFundingRate(BaseRaw):
    """마크 가격 & 펀딩비 (REST: premiumIndex)"""
    symbol: str = Field(alias="symbol")
    mark_price: str = Field(alias="markPrice")
    index_price: str = Field(alias="indexPrice")
    estimated_settle_price: str = Field(alias="estimatedSettlePrice")
    funding_rate: str = Field(alias="lastFundingRate")
    interest_rate: str = Field(alias="interestRate")
    next_funding_time: int = Field(alias="nextFundingTime")
    timestamp: int = Field(alias="time")


class RawOpenInterest(BaseRaw):
    """미체결 약정 (REST: openInterest)"""
    symbol: str = Field(alias="symbol")
    open_interest: str = Field(alias="openInterest")
    timestamp: int = Field(alias="time")


class RawLongShortRatio(BaseRaw):
    """롱숏 비율 (REST: globalLongShortAccountRatio)"""
    symbol: str = Field(alias="symbol")
    long_short_ratio: str = Field(alias="longShortRatio")
    long_account: str = Field(alias="longAccount")
    short_account: str = Field(alias="shortAccount")
    timestamp: int = Field(alias="timestamp")

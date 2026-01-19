import json
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class BaseProcessed(BaseModel):
    """가공 데이터 기본 모델"""
    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    timestamp: int

    def to_dict(self):
        return {
            k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v))
            for k, v in self.model_dump().items()
        }


class ProcessedCVD(BaseProcessed):
    """CVD (Cumulative Volume Delta) - 소스: AggTrades"""
    interval: str
    cvd: float
    buy_volume: float
    sell_volume: float
    delta: float


class ProcessedBookImbalance(BaseProcessed):
    """Book Imbalance - 소스: Order Book"""
    bid_total: float
    ask_total: float
    imbalance_ratio: float
    signal: str  # BUY_PRESSURE, SELL_PRESSURE, NEUTRAL


class ProcessedSpreadAnalysis(BaseProcessed):
    """Spread Analysis - 소스: Order Book"""
    best_bid: float
    best_ask: float
    spread: float
    spread_percent: float
    liquidity_status: str  # NORMAL, LOW, CRITICAL


class ProcessedWallDetection(BaseProcessed):
    """Wall Detection - 소스: Order Book"""
    bid_walls: List[dict]
    ask_walls: List[dict]
    strongest_support: Optional[float]
    strongest_resistance: Optional[float]


class ProcessedLiqSpike(BaseProcessed):
    """Liquidation Spike - 소스: Liquidations"""
    current_liq_value: float
    avg_liq_value_1h: float
    spike_ratio: float
    long_liq_value: float
    short_liq_value: float
    is_spike: bool
    signal: str  # LONG_SQUEEZE, SHORT_SQUEEZE, NEUTRAL


class ProcessedPriceVolSpike(BaseProcessed):
    """Price/Volume Spike - 소스: OHLCV"""
    price_change_percent: float
    volume: float
    avg_volume: float
    volume_ratio: float
    is_price_spike: bool
    is_volume_spike: bool
    signal: str  # IMPULSE_UP, IMPULSE_DOWN, NORMAL


class ProcessedOITrend(BaseProcessed):
    """OI Trend - 소스: Open Interest"""
    open_interest: float
    oi_change_percent: float
    price_change_percent: float
    trend_signal: str  # HEALTHY_LONG, HEALTHY_SHORT, WEAK_LONG, WEAK_SHORT, NEUTRAL


class ProcessedFRHeatmap(BaseProcessed):
    """FR Heatmap - 소스: Funding Rate"""
    funding_rate: float
    deviation: float
    heat_level: str  # EXTREME_LONG, HIGH_LONG, NORMAL, HIGH_SHORT, EXTREME_SHORT
    squeeze_risk: str  # HIGH, MEDIUM, LOW


class ProcessedLSDivergence(BaseProcessed):
    """LS Divergence - 소스: Long/Short Ratio"""
    long_ratio: float
    short_ratio: float
    ls_ratio: float
    price_change_percent: float
    is_divergence: bool
    divergence_type: Optional[str]  # BEARISH_DIV, BULLISH_DIV
    signal: str  # CONTRARIAN_SHORT, CONTRARIAN_LONG, NEUTRAL

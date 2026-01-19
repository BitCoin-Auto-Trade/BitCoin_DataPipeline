from shared.models.core import (
    ProcessedCVD,
    ProcessedBookImbalance,
    ProcessedSpreadAnalysis,
    ProcessedWallDetection,
    ProcessedLiqSpike,
    ProcessedPriceVolSpike,
)


class RealtimeTransformer:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.symbol = fetcher.symbol

    def _calc_orderbook_volumes(self, ob):
        bid_vols = [float(b[1]) for b in ob.bids]
        ask_vols = [float(a[1]) for a in ob.asks]
        return sum(bid_vols), sum(ask_vols), bid_vols, ask_vols

    def transform_cvd(self, market, prev_cvd=0, interval="1m"):
        """AggTrade -> CVD (Cumulative Volume Delta)"""
        agg = self.fetcher.get_aggtrade(market)
        if not agg:
            return None

        qty = float(agg.quantity)
        is_sell = agg.is_buyer_maker
        delta = -qty if is_sell else qty

        return ProcessedCVD(
            symbol=self.symbol,
            timestamp=agg.timestamp,
            interval=interval,
            cvd=prev_cvd + delta,
            buy_volume=0 if is_sell else qty,
            sell_volume=qty if is_sell else 0,
            delta=delta,
        )

    def transform_book_imbalance(self, market):
        """OrderBook -> 매수/매도 불균형"""
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        bid_total, ask_total, _, _ = self._calc_orderbook_volumes(ob)
        total = bid_total + ask_total
        if total == 0:
            return None

        ratio = (bid_total - ask_total) / total
        if ratio > 0.2:
            signal = "BUY_PRESSURE"
        elif ratio < -0.2:
            signal = "SELL_PRESSURE"
        else:
            signal = "NEUTRAL"

        return ProcessedBookImbalance(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            bid_total=bid_total,
            ask_total=ask_total,
            imbalance_ratio=ratio,
            signal=signal,
        )

    def transform_spread_analysis(self, market):
        """OrderBook -> 스프레드 분석"""
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        best_bid = float(ob.bids[0][0])
        best_ask = float(ob.asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100

        if spread_pct < 0.01:
            status = "NORMAL"
        elif spread_pct < 0.05:
            status = "LOW"
        else:
            status = "CRITICAL"

        return ProcessedSpreadAnalysis(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            spread_percent=spread_pct,
            liquidity_status=status,
        )

    def transform_wall_detection(self, market, threshold=2.0):
        """OrderBook -> 매물벽 탐지"""
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        bid_total, ask_total, bid_vols, ask_vols = self._calc_orderbook_volumes(ob)
        avg_bid = bid_total / len(bid_vols) if bid_vols else 0
        avg_ask = ask_total / len(ask_vols) if ask_vols else 0

        bid_walls = [
            {"price": float(ob.bids[i][0]), "volume": v}
            for i, v in enumerate(bid_vols) if v > avg_bid * threshold
        ]
        ask_walls = [
            {"price": float(ob.asks[i][0]), "volume": v}
            for i, v in enumerate(ask_vols) if v > avg_ask * threshold
        ]

        return ProcessedWallDetection(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            bid_walls=bid_walls,
            ask_walls=ask_walls,
            strongest_support=max((w["price"] for w in bid_walls), default=None),
            strongest_resistance=min((w["price"] for w in ask_walls), default=None),
        )

    def transform_liq_spike(self, market, avg_liq_1h=0):
        """Liquidation -> 청산 스파이크"""
        liq = self.fetcher.get_liquidation(market)
        if not liq:
            return None

        value = float(liq.quantity) * float(liq.price)
        ratio = value / avg_liq_1h if avg_liq_1h > 0 else 0
        is_spike = ratio > 3.0
        is_long = liq.side == "SELL"

        signal = ("LONG_SQUEEZE" if is_long else "SHORT_SQUEEZE") if is_spike else "NEUTRAL"

        return ProcessedLiqSpike(
            symbol=self.symbol,
            timestamp=liq.timestamp,
            current_liq_value=value,
            avg_liq_value_1h=avg_liq_1h,
            spike_ratio=ratio,
            long_liq_value=value if is_long else 0,
            short_liq_value=0 if is_long else value,
            is_spike=is_spike,
            signal=signal,
        )

    def transform_price_vol_spike(self, market, avg_volume=0):
        """Kline -> 가격/거래량 스파이크"""
        kline = self.fetcher.get_kline(market)
        if not kline:
            return None

        open_p = float(kline.open_price)
        close_p = float(kline.close_price)
        vol = float(kline.volume)

        price_chg = ((close_p - open_p) / open_p) * 100
        vol_ratio = vol / avg_volume if avg_volume > 0 else 0
        is_price_spike = abs(price_chg) > 0.5
        is_vol_spike = vol_ratio > 2.0

        if is_price_spike and price_chg > 0:
            signal = "IMPULSE_UP"
        elif is_price_spike and price_chg < 0:
            signal = "IMPULSE_DOWN"
        else:
            signal = "NORMAL"

        return ProcessedPriceVolSpike(
            symbol=self.symbol,
            timestamp=kline.close_time,
            price_change_percent=price_chg,
            volume=vol,
            avg_volume=avg_volume,
            volume_ratio=vol_ratio,
            is_price_spike=is_price_spike,
            is_volume_spike=is_vol_spike,
            signal=signal,
        )

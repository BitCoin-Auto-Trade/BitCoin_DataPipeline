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
        """호가창 잔량 합계 및 리스트 추출"""
        bid_vols = [float(b[1]) for b in ob.bids]
        ask_vols = [float(a[1]) for a in ob.asks]
        return sum(bid_vols), sum(ask_vols), bid_vols, ask_vols

    def transform_cvd(self, market, prev_cvd=0, price_change_pct=0, interval="1m"):
        """
        AggTrade -> CVD (Cumulative Volume Delta) 분석
        로직: 가격 방향과 CVD 방향이 다를 경우 '다이버전스'로 판단 (추세 반전 예고)
        """
        agg = self.fetcher.get_aggtrade(market)
        if not agg:
            return None

        qty = float(agg.quantity)
        is_sell = agg.is_buyer_maker
        delta = -qty if is_sell else qty
        curr_cvd = prev_cvd + delta

        # 시그널 판단 로직 (CVD 다이버전스)
        signal = 0.0
        if price_change_pct > 0.05 and delta < 0:
            signal = -0.7  # BEARISH_DIVERGENCE
        elif price_change_pct < -0.05 and delta > 0:
            signal = 0.7   # BULLISH_DIVERGENCE
        elif abs(price_change_pct) > 0.1 and (price_change_pct * delta > 0):
            signal = 0.5 if delta > 0 else -0.5  # TREND_CONFIRMED

        return ProcessedCVD(
            symbol=self.symbol,
            timestamp=agg.timestamp,
            interval=interval,
            cvd=curr_cvd,
            buy_volume=0 if is_sell else qty,
            sell_volume=qty if is_sell else 0,
            delta=delta,
            signal=signal
        )

    def transform_book_imbalance(self, market):
        """
        OrderBook -> 매수/매도 불균형 분석
        로직: 단순 비율이 아닌 20% 이상의 유의미한 쏠림 현상 포착
        """
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        bid_total, ask_total, _, _ = self._calc_orderbook_volumes(ob)
        total = bid_total + ask_total
        if total == 0:
            return None

        ratio = (bid_total - ask_total) / total

        # 불균형 강도에 따른 시그널 세분화 (-1 to 1)
        if ratio > 0.4:
            signal = 1.0  # STRONG_BUY_IMMINE
        elif ratio > 0.15:
            signal = 0.5  # BUY_PRESSURE
        elif ratio < -0.4:
            signal = -1.0 # STRONG_SELL_IMMINE
        elif ratio < -0.15:
            signal = -0.5 # SELL_PRESSURE
        else:
            signal = 0.0

        return ProcessedBookImbalance(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            bid_total=bid_total,
            ask_total=ask_total,
            imbalance_ratio=ratio,
            signal=signal,
        )

    def transform_spread_analysis(self, market):
        """
        OrderBook -> 스프레드 및 유동성 분석
        로직: 스프레드가 벌어지면 변동성 폭발(Slippage 발생) 전조로 해석
        """
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        best_bid = float(ob.bids[0][0])
        best_ask = float(ob.asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100

        # liquidity_status: 1.0 (Healthy) to 0.0 (Critical)
        if spread_pct <= 0.015:
            status = 1.0  # HEALTHY
        elif spread_pct <= 0.04:
            status = 0.5  # THIN_LIQUIDITY
        else:
            status = 0.0  # HIGH_VOLATILITY_ALERT

        return ProcessedSpreadAnalysis(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            spread_percent=spread_pct,
            liquidity_status=status,
        )

    def transform_wall_detection(self, market, threshold=3.0):
        """
        OrderBook -> 매물벽 탐지
        로직: 전체 평균 대비 n배 이상 크고, 현재가와 1% 이내로 가까운 벽만 '의미 있는 벽'으로 판단
        """
        ob = self.fetcher.get_orderbook(market)
        if not ob:
            return None

        best_price = float(ob.bids[0][0])
        bid_total, ask_total, bid_vols, ask_vols = self._calc_orderbook_volumes(
            ob)
        avg_vol = (bid_total + ask_total) / (len(bid_vols) + len(ask_vols))

        # 현재가 기준 상하방 1% 이내의 벽만 필터링 (가까운 벽이 실질적 저항/지지)
        def is_significant(price, vol):
            dist = abs(price - best_price) / best_price
            return vol > avg_vol * threshold and dist < 0.01

        bid_walls = [
            {"price": float(ob.bids[i][0]), "volume": v,
             "strength": round(v / avg_vol, 1)}
            for i, v in enumerate(bid_vols) if is_significant(float(ob.bids[i][0]), v)
        ]
        ask_walls = [
            {"price": float(ob.asks[i][0]), "volume": v,
             "strength": round(v / avg_vol, 1)}
            for i, v in enumerate(ask_vols) if is_significant(float(ob.asks[i][0]), v)
        ]

        return ProcessedWallDetection(
            symbol=self.symbol,
            timestamp=self.fetcher.get_timestamp(ob, market),
            bid_walls=bid_walls,
            ask_walls=ask_walls,
            strongest_support=max((w["price"]
                                  for w in bid_walls), default=None),
            strongest_resistance=min((w["price"]
                                     for w in ask_walls), default=None),
        )

    def transform_liq_spike(self, market, avg_liq_1h=10000):
        """
        Liquidation -> 청산 스파이크 분석
        로직: 대량 청산은 추세의 끝(Extremum)일 확률이 높음. '반대 방향' 시그널 생성.
        """
        liq = self.fetcher.get_liquidation(market)
        if not liq:
            return None

        value = float(liq.quantity) * float(liq.price)
        ratio = value / avg_liq_1h if avg_liq_1h > 0 else 0
        is_spike = ratio > 5.0  # 5배 이상 터졌을 때 유의미한 스파이크
        is_long_liq = liq.side == "SELL"  # 롱 포지션이 강제 매도됨

        # 시그널: 1.0 (Bullish reversal from long liq) to -1.0 (Bearish reversal from short liq)
        if is_spike:
            signal = 1.0 if is_long_liq else -1.0
        else:
            signal = 0.0

        return ProcessedLiqSpike(
            symbol=self.symbol,
            timestamp=liq.timestamp,
            current_liq_value=value,
            avg_liq_value_1h=avg_liq_1h,
            spike_ratio=ratio,
            long_liq_value=value if is_long_liq else 0,
            short_liq_value=0 if is_long_liq else value,
            is_spike=is_spike,
            signal=signal,
        )

    def transform_price_vol_spike(self, market, avg_volume=0, vol_std_dev=0):
        """
        Kline -> 가격/거래량 스파이크 (Vol-Price Action)
        로직: 거래량이 실린 가격 변화는 '돌파(Breakout)' 혹은 '절정(Climax)'으로 판단
        """
        kline = self.fetcher.get_kline(market)
        if not kline:
            return None

        open_p = float(kline.open_price)
        close_p = float(kline.close_price)
        vol = float(kline.volume)

        price_chg = ((close_p - open_p) / open_p) * 100
        vol_ratio = vol / avg_volume if avg_volume > 0 else 0

        # 거래량 2.5배 이상 & 가격 0.5% 이상 변화 시 스파이크
        is_vol_spike = vol_ratio > 2.5
        is_price_spike = abs(price_chg) > 0.4

        if is_vol_spike and is_price_spike:
            signal = 1.0 if price_chg > 0 else -1.0  # VOL_DRIVEN_BREAKOUT / DUMP
        elif not is_vol_spike and is_price_spike:
            signal = 0.3 if price_chg > 0 else -0.3   # LOW_VOL_FAKE_MOVE
        elif is_vol_spike and not is_price_spike:
            signal = 0.1                            # ABSORPTION (Indecision)
        else:
            signal = 0.0

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

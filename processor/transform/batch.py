from shared.models.core import ProcessedOITrend, ProcessedFRHeatmap, ProcessedLSDivergence


class BatchTransformer:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.symbol = fetcher.symbol

    def transform_oi_trend(self, prev_oi=0, price_change_pct=0):
        """
        Open Interest -> OI 트렌드 분석
        의도: 가격 변화와 OI 변화를 결합하여 현재 상승/하락이 '신규 자금 유입'인지 '기존 포지션 손절'인지 판별
        """
        oi_data = self.fetcher.get_open_interest()
        if not oi_data:
            return None

        curr_oi = float(oi_data.open_interest)
        oi_chg = ((curr_oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0

        # 시그널 로직 고도화 (전문 트레이딩 관점)
        # 1. 상승 + OI 상승: 신규 롱 진입 (추세 강화 - 매우 긍정)
        if price_change_pct > 0.5 and oi_chg > 1.0:
            signal = "ACCUMULATION_LONG"
        # 2. 하락 + OI 상승: 신규 숏 진입 (추세 하락 강화 - 매우 부정)
        elif price_change_pct < -0.5 and oi_chg > 1.0:
            signal = "AGGRESSIVE_SHORTING"
        # 3. 상승 + OI 하락: 숏 포지션의 강제 청산/손절로 인한 상승 (추세 반전 가능성)
        elif price_change_pct > 0.5 and oi_chg < -1.0:
            signal = "SHORT_COVERING_RALLY"
        # 4. 하락 + OI 하락: 롱 포지션의 항복/손절 (바닥 근접 가능성)
        elif price_change_pct < -0.5 and oi_chg < -1.0:
            signal = "LONG_LIQUIDATION_DUMP"
        else:
            signal = "NEUTRAL"

        return ProcessedOITrend(
            symbol=self.symbol,
            timestamp=oi_data.timestamp,
            open_interest=curr_oi,
            oi_change_percent=oi_chg,
            price_change_percent=price_change_pct,
            trend_signal=signal,
        )

    def transform_fr_heatmap(self):
        """
        Funding Rate -> 히트맵 및 스퀴즈 위험 분석
        의도: 펀딩비가 극단적으로 높거나 낮으면 반대 방향으로의 '스퀴즈(가격 급변동)' 위험이 커짐
        """
        fr_data = self.fetcher.get_funding_rate()
        if not fr_data:
            return None

        rate = float(fr_data.funding_rate)
        # 비트코인 기본 펀딩비는 0.01%(0.0001)임. 이보다 높으면 롱 과열, 낮으면 숏 과열.
        deviation = rate - 0.0001

        # 8시간마다 결제되는 펀딩비 특성상 0.05% 이상은 매우 극단적인 상태
        if rate >= 0.05:  # 0.05%
            heat, risk = "LONG_OVERHEATED", "CRITICAL"
        elif rate >= 0.02:
            heat, risk = "LONG_CROWDED", "HIGH"
        elif rate <= -0.05:
            heat, risk = "SHORT_OVERHEATED", "CRITICAL"
        elif rate <= -0.02:
            heat, risk = "SHORT_CROWDED", "HIGH"
        elif abs(rate) < 0.01:
            heat, risk = "STABLE", "LOW"
        else:
            heat, risk = "NORMAL", "MEDIUM"

        return ProcessedFRHeatmap(
            symbol=self.symbol,
            timestamp=fr_data.timestamp,
            funding_rate=rate,
            deviation=deviation,
            heat_level=heat,
            squeeze_risk=risk,
        )

    def transform_ls_divergence(self, price_change_pct=0):
        """
        Long/Short Ratio -> 다이버전스(역발상) 분석
        의도: 개미들(Retail)이 한쪽으로 몰릴 때 가격이 반대로 가는 '유동성 확보(Liquidity Grab)' 현상 포착
        """
        ls_data = self.fetcher.get_ls_ratio()
        if not ls_data:
            return None

        long_r = float(ls_data.long_account)
        short_r = float(ls_data.short_account)
        ls_ratio = float(ls_data.long_short_ratio)

        is_div, div_type, signal = False, None, "NEUTRAL"

        # 1. 강세 다이버전스 (Bullish Reversal)
        # 가격은 급락하는데, 개미들은 겁먹고 숏을 늘림 (LS Ratio 하락) -> 세력의 매집 시점
        if price_change_pct < -2.0 and ls_ratio < 0.8:
            is_div, div_type, signal = True, "BULLISH_CONTRARIAN", "STRONG_BUY_SIGNAL"

        # 2. 약세 다이버전스 (Bearish Reversal)
        # 가격은 오르는데, 개미들이 환희에 차서 롱을 늘림 (LS Ratio 급상승) -> 세력의 매도 시점
        elif price_change_pct > 2.0 and ls_ratio > 1.5:
            is_div, div_type, signal = True, "BEARISH_CONTRARIAN", "STRONG_SELL_SIGNAL"

        # 3. 롱 트랩 (Long Trap)
        # 가격은 횡보하거나 소폭 하락하는데 롱 비율만 계속 높아짐 -> 개미들만 타 있는 배 (무거움)
        elif abs(price_change_pct) < 0.5 and ls_ratio > 1.3:
            is_div, div_type, signal = True, "LONG_TRAP", "WARNING_EXIT_LONG"

        return ProcessedLSDivergence(
            symbol=self.symbol,
            timestamp=ls_data.timestamp,
            long_ratio=long_r,
            short_ratio=short_r,
            ls_ratio=ls_ratio,
            price_change_percent=price_change_pct,
            is_divergence=is_div,
            divergence_type=div_type,
            signal=signal,
        )

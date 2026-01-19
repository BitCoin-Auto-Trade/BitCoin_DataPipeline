from shared.models.core import ProcessedOITrend, ProcessedFRHeatmap, ProcessedLSDivergence


class BatchTransformer:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.symbol = fetcher.symbol

    def transform_oi_trend(self, prev_oi=0, price_change_pct=0):
        """Open Interest -> OI 트렌드 분석"""
        oi = self.fetcher.get_open_interest()
        if not oi:
            return None

        curr_oi = float(oi.open_interest)
        oi_chg = ((curr_oi - prev_oi) / prev_oi * 100) if prev_oi > 0 else 0

        # 가격과 OI 변화 조합으로 시그널 결정
        if price_change_pct > 0.5 and oi_chg > 1.0:
            signal = "HEALTHY_LONG"
        elif price_change_pct < -0.5 and oi_chg > 1.0:
            signal = "HEALTHY_SHORT"
        elif price_change_pct > 0.5 and oi_chg < -1.0:
            signal = "WEAK_LONG"
        elif price_change_pct < -0.5 and oi_chg < -1.0:
            signal = "WEAK_SHORT"
        else:
            signal = "NEUTRAL"

        return ProcessedOITrend(
            symbol=self.symbol,
            timestamp=oi.timestamp,
            open_interest=curr_oi,
            oi_change_percent=oi_chg,
            price_change_percent=price_change_pct,
            trend_signal=signal,
        )

    def transform_fr_heatmap(self):
        """Funding Rate -> 히트맵"""
        fr = self.fetcher.get_funding_rate()
        if not fr:
            return None

        rate = float(fr.funding_rate)
        deviation = rate - 0.0001  # 기준 펀딩비(0.01%)와의 편차

        if rate >= 0.0005:
            heat, risk = "EXTREME_LONG", "HIGH"
        elif rate >= 0.0002:
            heat, risk = "HIGH_LONG", "MEDIUM"
        elif rate <= -0.0005:
            heat, risk = "EXTREME_SHORT", "HIGH"
        elif rate <= -0.0002:
            heat, risk = "HIGH_SHORT", "MEDIUM"
        else:
            heat, risk = "NORMAL", "LOW"

        return ProcessedFRHeatmap(
            symbol=self.symbol,
            timestamp=fr.timestamp,
            funding_rate=rate,
            deviation=deviation,
            heat_level=heat,
            squeeze_risk=risk,
        )

    def transform_ls_divergence(self, price_change_pct=0):
        """Long/Short Ratio -> 다이버전스 분석"""
        ls = self.fetcher.get_ls_ratio()
        if not ls:
            return None

        long_r = float(ls.long_account)
        short_r = float(ls.short_account)
        ls_r = float(ls.long_short_ratio)

        is_div, div_type, signal = False, None, "NEUTRAL"

        # 가격 하락 + 롱 비율 높음 = 강세 다이버전스
        if price_change_pct < -1.0 and ls_r > 1.2:
            is_div, div_type, signal = True, "BULLISH_DIV", "CONTRARIAN_LONG"
        # 가격 상승 + 숏 비율 높음 = 약세 다이버전스
        elif price_change_pct > 1.0 and ls_r < 0.8:
            is_div, div_type, signal = True, "BEARISH_DIV", "CONTRARIAN_SHORT"

        return ProcessedLSDivergence(
            symbol=self.symbol,
            timestamp=ls.timestamp,
            long_ratio=long_r,
            short_ratio=short_r,
            ls_ratio=ls_r,
            price_change_percent=price_change_pct,
            is_divergence=is_div,
            divergence_type=div_type,
            signal=signal,
        )

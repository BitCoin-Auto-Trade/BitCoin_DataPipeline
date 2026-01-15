## 비트코인 데이터 파이프라인


## 데이터 정리

1. 기본 시장 데이터
- 가장 기본이 되지만, '틱(Tick)' 단위의 세밀함이 필요합니다.
- OHLCV: 시가, 고가, 저가, 종가, 거래량.
- Aggregated Trades: 개별 체결 데이터. (시장가 매수인지 매도인지 구분된 데이터)
- CVD: 누적 볼륨 델타. 시장가 매수 합계와 매도 합계의 차이. (에너지의 방향 확인)

2. 호가창 데이터
- 가격이 움직이기 전의 '전조 현상'을 포착합니다.
- Order Book Depth (L2): 상위 20~50호가의 가격과 잔량.
- Order Book Imbalance: 매수 거미줄과 매도 거미줄의 두께 차이.
- Spread: 최우선 매수/매도 호가 간격. (유동성 부족으로 인한 급변동 감지)
- Wall Detection: 특정 가격대에 유독 몰려 있는 대형 주문(세력 벽)의 위치.

3. 선물 시장 특화 데이터
선물 시장에만 존재하는 '강제 청산'과 '비용' 관련 데이터입니다. (가장 중요)
- Open Interest (미체결 약정): 현재 시장에 열려 있는 포지션 총량. (추세의 지속성 판단)
- Funding Rate (펀딩비): 롱/숏 중 어느 쪽이 과열되었는지 확인.
- Liquidations (실시간 청산액): 롱 청산 vs 숏 청산 규모. (반대 방향으로의 급등락/스퀴즈 포착용)
- Long/Short Ratio: 거래소 내 개인/기관들의 포지션 비율.

4. 온체인 및 거매크로 데이터
- 비트코인의 특수성과 글로벌 경제 상황을 반영합니다.
- Whale Alert: 거래소로 대량 입금(매도 압력) 또는 지갑으로 출금(보유 의지).
- DXY (달러 인덱스) & 나스닥 선물: 비트코인과 커플링/디커플링 확인을 위해 1분 단위 수집.
- Tether Dominance (USDT.D): 시장 참여자들이 코인을 샀는지 현금화했는지 보여주는 지표.
- Fear & Greed Index: 시장의 과열/공포 수치.

5. 실시간 뉴스 및 감성 데이터
- Vertex AI(Gemini)를 활용해 수치화할 데이터입니다.
- CryptoPanic API: 전 세계 코인 뉴스 헤드라인 및 본문.
- 특정 트위터(X) 계정 피드: 일론 머스크, 파월 의장, 주요 거래소 공지 등.
- Sentiment Score: 뉴스를 Gemini에게 던져서 나온 -1 ~ 1 사이의 점수.


## 아키텍처 정리

### 클라우드 환경
- BigQuery : 모델 학습을 위한 DB 
- GCS : 저지연 데이터 분석을 위한 DB
- Vertex : Gemini를 활용한 AI 모델 학습 플랫폼
- GCP Compute Engine : 데이터 파이프라인 띄어둘 서버

### 데이터 피드
- BINANCE
- 인스타 or X SNS



## DB 흐름도
```
raw -> Redis
    -> GCS -> BigQuery
```

## 데이터

### 1. Raw 데이터 수집

| 카테고리 | 데이터 항목 | 수집처 (API/Stream) | 방식 | 주기/빈도 |
|----------|------------|---------------------|------|-----------|
| 기본 시장 | OHLCV (Klines) | Binance WS: btcusdt@kline_1m | WS | 실시간 (1분마다 확정) |
| 기본 시장 | Aggregated Trades | Binance WS: btcusdt@aggTrade | WS | 실시간 (체결 시) |
| 호가창 | Order Book (L2) | Binance WS: depth20@100ms | WS | 100ms 단위 |
| 선물 | Liquidations | Binance WS: !forceOrder@arr | WS | 실시간 (발생 시) |
| 선물 | Open Interest | Binance REST: /fapi/v1/openInterest | REST | 1분 단위 |
| 선물 | Funding Rate | Binance REST: /fapi/v1/premiumIndex | REST | 1분 단위 |
| 선물 | Long/Short Ratio | Binance REST: globalLongShortAccountRatio | REST | 5분 단위 |
| 온체인 | Whale Alert | Whale-Alert.io API | REST | 실시간 (Webhook/Polling) |
| 거시/도미 | USDT.D / BTC.D | CoinMarketCap API 또는 TradingView | REST | 1분~5분 단위 |
| 거시 | DXY / Nasdaq | Yahoo Finance API | REST | 1분 단위 |
| 거시 | Fear & Greed | Alternative.me API | REST | 1일 1회 |
| 뉴스 | News/Tweets | CryptoPanic API / Twitter API | REST | 1분~5분 |

### 2. 실시간 가공 지표 (High Frequency)

스캘핑/데이트레이딩 시그널로 사용되는 즉각적 매매 대응 지표입니다.

| 가공 데이터 | 소스 Raw 데이터 | 가공 로직 | 용도 |
|------------|----------------|----------|------|
| CVD (1m/5m) | AggTrades | (시장가 매수량 - 매도량)의 실시간 누적합 | 매수/매도 세력의 실질적 우위 확인 |
| Book Imbalance | Order Book | (매수 총 잔량 / 매도 총 잔량) 비율 | 단기 가격 밀어올리기/누르기 포착 |
| Spread Analysis | Order Book | 최상단 매도/매수 가격 차이 및 호가 갭 | 유동성 부족 시 급변동 경보 |
| Wall Detection | Order Book | 평균 호가 대비 5~10배 이상의 '벽' 탐지 | 강력한 지지/저항 및 벽 깨기(Break) 포착 |
| Liq. Spike | Liquidations | 최근 1시간 평균 대비 청산액이 300% 이상 급증 시 | 역추세 돌파(Squeeze) 및 반등 지점 포착 |
| Price/Vol Spike | OHLCV | 전봉 대비 거래량/가격 변동폭 급증 여부 | 변동성 확대 시작점(Impulse Move) 감지 |

### 3. 중장기/매크로 가공 지표 (Low Frequency)

시장의 전체적인 온도와 돈의 흐름을 분석하는 추세 및 환경 분석 지표입니다.

| 가공 데이터 | 소스 Raw 데이터 | 가공 로직 | 용도 |
|------------|----------------|----------|------|
| Sentiment Score | News/Tweets | Gemini AI가 텍스트를 -1 ~ 1 사이 점수로 환산 | 뉴스 호재/악재의 수치화 및 필터링 |
| OI Trend Analysis | Open Interest | 가격 상승+OI 상승=건강한 매수 / 가격 하락+OI 상승=강한 매도 압력 | 현재 추세의 진정성(지속성) 판단 |
| FR Heatmap | Funding Rate | 0.01%(기본) 대비 이격도 분석 (예: > 0.05%면 과열) | 롱/숏 포지션 과열 및 반대 방향 스퀴즈 대비 |
| LS Divergence | Long/Short Ratio | 개미(Long)가 늘어나는데 가격이 하락하는지 체크 | '개미 반대로 가기' 전략 (역발상 지표) |
| Whale Inflow | Whale Alert | 거래소로 입금되는 대량 알림 합계 | 잠재적 대량 매도 압력(Dump) 사전 감지 |
| Tether Dominance | USDT.D | BTC 가격과 USDT.D의 음의 상관관계 분석 | 시장 참여자들의 현금화 vs 코인 매수 의지 확인 |
| Greed Alignment | Fear & Greed | 공포/탐욕 지수와 현재 가격의 과매수/과매도 비교 | 시장의 극단적 감정 상태에서 반전 기회 포착 |
| DXY Correlation | DXY, BTC Price | 최근 24시간 DXY와의 피어슨 상관계수 | 매크로(달러) 환경의 영향력 강도 파악 |

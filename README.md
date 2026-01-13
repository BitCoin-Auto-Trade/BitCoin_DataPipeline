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

### 1. Redis 설계 (실시간 메모리 데이터)

| 구분 | 데이터 항목 | Key/Table Name | 데이터 구조 | 설명 |
|------|------------|----------------|------------|------|
| **기본 시장 데이터** | OHLCV | `ticker:{symbol}` | Hash | 실시간 시가, 고가, 저가, 종가, 거래량 (현재 진행 중인 캔들) |
| | Aggregated Trades | `trades:{symbol}` | Stream | 틱 단위 체결 데이터 (시장가 매수/매도 구분) |
| | CVD | `cvd:{symbol}` | String/Float | 누적 볼륨 델타 (시장가 매수량 - 매도량, 에너지 방향 확인) |
| **호가창 데이터** | Order Book (L2) | `orderbook:{symbol}` | Sorted Set | 실시간 상위 20~50호가의 가격과 잔량 |
| | Spread | `orderbook:spread:{symbol}` | String/Float | 최우선 매수/매도 호가 간격 (유동성 부족 감지) |
| | Imbalance & Wall | `ob_metrics:{symbol}` | Hash | 매수/매도 거미줄 두께 차이, 대형 주문(세력 벽) 위치 |
| **선물 시장 데이터** | Open Interest | `futures:oi:{symbol}` | String/Float | 미체결 약정 총량 (추세의 지속성 판단) |
| | Funding Rate | `futures:funding:{symbol}` | String/Float | 롱/숏 과열도 측정 펀딩비 |
| | Liquidations | `futures:liq:{symbol}` | Hash | 실시간 롱/숏 청산액 (스퀴즈 포착용) |
| | Long/Short Ratio | `futures:ratio:{symbol}` | String/Float | 거래소 내 개인/기관 포지션 비율 |
| **거시경제 데이터** | DXY & 나스닥 | `macro:dxy` / `macro:nasdaq` | Hash | 달러 인덱스 & 나스닥 선물 1분 단위 시세 |
| | USDT Dominance | `macro:usdt_d` | String/Float | 테더 도미넌스 (현금화 여부 지표) |
| | Fear & Greed | `macro:fear_greed` | String/Float | 시장 과열/공포 수치 |
| **온체인 데이터** | Whale Alert | `whale:latest` | Stream | 최근 대량 거래소 입출금 트랜잭션 |
| **뉴스/감성 데이터** | Sentiment Score | `sentiment:latest` | String/Float | Gemini 분석 최근 5분 평균 감성 점수 (-1 ~ 1) |
| | News Feed | `news:feed` | Stream | CryptoPanic API & 주요 트위터(X) 피드 실시간 수집 |

### 2. BigQuery 설계 (역사적 분석용 데이터)

| 구분 | 데이터 항목 | Table Name | 파티션/클러스터 | 상세 설명 |
|------|------------|-----------|----------------|----------|
| **기본 시장 데이터** | OHLCV | `hist_ohlcv` | timestamp (Day) | 1분/1시간 단위 과거 시세 데이터 (백테스팅용) |
| | Aggregated Trades | `hist_trades_raw` | symbol, timestamp | 틱 단위 체결 로그 (CVD 계산 및 복기 분석용) |
| **호가창 데이터** | Order Book Snapshot | `hist_orderbook_snapshot` | timestamp (Hour) | 1초~10초 단위 호가창 스냅샷 (벽 감지 패턴 분석) |
| | Imbalance History | `hist_ob_imbalance` | timestamp (Day) | 호가 불균형 이력 (급등락 전조 현상 학습) |
| **선물 시장 데이터** | OI & Funding & Liq | `hist_futures_metrics` | timestamp (Day) | 미체결약정, 펀딩비, 청산 이력 시간대별 기록 |
| | Long/Short Ratio | `hist_long_short_ratio` | timestamp (Day) | 포지션 비율 변화 추이 (포지션 쏠림 분석) |
| **거시경제 데이터** | Macro Indicators | `hist_macro_indicators` | timestamp (Month) | DXY, 나스닥, USDT.D, Fear & Greed 히스토리 |
| **온체인 데이터** | Whale Alerts | `hist_whale_alerts` | timestamp | 거래소 입출금 대량 트랜잭션 기록 (매도 압력/보유 의지 분석) |
| **뉴스/감성 데이터** | News & Sentiment | `hist_news_sentiment` | timestamp (Day) | CryptoPanic, 트위터 피드, Gemini 감성 점수 이력 |

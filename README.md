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

| 구분 | 데이터 항목 | Redis Key (네이밍 규칙) | 데이터 구조 | 설명 및 선정 이유 |
|------|------------|-------------------------|------------|------------------|
| **기본 시장** | Aggregated Trades | `raw:trades:{symbol}` | Stream | 필수. 모든 틱을 순서대로 저장. Processor가 읽어서 CVD 계산. |
| | OHLCV (현재) | `state:ticker:{market}:{symbol}` | Hash | 현재 진행 중인 캔들 데이터 (시/고/저/종/거). |
| | CVD (실시간) | `proc:metrics:{symbol}` | Hash | (필드: cvd) 여러 지표와 함께 Hash에 넣어 한 번에 조회. |
| **호가창** | Order Book (L2) | `raw:orderbook:{symbol}` | Hash (JSON) | ZSET보다 JSON 직렬화가 대역폭 효율 및 복구 속도가 빠름 (상위 50호가). |
| | OB Metrics | `proc:metrics:{symbol}` | Hash | (필드: spread, imbalance, wall_price, wall_size) 가공된 모든 호가 지표. |
| **선물 특화** | Liquidations | `raw:liq:{symbol}` | Stream | 중요. 청산은 '사건'이므로 Stream으로 쌓아서 빈도/규모 측정. |
| | Futures Info | `state:futures:{symbol}` | Hash | OI(미체결), 펀딩비, L/S Ratio 통합 관리. (REST API 주기적 갱신) |
| **거시/온체인** | Whale Alert | `raw:whale` | Stream | 대량 입출금 알림. 발생 시각과 규모 저장. |
| | Macro Indicators | `state:macro` | Hash | DXY, 나스닥, USDT.D를 한 키에 통합하여 네트워크 오버헤드 감소. |
| | Fear & Greed | `state:sentiment:fng` | String | 일 단위 데이터이므로 가장 단순하게 저장. |
| **뉴스/감성** | News Feed | `raw:news` | Stream | 뉴스 본문, 출처, 원문 수집용. |
| | Sentiment Score | `proc:sentiment` | Hash | (필드: latest_score, ma_5m_score) Gemini가 분석한 점수. |


### 2. BigQuery 설계 (역사적 분석용 데이터)

| 구분 | 테이블명 (Table Name) | 파티션 (Partition) | 클러스터 (Cluster) | 주요 컬럼 및 분석 용도 |
|------|----------------------|-------------------|--------------------|----------------------|
| **시장** | `market_ohlcv` | timestamp (Day) | symbol, interval | 1m, 1h 단위 시세. 전략의 기본 수익률 계산용. |
| | `market_trades_raw` | timestamp (Day) | symbol | 가장 대용량. 틱 단위 체결 데이터. CVD 복기 및 체결 강도 분석용. |
| **호가** | `market_orderbook_snapshot` | timestamp (Day) | symbol | 1~10초 단위 스냅샷 + Imbalance, Spread 포함. 호가창 벽 붕괴 패턴 분석. |
| **선물** | `futures_metrics_history` | timestamp (Day) | symbol | OI, 펀딩비, L/S Ratio 통합. 상관관계 분석을 위해 한 테이블에 적재. |
| **사건** | `futures_liquidations` | timestamp (Day) | symbol | 청산 데이터 전용. 급등락(Squeeze) 시점의 청산 규모 분석용. |
| **거시** | `macro_onchain_history` | timestamp (Month) | indicator_name | DXY, 나스닥, USDT.D, Whale Alert 통합. 지표별 비트코인 커플링 지수 계산. |
| **감성** | `news_sentiment_history` | timestamp (Day) | source | 뉴스 원문 + Gemini 점수. 호재/악재 점수와 가격 변동의 상관관계 분석. |
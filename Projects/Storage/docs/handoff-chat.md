# storage 인수인계 (Claude 일반 채팅용)

> 이 문서를 새 채팅의 첫 메시지로 붙여 넣는다. 2026-11-03 기준. 전체 작업 기록은 `docs/session-2026-11-03.md`.
> 채팅의 Claude 는 **MotherDuck 커넥터**로 데이터를 조회한다. PC 는 꺼져 있어도 된다.

## 0. 채팅 Claude 에게 부탁

- MotherDuck 의 **`storage` 데이터베이스만 조회**한다. **데이터를 바꾸거나 지우지 않는다.**
  - `query_rw` 같은 쓰기 도구는 쓰지 않는다.
  - 같은 계정의 `stocks` DB(예전 매매일지·메모)는 건드리지 않는다.
- KRX 정보데이터시스템(data.krx.co.kr)을 자동으로 대량 조회하지 않는다. 약관 위반으로 IP 가 차단된 적이 있다. KRX 데이터는 공식 Open API 로만 받는다.
- 숫자로 말한다. 성공 사례만 보지 말고, 같은 조건 전체(실패 포함)와 비교한다. 기준 대비 몇 배(lift)인지로 말한다.
- 답은 한국어로, 쉽게 풀어서 한다.

## 1. 프로젝트

- 키움 REST API 로 국내 주식(코스피·코스닥 보통주·우선주 2,673종목)의 일봉·분봉을 모아 PC 의 DuckDB 에 쌓는다.
- 목적: 데이터를 모아 두는 것. (전략·시뮬레이션 내용은 2026-11-03 에 이 문서에서 지웠다.)
- 매일 운영:
  - 평일 20:20 BIOS 가 PC 를 켠다.
  - 20:30 수집한다.
  - 수집이 끝나면 MotherDuck 에 업로드하고, 월말이면 G 드라이브로 백업하고, 텔레그램으로 알린 뒤 PC 를 끈다.
  - 주말에는 20:40 에 PC 를 끈다.
- 코드: GitHub `woong2399/storage` (비공개). 자세한 내용은 `docs/data-collection.md`, `docs/session-2026-11-03.md`.

## 2. MotherDuck `storage` 데이터 (분봉 제외)

| 테이블 | 내용 |
|---|---|
| `daily` | code, date, open, high, low, close, volume = **정규장 수정주가**. raw_close = 정규장 **원주가** 종가. amount = KRX 일봉 거래대금(**백만 원**) |
| `stocks` | code, name, market(KOSPI/KOSDAQ), kind(보통주/우선주), foreign, nxt, first_seen, last_seen, delisted |
| `kiwoom_mktcap` | code, date, kiwoom_list_shrs(상장주식수), kiwoom_close(정규장 종가), kiwoom_mktcap(원). **2026-11-02부터** 매일 쌓인다. 그날 거래가 없던 종목은 시가총액이 비어 있다 |
| `krx_daily` | KRX 시가총액·거래대금용. **아직 비어 있음** (KRX Open API 키 신청 예정) |

- `daily` 는 약 1,237만 행이고, 1985-01 부터 마지막 수집일까지 있다.
- 평일 저녁 수집이 끝나면 그날 것까지 올라온다.

**데이터 주의**
- **거래대금(amount)**
  - 대략 2000년대 초까지는 키움 환산 때문에 단위가 맞지 않는다. 쓰려면 **2005년 이후만** 쓴다.
  - 2026-09-14부터 KRX 에 애프터마켓(16:00~20:00)이 생겼다. 그래서 amount 에는 애프터마켓과 시간외 거래가 섞인다. 가격(daily 의 OHLC)은 정규장만이다.
- **과거 시가총액은 없다.** "거래대금 ÷ 시가총액"은 아직 계산할 수 없다.
- **상장폐지 종목이 없다.** 생존 편향이 있어서 결과가 실제보다 좋게 나온다.
- **2015-06-15 전에는 가격제한폭이 ±15%였다.** 그래서 아래 조건 캔들(고가 ≥ 전일 종가 ×1.15)이 거의 나오지 않는다. 분석은 2015-06 이후로 보는 게 맞다.
- **보정한 오류:** 키움 일봉 중 환산이 빠진 47건(2001-03-23, 2001-07-03 등)은 이미 고쳐 두었다.
- **남은 이상치**
  - 9종목은 1997~2004년 일부 9거래일의 수정주가가 다른 출처와 10배 다르다: 000040·001260·003060·004870·012170·025620·030350·032860·060900
  - 그 밖에 대한방직 1987-07-21, 한국알콜 1996-09-18, HLB 2002-04-01, SM Life Design(063440) 2001-11-28.

## 6. 조회 예시 (MotherDuck SQL)

```sql
-- 최근 20일 일봉
SELECT d.date, d.open, d.high, d.low, d.close, d.volume, d.amount
FROM storage.main.daily d JOIN storage.main.stocks s USING (code)
WHERE s.name = '삼성전자' ORDER BY d.date DESC LIMIT 20;
```

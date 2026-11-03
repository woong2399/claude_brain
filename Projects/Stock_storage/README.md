---
project: Stock_storage
repo: woong2399/woong_stock (비공개)
updated: 2026-11-03
---
# Stock_storage (주식 수집, 저장소 이름: woong_stock)

## 한 줄 설명
키움 REST API 로 코스피·코스닥 2,673종목의 일봉·분봉을 모아 DuckDB 에 쌓는 프로젝트. (시뮬레이션·매수 근거 연구 기록은 2026-11-03 에 이 폴더에서 지웠다. 필요하면 git 기록에서 되살린다.)

## 현재 상태 (2026-11-03)
- **자동 운영 중:** 평일 20:20 BIOS 켜짐 → 20:30 수집 → MotherDuck 업로드 → 월말 G 드라이브 백업 → 텔레그램 알림 → PC 종료. 주말 20:40 종료.
- **클라우드:** MotherDuck `woong_stock` DB (daily 약 1,237만 행, stocks, kiwoom_mktcap(11-02부터), krx_daily(비어 있음)).

## 다음 할 일
1. KRX Open API 키 신청(사용자) → `krx_daily` 채우기 (시가총액 확보)
2. 상장폐지 종목 확보 방법 (생존 편향)
3. 11-30 첫 월말 백업 확인

## 꼭 지킬 것
- KRX 정보데이터시스템 자동 대량 조회 금지 (IP 차단 이력). 공식 Open API 만.
- MotherDuck 은 조회만. 같은 계정 `stocks` DB(매매일지)는 건드리지 않는다.
- 거래대금은 2005년 이후만, 분석은 2015-06 이후 (가격제한폭 ±15% 시절 제외).

## 이 폴더 안
- `docs/` — 상세 문서 사본 (원본: woong_stock 저장소 `docs/`) → [[Projects/Stock_storage/docs/README|문서 목록]]
- `code/` — 조회 SQL 등 코드 조각 → [[조회-SQL]]
- 수집 프로그램 전체 코드: GitHub `woong2399/woong_stock`

## 세션 기록
- [[2026-11-03-요약]]

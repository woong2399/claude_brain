# Surge / code

종목을 추리는 **SQL·수식**만 둔다. 돌아가는 프로그램 전체는 프로젝트 저장소에 두고 여기엔 복사하지 않는다.

- `picks_만들기.sql`, `surge_daily.py` — 10%↑ 종목 추리기 (`surge_daily.py` 의 원본은 `C:\Users\Jinwo\Documents\surge\`)
- `watchlist_일봉검증.sql` — 변동성 추적 목록(R·P·H) 일봉 검증 쿼리 (마더덕 `storage`)
- `spike_study.py` — 분봉 1년치 거래대금 급증 → 종가·내일 변동성 검증 (로컬 DB 읽기 전용, 수집 중엔 DB 잠김)
- `top30_monitor.py` — 하루 분봉으로 거래대금 30위 진입·이탈 모니터링
- `spike_lookup.py` — 하루 분봉에서 1분 거래대금 급증 종목 조회 (인자: 날짜, 배수, 최소 백만원, 시작시각)

분석용 임시 스크립트의 **사본**이다 (원본은 세션 임시 폴더). 모두 `C:\Users\Jinwo\Documents\storage\.venv` 의 파이썬으로 실행한다.

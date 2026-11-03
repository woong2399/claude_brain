---
project: Storage
repo: woong2399/storage (비공개)
updated: 2026-11-03
---
# Storage (주식 수집)

- **프로그램 폴더:** `C:\Users\Jinwo\Documents\storage` (11-04 에 `C:\Users\Jinwo\woong_stock` 에서 옮기고 이름을 바꿨다). 실행은 `python -m storage`, DB 는 `data\storage.duckdb`.
- GitHub 저장소 `woong2399/storage`, G 백업 폴더 `G:\storage_backup`(안의 파일도 `storage.duckdb`) 모두 바뀌었다 (사용자가 폴더·저장소 이름을 바꾸고 Claude 가 remote·문서·백업 파일 이름을 맞춤).
- 안 바뀐 것: MotherDuck 토큰 이름 `woong_stock_pc`.

## 한 줄 설명
키움 REST API 로 코스피·코스닥 2,673종목의 일봉·분봉을 모아 DuckDB 에 쌓는 프로젝트. (시뮬레이션·매수 근거 연구 기록은 2026-11-03 에 이 폴더에서 지웠다. 필요하면 git 기록에서 되살린다.)

## 현재 상태 (2026-11-03)
- **수집 방식 바꾸는 중 (11-03):** 평일 **16:00 정규장**(`run_update.bat 1600`) + **21:00 애프터마켓까지**(`run_update.bat 2100`, 월말 백업 포함), **PC 는 끄지 않음.** 코드는 고쳤고 11-03 에 1600·2100 을 손으로 한 번씩 돌려 둘 다 실패 0 으로 확인했다. 작업 스케줄러는 `storage_update_1600`·`storage_update_2100` 두 개만 남기고(예전 `woong_stock_*` 4개 삭제) **11-04 에 켰다 (월~금 16:00·21:00).** BIOS 자동 켜짐은 사용자가 15:40 으로 설정 (11-04). 첫 자동 실행은 11-04 16:00 → 결과 확인 대기. 같은 날 같은 이름(1600/2100)은 다시 돌려도 0종목을 받고 끝난다. → [[2026-11-03-수집방식변경]]
- **검증:** 거래정지로 보이는 종목(키움 상태 '거래정지' 또는 현재가 0)의 빠진 날은 검증 문제에서 빼고 알림에 따로 적는다 (11-03, 004415 서울식품우 계기).
- 예전 방식(꺼 둠): 평일 20:20 BIOS 켜짐 → 20:30 수집 → 업로드 → 월말 백업 → PC 종료. 주말 20:40 종료.
- **클라우드:** MotherDuck `storage` DB (daily 약 1,238만 행, stocks, kiwoom_mktcap(11-02부터), krx_daily(비어 있음)). MotherDuck 에는 DB 이름 바꾸기가 없어 `CREATE DATABASE storage FROM woong_stock` 으로 복제했고 행 수가 모두 같다. 옛 `woong_stock` DB 는 아직 남아 있다(지울지 사용자 결정).

## 다음 할 일
1. 옛 MotherDuck `woong_stock` DB 지울지 결정 (Colab 등 `woong_stock` 을 쓰는 곳이 없는지 확인한 뒤). 이름 변경의 나머지는 모두 끝났다 (11-04)
2. 11-04 16:00·21:00 첫 자동 실행 결과 확인 (자동 로그인·15:40 켜짐 포함), 절전이 꺼져 있는지 확인
3. 프로그램 `docs/` 를 새 수집 방식·거래정지 검증 제외로 고치기, push (지금까지 커밋 모두 push 됨, 마지막 `fbd7a38`)
4. 004415 서울식품우 거래정지·상장폐지 공시 확인
4. KRX Open API 키 신청(사용자) → `krx_daily` 채우기 (시가총액 확보)
5. 상장폐지 종목 확보 방법 (생존 편향)
6. 11-30 첫 월말 백업 확인 (이제 2100 실행 뒤에 한다)

## 꼭 지킬 것
- KRX 정보데이터시스템 자동 대량 조회 금지 (IP 차단 이력). 공식 Open API 만.
- MotherDuck 은 조회만. 같은 계정 `stocks` DB(매매일지)는 건드리지 않는다.
- 거래대금은 2005년 이후만, 분석은 2015-06 이후 (가격제한폭 ±15% 시절 제외).

## 이 폴더 안
- `docs/` — 상세 문서 사본 (원본: 프로그램 저장소 `docs/`) → [[Projects/Storage/docs/README|문서 목록]]
- `code/` — 조회 SQL 등 코드 조각 → [[조회-SQL]]
- 수집 프로그램 전체 코드: `C:\Users\Jinwo\Documents\storage`, GitHub `woong2399/storage`

## 세션 기록
- [[2026-11-04-이름변경]]
- [[2026-11-03-수집방식변경]]
- [[2026-11-03-요약]]

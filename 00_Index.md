---
updated: 2026-11-08
---
# 00 Index — 제2의 뇌 목차

> 새 세션은 여기부터 읽는다. 규칙은 [[CLAUDE]].

## 진행 중
| 프로젝트 | 상태 | 다음 할 일 | 노트 |
|---|---|---|---|
| Storage (주식 수집) | 16:00·21:00 두 번 자동 수집 (2100 뒤 프로그램 매매·수급 4종(투자자별·외국인 보유·공매도·대차·프로그램 매매, 2021-12~ 백필 완료)·업로드), 이동평균 표 `ma_daily`(매 갱신 재계산), KRX 시총 2010-01~, 정규장 추정 거래대금 칸 | 1540 분봉 전용 수집 결정(주말 검토), 수급 단위·기준 대조, docs 갱신 | [[Projects/Storage/README\|Storage]] |
| Assistant › Daily (주식 일지) | 보관함 `Documents\Obsidian\Daily` 로 이동, 플러그인 없는 새 일지 형식, Obsidian Sync 연결 확인 (폰 미확인), Surge CSV → 일지 스크립트 `csv_to_daily.py` 로 11/02·11/03 새로 생성, 구글 시트 `Daily 일지 입력`에 뉴스·텔레그램 입력, `sheet_to_journal.py` 로 11/02·11/03 일지를 `종목→뉴스→텔레그램` 형식으로 생성. **11/05: 공개 텔레그램 `t.me/tazastock` 자동 가져오기 + 날짜별 JSON(`daily_data\data`, 11/02~11/05)을 만들어 Assistant 클라우드 화면(MotherDuck `daily_pick`)에 공급** (Daily 는 데이터만, 화면은 Assistant) | 시트(11/04·11/05 행, 테마·뉴스) 채워 JSON 갱신·올리기, 매일 절차 굳히기, 폰 Sync 확인, Remotely Save 끄기 | [[Projects/Assistant/Daily/README\|Daily]] |
| Assistant › Surge (10%↑ 종목 추리기) | 11/02~11/05 10%↑ 156건 날짜별 CSV 저장(11/02 48·11/03 21·11/04 52·11/05 35). `surge_daily.py` 는 로컬 DB 읽기 전용·CSV 만 (거래대금 `amount_est` 정규장 추정) | "1600 끝났어" 받으면 `surge_daily.py` 실행, Daily 가져오는 방법·제외 규칙 정하기. 변동성 추적 목록 연구(11/05): 거래대금 순위·급증은 변동성만 맞힘, 수급 근사 지표 6개 검증 예정 | [[Projects/Assistant/Surge/README\|Surge]] |
| Assistant › News (뉴스 수집 → **주식 비서**의 입력) | 2026-11-05 **RSS 전용**으로 전환: 한국 10개 매체+미국 7개 매체, 작업 스케줄러가 매시 정각·30분 자동 수집, 새 자동 X 규칙·사건 묶기·종류 태그(정확도 미확인). 완전한 날짜는 11/06부터. 11/06 확인: 30분 수집 정상, 11/05 사건별 정리(474묶음). **11/07: 필터·애널리스트 선별·리포트 1장·대시보드 리포트 화면(로컬)을 만들고, 일일 자동 리포트(규칙 점수만, 매일 23:50)는 설계만** | 일일 리포트 자동화 코드(규칙 점수), 사진 기사 규칙 좁히기, 제외 키워드 66줄 반영, 연합뉴스 RSS 3개 오류, 정시 수집 안정 확인, X 표본 보고 규칙 다듬기, DART 수집, 이데일리 보충 여부, 미국 종목 범위 결정, 사용자 결정 4가지 | [[Projects/Assistant/News/README\|News]] |
| Assistant (주식 비서) | **11-12: 수집 뒤 일지 자동 실행(Storage `run_update.bat` 에 1600·2100 뒤 `surge_auto.py`, 미실행 확인 전), 신규 종목 빨간 테두리, 종목 추가, 거래대금 분포 조사([[Projects/Assistant/Sessions/2026-11-12-신규테두리·종목추가·거래대금분포·일지자동화|기록]])** · 11-11: 일지 앱 수정 기능(종목 화면)·테마 정리·시트 하나로 합침([[Projects/Assistant/Sessions/2026-11-11-일지앱-수정기능과시트합치기|기록]])** · 2026-11-06 **종목 창고**: 구글 시트 `surge`(이력·종목 탭) + 시트를 직접 읽는 Streamlit 앱 `woong-daily.streamlit.app`(이슈·종목·테마) 배포, 하루치를 시트까지 올리는 자동화 `surge_auto.py` 작성(실제 시트 쓰기는 미확인). 앞서 배포한 장전 보고서·급등주 일지 화면은 이제 쓰지 않는 쪽. 스케줄러는 미등록. **11/07: 기준봉(500억)+480일선 돌파 연구·박스권 시도·수급 데이터 확인([[Projects/Assistant/Sessions/2026-11-07-캔들연구와박스권|기록]])** | 11-12 저녁 `surge_auto.log` 로 자동 일지 확인, Storage 수급 수집 하한선 결정, 박스권은 예시 종목·기간부터, 수집 끝난 뒤 `run_auto.bat` 첫 실행 확인, 스케줄러 등록(평일 17:40), 종목 정보·테마 입력, 아티팩트·MotherDuck `surge_*` 표 정리 | [[Projects/Assistant/README|Assistant]] |
| Brain (볼트 구축·규칙) | 설정 완료, 폴더 이름 정리, 열기 규칙 변경 | `.obsidian/` 커밋 여부 결정 ([[인수인계-2026-11-03]]) | [[Projects/Brain/README\|Brain]] |

## 폴더
- `Projects/<이름>/` 프로젝트별 (**Daily·News·Surge 는 `Projects/Assistant/` 안의 하위 폴더**, 2026-11-06 합침) — `README.md`(요약) · `Sessions/`(요약) · `Archive/`(상세) · `docs/`(상세 문서) · `code/`(코드 조각)
- `Knowledge/` 오래 쓰는 사실·결정·나에 대한 정보
- `Inbox/` 사용자가 Claude 에게 남기는 메모
- `Templates/` 노트 틀

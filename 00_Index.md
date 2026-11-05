---
updated: 2026-11-05
---
# 00 Index — 제2의 뇌 목차

> 새 세션은 여기부터 읽는다. 규칙은 [[CLAUDE]].

## 진행 중
| 프로젝트 | 상태 | 다음 할 일 | 노트 |
|---|---|---|---|
| Storage (주식 수집) | 16:00·21:00 두 번 자동 수집 (1600 수집만, 2100 뒤 업로드), KRX 시총 2010-01~ 백필 완료, 정규장 추정 거래대금 칸 추가 | 11-04 첫 자동 실행 확인, krx.py 수정 커밋, docs 갱신 | [[Projects/Storage/README\|Storage]] |
| Daily (주식 일지) | 보관함 `Documents\Obsidian\Daily` 로 이동, 플러그인 없는 새 일지 형식, Obsidian Sync 연결 확인 (폰 미확인), Surge CSV → 일지 스크립트 `csv_to_daily.py` 로 11/02·11/03 새로 생성, 구글 시트 `Daily 일지 입력`에 뉴스·텔레그램 입력, `sheet_to_journal.py` 로 11/02·11/03 일지를 `종목→뉴스→텔레그램` 형식으로 생성 | 시트의 오타·빈 칸 고치고 일지 다시 돌리기, 새 날짜 절차 굳히기, 폰 Sync 확인, Remotely Save 끄기 | [[Projects/Daily/README\|Daily]] |
| Surge (10%↑ 종목 추리기) | 11/02·11/03 10%↑ 69건 날짜별 CSV 저장. `surge_daily.py` 는 로컬 DB 읽기 전용·CSV 만 (거래대금 `amount_est` 정규장 추정) | "1600 끝났어" 받으면 `surge_daily.py` 실행, Daily 가져오는 방법·제외 규칙 정하기. 변동성 추적 목록 연구(11/05): 거래대금 순위·급증은 변동성만 맞힘, 수급 근사 지표 6개 검증 예정 | [[Projects/Surge/README\|Surge]] |
| News (뉴스 수집 → **주식 비서**의 입력) | 2026-11-05 **RSS 전용**으로 전환: 한국 10개 매체+미국 7개 매체, 작업 스케줄러가 매시 정각·30분 자동 수집, 새 자동 X 규칙·사건 묶기·종류 태그(정확도 미확인). 완전한 날짜는 11/06부터 | 정시 수집 안정 확인, X 표본 보고 규칙 다듬기, DART 수집, 이데일리 보충 여부, 미국 종목 범위 결정, 사용자 결정 4가지 | [[Projects/News/README\|News]] |
| Assistant (주식 비서) | 2026-11-06 **Streamlit 클라우드(공개 주소)로 배포**: 장전 보고서 + 급등주 일지(읽기 전용), 데이터는 MotherDuck `assistant`. 대시보드는 이 프로젝트에서만 고침. 스케줄러는 미등록 | 폰 화면 확인, 스케줄러 등록(권한), 실적 발표·휴장일, ⑤ 테마 표 | [[Projects/Assistant/README|Assistant]] |
| Brain (볼트 구축·규칙) | 설정 완료, 폴더 이름 정리, 열기 규칙 변경 | `.obsidian/` 커밋 여부 결정 ([[인수인계-2026-11-03]]) | [[Projects/Brain/README\|Brain]] |

## 폴더
- `Projects/<이름>/` 프로젝트별 — `README.md`(요약) · `Sessions/`(요약) · `Archive/`(상세) · `docs/`(상세 문서) · `code/`(코드 조각)
- `Knowledge/` 오래 쓰는 사실·결정·나에 대한 정보
- `Inbox/` 사용자가 Claude 에게 남기는 메모
- `Templates/` 노트 틀

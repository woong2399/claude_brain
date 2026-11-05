---
project: Assistant
repo: (없음, 만들지 미정)
updated: 2026-11-05
---
# Assistant (주식 비서)

## 한 줄 설명
뉴스로 앞으로의 시나리오를 추론해 **보고서**를 만들고 **일정**을 관리하는, 사용자의 주식 비서. Storage·Surge·Daily·News 가 모두 이 비서의 부품이다. 목표와 구조 초안은 [[Knowledge/주식비서-목표와구조]].

## 현재 상태
- 2026-11-05: 프로젝트 폴더 생성, **기획 진행 중**. 장전 보고서(08:00) 아웃라인 확정 → [[docs/보고서-아웃라인]], 예정 행사 일정표 → [[docs/일정표-2026]]. 마감전 보고서는 나중.
- **공시(DART) 수집은 News 프로젝트에서 한다**(사용자 결정). 인증키는 사용자가 발급해 `news\.env` 에 `DART_API_KEY` 로 둠(채팅에 붙이지 않음).
- **코드 폴더: `C:\Users\Jinwo\Documents\assistant`** (사용자가 만든 빈 폴더 사용). git 저장소는 아직 안 만듦(미정). 실행 `run_report.bat` 또는 `python src\run_report.py [--dry-run]`.
- **보고서는 MotherDuck 새 DB `assistant`(표 `report_run`·`market_snapshot`·`events`)에 올리고, 핸드폰에서 보는 대시보드(Dive)로 만든다**(사용자 결정). 코드가 쓰고 Dive 는 읽기만 한다. 폰 화면 모양은 만든 뒤 확인(미확인).
- **미국 뉴스·공시 수집은 News 프로젝트에서 한다**(사용자 결정). 이 프로젝트는 하지 않는다.
- 2026-11-05 구현: 지수·지표 13개 수집(야후 기본, FRED·frankfurter 예비) 시험 통과(`--dry-run`, 예비 소스도 시험). **MotherDuck 업로드는 토큰 대기** — 사용자가 새 토큰을 만들어 `assistant\.env` 의 `MOTHERDUCK_TOKEN` 에 넣을 예정(채팅에 붙이지 않음).
- 구조(수집 → 이벤트 추출 → 지식표 → 검증 → 보고서, 일정)는 Claude 제안이고 **사용자 확정 전**.

## 부품 (이미 있는 것)
| 부품 | 맡은 일 | 노트 |
|---|---|---|
| Storage | 일봉·분봉 수집 | [[Projects/Storage/README\|Storage]] |
| Surge | 10%↑ 급등 종목 추리기 | [[Projects/Surge/README\|Surge]] |
| Daily | 직접 쓰는 주식 일지 (비서가 대체하지 않음) | [[Projects/Daily/README\|Daily]] |
| News | 뉴스 수집·검토 (한경·이데일리) | [[Projects/News/README\|News]] |

## 다음 할 일
1. 토큰을 `.env` 에 넣으면 업로드 시험(`run_report.bat`) → 대시보드(Dive) 첫 화면(지수·지표)
2. 작업 스케줄러 08:00 등록, 텔레그램 "완료 + 링크" 알림(제안)
3. 일정표 코드화 + 휴장일 표(KRX 미확인), 종목→테마 표 씨앗(Daily 테마 노트·시트)
4. DART 키 발급(사용자) 후 News `dart.py`, 실적 발표 대상 기업 목록 정하기
5. 프로그램 매매 수집 가능 여부는 Storage 수집이 끝난 뒤 시험 호출

## 중요한 결정
- 프로그램은 **코드로** 한다. 이유: Claude 가 직접 읽고 판단하면 토큰이 너무 많이 든다. AI 는 규칙이 못 알아본 새 이벤트 분류에만 쓴다.
- 추론은 예측이 아니라 "근거 있는 후보 목록". 매수·매도 권유 도구가 아니다.

## 이 폴더 안
- `Sessions/` — 세션 요약 (열 때 읽음)
- `Archive/` — 세션 상세 (필요할 때만 읽음)
- `docs/` — 기획서·설계
- `code/` — 코드 조각

## 세션 기록
- (아직 없음)

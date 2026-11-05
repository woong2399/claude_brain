---
project: Assistant
repo: (없음, 만들지 미정)
updated: 2026-11-06
---
# Assistant (주식 비서)

## 한 줄 설명
뉴스로 앞으로의 시나리오를 추론해 **보고서**를 만들고 **일정**을 관리하는, 사용자의 주식 비서. Storage·Surge·Daily·News 가 모두 이 비서의 부품이다. 목표와 구조 초안은 [[Knowledge/주식비서-목표와구조]].

## 현재 상태
- **2026-11-06 종목 창고:** Surge 10%↑ 종목(+텔레그램에만 나온 종목)을 **구글 시트 `surge`** 의 `이력` 탭에 쌓고(테마 F열·텔레그램 G열·뉴스 H열), 시트를 직접 읽는 **Streamlit 앱 `surge_app`**(이슈·종목·테마 세 장, 주소 `surge-warehouse.streamlit.app`, GitHub `woong2399/surge_app`)을 배포했다. 시트를 고치면 1분 안에 앱에 반영. 하루치를 시트까지 올리는 자동화 `surge\surge_auto.py`(서비스 계정)는 만들었지만 **실제 시트 쓰기·전체 한 바퀴는 아직 못 돌림**(Storage 수집이 DB 를 잡고 있었음). 아래 "늦게 변경"의 일지 화면·아티팩트는 이제 쓰지 않는 쪽. → [[2026-11-06-종목창고와자동화]], [[Knowledge/종목창고-시트-앱]]
- **2026-11-06 늦게 변경:** Streamlit 첫 화면은 이제 **급등주 일지만**(장전 보고서 화면은 `report_view/` 로 옮겨 보존). 같은 일지를 **Claude 아티팩트**로도 만듦(https://claude.ai/artifact/9gnBy8pZpJtdpaB8AUE2Rc, 데이터는 복사본이라 갱신은 Claude 에게 요청). **Streamlit/아티팩트 중 쓸 쪽은 사용자가 비교 중.**
- **2026-11-06 클라우드 배포:** 보고서를 MotherDuck `assistant.report_doc` 에 올리고 **Streamlit 클라우드**(공개 주소)로 배포. 코드는 GitHub 공개 `woong2399/assistant`. 화면 두 개: 장전 보고서(`app.py`), **급등주 일지**(`pages/1_급등주_일지.py`, 읽기 전용, 데이터 `daily_pick`). 일지는 `daily_data\data` JSON 을 `py src\load_daily.py` 로 올린다. **대시보드는 이 프로젝트에서만 고친다**(Daily 는 데이터만). 폰 화면 미확인. → [[2026-11-06-클라우드배포와일지]], [[Knowledge/주식비서-클라우드화면]]
- (아래 "MotherDuck 에 올리지 않고 PC JSON/Tailscale" 줄들은 11-05 기준 옛 상태. PC 서버 `100.92.146.20:8501` 은 이제 예비.)
- 2026-11-05: 프로젝트 폴더 생성, **기획 진행 중**. 장전 보고서(08:00) 아웃라인 확정 → [[docs/보고서-아웃라인]], 예정 행사 일정표 → [[docs/일정표-2026]]. 마감전 보고서는 나중.
- **공시(DART) 수집은 News 프로젝트에서 한다**(사용자 결정). 인증키는 사용자가 발급해 `news\.env` 에 `DART_API_KEY` 로 둠(채팅에 붙이지 않음).
- **코드 폴더: `C:\Users\Jinwo\Documents\assistant`** (사용자가 만든 빈 폴더 사용). git 저장소는 11-06 에 만들어 GitHub 공개 `woong2399/assistant` 에 올림. 실행 `run_report.bat` 또는 `python src\run_report.py [--dry-run]`.
- **보고서 저장·화면 변경(2026-11-05, 사용자): MotherDuck 에 올리지 않고 Streamlit 으로 만든다. 저장은 날짜별 JSON `data\reports\YYYY-MM-DD.json`.** 화면 `app.py`(`run_app.bat`), 수집 `run_report.bat`. 시험 통과(수집 12/12 저장, Streamlit 응답 확인). 폰 화면 모양은 미확인.
- 앞서 만든 MotherDuck `assistant` DB(표 3개)와 Dive `장전 보고서` 는 **남아 있다**(지울지 사용자 결정 대기). 토큰이 `assistant\.env` 에 있으나 지금 코드는 쓰지 않음.
- 폰 접속 방법 미정: A 같은 와이파이, B Tailscale(권장), C Streamlit Cloud+MotherDuck 데이터(PC 불필요하나 공개 주소·토큰 외부 저장). `run_app.bat` 은 보안상 `127.0.0.1` 로만 연다.
- **2026-11-05 추가 구현:** ④ 예정 행사(`src/schedule.py`: FOMC·CPI·고용지표·금통위·미국 휴장·옵션 만기·마녀의 날, 오늘부터 7일), ③ 전자공시(`src/dart.py` + 고치기 쉬운 키워드 목록 `dart_keywords.txt`: **계약·주주환원·리스크만**, 사용자 결정. 직전 영업일~오늘, 코스피·코스닥만, 정정 공시 합침, 호재/악재 표시는 제목만 본 참고용). 11/05 보고서에 공시 67건(계약 25·주주환원 20·리스크 22). **공시 수집은 News 에 두기로 했으나 News 폴더를 다른 세션이 개편 중이라 먼저 assistant 에 독립 파일로 만듦 → 나중에 옮김.** DART 키는 `news\.env`(없으면 assistant `.env`)에서 읽음.
- **스케줄러 등록은 자동 권한 검사에서 거부돼 못 함**(사용자가 직접 실행하거나 허용 필요). 자동 실행용 `run_report_auto.bat`, `start_app_auto.bat` 은 만들어 둠. 지금 화면 서버는 Tailscale 주소 `100.92.146.20:8501` 로 수동 실행 중(PC 재시작하면 꺼짐).
- **미국 뉴스·공시 수집은 News 프로젝트에서 한다**(사용자 결정). 이 프로젝트는 하지 않는다.
- 2026-11-05 구현: 지수·지표 12개 수집(비트코인 뺌)(야후 기본, FRED·frankfurter 예비) 시험 통과(`--dry-run`, 예비 소스도 시험). **
- 구조(수집 → 이벤트 추출 → 지식표 → 검증 → 보고서, 일정)는 Claude 제안이고 **사용자 확정 전**.

## 하위 프로젝트 (2026-11-06 합침, 사용자 결정)
Surge·News·Daily 폴더를 이 폴더 안으로 옮겼다(`git mv` 라 기록 보존, Storage·Brain 은 그대로). 각 하위 폴더도 `README`·`Sessions`·`Archive`·`docs`·`code` 다섯 칸을 그대로 가진다. **하위 프로젝트를 열 때는 그 폴더의 README 만 읽는다** (`CLAUDE.md`).
- [[Projects/Assistant/Daily/README|Daily]] — 일지·급등주 일지 화면용 데이터
- [[Projects/Assistant/News/README|News]] — 뉴스·공시 수집
- [[Projects/Assistant/Surge/README|Surge]] — 10%↑ 종목·변동성 추적
- 이 폴더 바로 아래 `Sessions/`·`Archive/`·`docs/`·`code/` 는 **비서 본체(보고서·화면·클라우드 배포)** 기록이다.

## 부품 (이미 있는 것)
| 부품 | 맡은 일 | 노트 |
|---|---|---|
| Storage | 일봉·분봉 수집 | [[Projects/Storage/README\|Storage]] |
| Surge | 10%↑ 급등 종목 추리기 | [[Projects/Assistant/Surge/README\|Surge]] |
| Daily | 직접 쓰는 주식 일지 (비서가 대체하지 않음) | [[Projects/Assistant/Daily/README\|Daily]] |
| News | 뉴스 수집·검토 (한경·이데일리) | [[Projects/Assistant/News/README\|News]] |

## 다음 할 일
0. **(종목 창고, 2026-11-06)** ① 오늘 16:00 수집이 끝나면 `run_auto.bat` 첫 실행을 같이 확인(시트 쓰기·텔레그램·DB 채우기·앱 반영, 빈 거래대금 17곳은 같은 날짜를 `--once` 로 다시 돌려 채움) ② 작업 스케줄러 등록(평일 17:40, 사용자가 직접) ③ 종목 정보·메모·비어 있는 테마 입력, `THEMES` 보강 ④ 아티팩트·MotherDuck `surge_*` 표 정리 여부 ⑤ 폰에서 테마 화면·라이트 모드 확인. 자세히는 [[2026-11-06-종목창고와자동화]]
1. **폰에서 클라우드 두 화면 확인**(미확인), MotherDuck 옛 표 3개·Dive 정리 여부, 일지 올리기 자동화 여부, Streamlit 토큰 새로 만들지(스크린샷에 일부 노출됨)
2. 작업 스케줄러 등록(평일 08:00 보고서, 로그인 때 화면 서버) — 권한 필요, 텔레그램 알림은 제안
   - 남은 ④ 보강: 미국·한국 실적 발표, 한국 휴장일, 2027 FOMC / ③ 공급계약 금액 비율(본문 조회 방법 미확인)
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
- [[2026-11-06-종목창고와자동화]] (상세: [[2026-11-06-종목창고와자동화-상세]])
- [[2026-11-06-클라우드배포와일지]] (상세: [[2026-11-06-클라우드배포와일지-상세]])
- [[2026-11-05-장전보고서-구축]] (상세: [[2026-11-05-장전보고서-구축-상세]])
- 오래 쓸 주의: [[Knowledge/주식비서-환경-주의]], [[Knowledge/주식비서-클라우드화면]]

---
project: Daily
updated: 2026-11-06
---
# 날짜별 JSON (`daily_data`)

원본은 PC `C:\Users\Jinwo\Documents\daily_data\` (기준일 2026-11-06). 이 문서는 요약이다. 경위: [[2026-11-05-텔레그램가져오기-날짜별JSON]].

## 폴더
- `data\YYYY-MM-DD.json` — 날짜별 급등주 일지 데이터 (Assistant 클라우드 화면의 원본)
- `build_daily_json.py` — Surge CSV + 텔레그램 + 시트 스냅샷 → JSON
- `fetch_telegram.py` — 공개 채널 `t.me/s/tazastock` 에서 `*일 *요일 상한가 및 급등주` 글만 가져오기
- `sheet_news.json` — 구글 시트에서 사용자가 채운 테마·뉴스의 스냅샷 (자동 아님)
- `app.py` — 로컬 Streamlit 시제품 (클라우드 화면이 생겨 안 쓰는 중, 남길지 미정)

## JSON 모양
```json
{"date": "2026-11-04",
 "stocks": [
  {"code": "430690", "name": "한싹", "pct": 29.96, "amount_est": 12345,
   "source": "both", "theme": ["보안주(정보)"],
   "issue": "텔레그램 원문 한 문장",
   "news": [{"headline": "헤드라인", "url": "https://…"}]}
 ]}
```
- `source`: `surge` / `telegram` / `both`. `pct` 내림차순. `code` 는 글자(앞자리 0, 영문 보존).

## 날마다 하는 순서 (수동)
1. Surge CSV 가 `C:\Users\Jinwo\Documents\surge\` 에 생겼는지 확인.
2. (시트에 테마·뉴스를 채웠다면) Claude 에게 "시트 다시 가져와" → `sheet_news.json` 갱신.
3. `daily_data` 폴더에서 `py -3 build_daily_json.py [--since 날짜] [--dry-run]` → `data\` 갱신 (텔레그램도 이때 읽음).
4. 올리기: `py C:\Users\Jinwo\Documents\assistant\src\load_daily.py --since 날짜` → MotherDuck `assistant.daily_pick` → 클라우드 화면.
- 열 약속과 역할 나누기(화면은 Assistant 세션만 고침): [[Knowledge/주식비서-클라우드화면]].

## 텔레그램 가져오기 규칙
- 글 맨 위 줄이 `N일 요일 상한가 및 급등주`(앞에 이모지)인 것만. 월은 글의 게시 날짜(한국 시간)로. 본문은 `이름 / (코드) / (+등락률%) / 문장` 블록 반복.
- 공개 웹 미리보기라 로그인·키가 필요 없음. 읽기 전용, 쪽마다 1.5초 쉼.

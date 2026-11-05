"""구글 시트 `surge` 에 올릴 월별 표(CSV)를 만든다.

실행 (로컬 DuckDB 는 2.0 형식이라 Storage 의 .venv 로 돌린다):
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_sheet.py              # 이번 달 전체
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_sheet.py 2026-11       # 그 달 전체
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_sheet.py --no-db       # DB 를 안 읽음(시험용)

하는 일 (날짜마다):
  1. daily_data\\data\\YYYY-MM-DD.json 을 읽는다. (먼저 build_daily_json.py 로 Surge CSV + 텔레그램을 합쳐 둔다)
  2. 10%↑ 종목(source 가 surge·both)은 등락률 큰 순으로 먼저 놓는다. 값은 Surge CSV 의 DB 값 그대로.
  3. 텔레그램에만 있는 종목(source = telegram)은 그 아래에 놓고, 등락률과 거래대금(amount_est)을
     로컬 DB 에서 다시 채운다. (surge_daily.py 와 같은 정의: 정규장 종가, 전 거래일 종가 대비)
  4. 텔레그램 글은 마지막 열 telegram 에 넣는다.
쓰는 곳: 이 폴더의 sheet\\YYYY-MM.csv 뿐 (덮어씀). DB 는 읽기 전용.

열: date, code, name, pct, amount_est, theme, telegram, news   (시트 탭 `이력` 의 A~H열과 같다)
  theme(F)·news(H) 는 사용자가 시트에서 직접 쓰는 칸이라 비워 둔다. 시트에 새 행을 붙일 때 F·H 를 덮어쓰지 않도록 A~E·G 만 쓴다.
주의:
  - 수집 중(평일 16:00~17:20경, 21:00~22:35경, storage flow 실행 중)에는 DB 가 잠겨 있다. 이때는 경고를 내고
    텔레그램 값(등락률)만 넣고 거래대금은 비운다. 끝난 뒤 다시 돌리면 채워진다.
  - 신규상장 첫날(전일 종가 없음)은 DB 로 등락률을 못 구한다. 텔레그램 값을 두고 '* ' 를 telegram 열 앞에 붙인다.
  - 구글 시트에 올리는 것은 이 스크립트가 하지 않는다. CSV 를 시트 탭에 붙여넣거나 Claude 에게 "시트 갱신해줘".
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = Path(r"C:\Users\Jinwo\Documents\daily_data\data")
DB = Path(r"C:\Users\Jinwo\Documents\storage\data\storage.duckdb")
OUT = HERE / "sheet"
HEAD = ["date", "code", "name", "pct", "amount_est", "theme", "telegram", "news"]

# 텔레그램 글에서 테마를 뽑는 단어 목록. 새 테마가 나오면 여기에 추가한다 (긴 이름이 먼저 맞도록 자동 정렬).
THEMES = [
    "2차전지", "태양광에너지", "풍력에너지", "전력저장장치(ESS)", "전기차", "수소에너지(수소차/연료전지 등)",
    "고체산화물 연료전지(SOFC)", "리튬", "전후 재건(우크라/중동 전쟁 등)", "건설 대표주", "건설기계",
    "정치/인맥(한동훈)", "정치/인맥(오세훈)", "보안주(정보)", "LNG(액화천연가스)", "조선기자재",
    "피팅(관이음쇠)/밸브", "조선", "방위산업/전쟁 및 테러", "철강 주요종목", "항공/저가 항공사(LCC)",
    "반도체", "제약/바이오", "의료기기", "의료AI", "자동차부품", "음식료업종",
]
_TH = sorted(THEMES, key=len, reverse=True)
_PHRASE = re.compile(r"(.{0,60}?)\s*(테마|관련주|그룹주)\s*상승")


def extract_themes(text):
    """'... 태양광에너지/ 2차전지 테마 상승 ...' 같은 문구에서 테마 이름을 뽑아 ', ' 로 잇는다 (초안, 시트에서 고친다)."""
    found = []
    for m in _PHRASE.finditer(text or ""):
        seg, kind = m.group(1), m.group(2)
        if kind == "그룹주":
            tail = re.search(r"([A-Za-z가-힣0-9]+)$", seg.strip())
            if tail:
                found.append(tail.group(1) + " 그룹주")
            continue
        seg = seg.strip()
        while seg:
            seg = re.sub(r"[\s/,]+$", "", seg)
            seg = re.sub(r"\s*관련주$", "", seg)
            hit = next((t for t in _TH if seg.endswith(t)), None)
            if not hit:
                break
            found.append(hit)
            seg = seg[: -len(hit)]
            seg = re.sub(r"\s*일부$", "", seg)
    seen = []
    for t in reversed(found):
        if t not in seen:
            seen.append(t)
    return ", ".join(seen)



def db_values(day, codes):
    """{code: (pct, amount_est)} — 전일 종가가 없으면 pct 는 None. DB 를 못 열면 None 을 돌려준다."""
    try:
        import duckdb
        con = duckdb.connect(str(DB), read_only=True)
    except Exception as e:
        print(f"경고: 로컬 DB 를 열 수 없습니다 (수집 중이면 끝난 뒤 다시 실행): {str(e).splitlines()[0]}")
        return None
    try:
        q = ",".join("?" * len(codes))
        rows = con.execute(f"""
            WITH x AS (
              SELECT code, date, close, amount_est,
                     lag(close) OVER (PARTITION BY code ORDER BY date) AS prev
              FROM daily_bar
              WHERE venue = 'KRX_REG' AND adjusted AND close > 0 AND date <= ?
            )
            SELECT code,
                   CASE WHEN prev > 0 THEN round((close * 1.0 / prev - 1) * 100, 2) END,
                   amount_est
            FROM x WHERE date = ? AND code IN ({q})
        """, [day, day] + list(codes)).fetchall()
    finally:
        con.close()
    return {c: (p, a) for c, p, a in rows}


def build_day(path, use_db):
    d = json.loads(path.read_text(encoding="utf-8"))
    day = d["date"]
    stocks = d["stocks"]
    top = sorted((s for s in stocks if s["source"] != "telegram"), key=lambda s: -(s["pct"] or 0))
    tg = [s for s in stocks if s["source"] == "telegram"]
    out = [[day, s["code"], s["name"], s["pct"], s["amount_est"], "", s.get("issue") or "", ""] for s in top]
    vals = db_values(date.fromisoformat(day), [s["code"] for s in tg]) if (tg and use_db) else None
    for s in sorted(tg, key=lambda s: -(s["pct"] or 0)):
        pct, amt, mark = s["pct"], None, ""
        if vals is not None and s["code"] in vals:
            p, a = vals[s["code"]]
            amt = a
            if p is not None:
                pct = p
            else:
                mark = "* "  # 전일 종가 없음(신규상장 첫날 등): 등락률은 텔레그램 값
        out.append([day, s["code"], s["name"], pct, amt, "", mark + (s.get("issue") or ""), ""])
    return out, len(tg), vals is None and bool(tg)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_db = "--no-db" not in sys.argv
    month = args[0] if args else date.today().strftime("%Y-%m")
    files = sorted(DATA.glob(f"{month}-*.json"))
    if not files:
        print(f"{month}: {DATA} 에 날짜별 JSON 이 없습니다. build_daily_json.py 를 먼저 돌리세요.")
        return 1
    rows, n_tg, locked = [], 0, False
    for f in files:
        r, t, l = build_day(f, use_db)
        rows += r
        n_tg += t
        locked = locked or l
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{month}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEAD)
        w.writerows(rows)
    empty = sum(1 for r in rows if r[4] in (None, ""))
    print(f"{month}: {len(files)}일, {len(rows)}행 (텔레그램에만 {n_tg}) → {path}")
    if empty:
        print(f"거래대금 빈칸 {empty}행" + (" — DB 를 못 읽어서입니다. 수집이 끝난 뒤 다시 실행하세요." if locked or not use_db else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

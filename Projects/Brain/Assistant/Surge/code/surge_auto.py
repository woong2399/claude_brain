"""하루치 급등 종목을 만들어 구글 시트 `surge` 까지 올리는 자동화 한 방.

실행 (Storage 의 .venv 로. 로컬 DuckDB 가 2.0 형식이라서):
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_auto.py             # 오늘
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_auto.py 2026-11-06  # 그 날짜
  ... --dry-run   시트에는 쓰지 않고 무엇을 할지만 보여 준다
  ... --no-sheet  CSV(surge\\sheet\\YYYY-MM.csv)까지만 만든다

순서:
  1. surge_daily.py  — 그날 10%↑ CSV (DB 가 잠겨 있으면 10분 간격으로 최대 6번 다시 시도, 휴장일·수집 전이면 끝냄)
  2. build_daily_json.py --since 날짜 — 텔레그램 + CSV → daily_data\\data\\날짜.json
  3. surge_sheet.build_day — 10%↑ 종목 + 텔레그램에만 있는 종목(등락률·거래대금은 DB 에서 다시 채움) + 텔레그램 글
  4. 테마 — 텔레그램 글에서 뽑는다(surge_sheet.THEMES 목록). 날짜 행에는 그날 나온 테마만 적는다(그래야 날짜별 테마 변화가 남는다).
     이미 있는 행에 사용자가 적은 테마가 있으면 지우지 않고, 새로 뽑힌 테마만 뒤에 추가한다.
     종목 하나의 전체 테마는 날짜별 테마를 합친 것이라 새 테마가 나오면 자동으로 늘어난다(앱·시트 `종목` 탭이 합친다).
  5. 구글 시트 — `이력` 탭에 없는 (날짜, 코드) 행만 맨 아래에 붙이고, 이미 있는 행은 빈 칸(거래대금·등락률·테마·텔레그램)만 채운다.
     사용자가 쓴 값은 지우지 않는다(테마는 추가만). `종목` 탭에는 새 종목 코드를 붙인다.

구글 시트 쓰기에는 서비스 계정 키가 필요하다: surge\\secrets\\service_account.json (비밀값이라 어디에도 복사·출력하지 않는다).
키가 없으면 5번만 건너뛰고 CSV 까지 만든다.
종료 코드: 0 성공, 1 데이터 없음(휴장일·수집 전), 2 오류.
"""
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import surge_sheet as S  # noqa: E402

SHEET_ID = "1SpHykeusHQ9PjYCu2W46DJrbgDKmcdmWfjfcaLkgOkM"
KEY = HERE / "secrets" / "service_account.json"
DAILY = Path(r"C:\Users\Jinwo\Documents\assistant\daily_data")
RETRY_WAIT, RETRY_MAX = 600, 6


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def step_csv(day):
    """1단계: surge_daily.py. DB 잠김(2)이면 기다렸다 다시."""
    tries = 1 if "--once" in sys.argv else RETRY_MAX
    for n in range(1, tries + 1):
        r = subprocess.run([sys.executable, str(HERE / "surge_daily.py"), day], capture_output=True, text=True, encoding="utf-8")
        out = (r.stdout or "").strip().splitlines()
        log(f"surge_daily({n}): rc={r.returncode} {out[-1] if out else ''}")
        if r.returncode in (0, 1):
            return r.returncode
        if n < tries:
            log(f"DB 가 잠겨 있어 {RETRY_WAIT // 60}분 뒤 다시 합니다")
            time.sleep(RETRY_WAIT)
    return 2


def step_json(day):
    """2단계: 텔레그램 + CSV → 날짜별 JSON (daily_data 의 스크립트를 그대로 쓴다)."""
    r = subprocess.run(["py", "build_daily_json.py", "--since", day], cwd=DAILY, capture_output=True, text=True, encoding="utf-8")
    tail = (r.stdout or "").strip().splitlines()[-2:]
    log(f"build_daily_json: rc={r.returncode} {' / '.join(tail)}")
    return r.returncode == 0


def merge_themes(existing, new):
    """existing 의 순서를 지키고, new 중 없던 것만 뒤에 붙인다 (쉼표로 구분)."""
    cur = [t.strip() for t in (existing or "").split(",") if t.strip()]
    for t in (new or "").split(","):
        t = t.strip()
        if t and t not in cur:
            cur.append(t)
    return ", ".join(cur)


def sheet_sync(rows, dry):
    """5단계: 이력 탭에 행을 붙이고 빈 칸을 채운다. 종목 탭에 새 코드를 붙인다."""
    import gspread
    gc = gspread.service_account(filename=str(KEY))
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet("이력")
    vals = ws.get_all_values()
    pad = lambda r: (list(r) + [""] * 8)[:8]  # noqa: E731
    where = {}
    for i, r in enumerate(vals[1:], start=2):
        r = pad(r)
        where[(r[0], r[1])] = i

    updates, appends = [], []
    for r in rows:  # [date, code, name, pct, amount_est, theme, telegram, news]
        day, code, name, pct, amt, theme, tg, news = r
        key = (day, code)
        if key in where:
            i = where[key]
            cur = pad(vals[i - 1])
            if amt not in (None, "") and not cur[4]:
                updates += [{"range": f"D{i}", "values": [[pct]]}, {"range": f"E{i}", "values": [[amt]]}]
            if tg and not cur[6]:
                updates.append({"range": f"G{i}", "values": [[tg]]})
            merged = merge_themes(cur[5], theme)  # 사용자가 적은 테마는 두고 새로 뽑힌 것만 추가
            if merged != cur[5]:
                updates.append({"range": f"F{i}", "values": [[merged]]})
        else:
            appends.append([day, code, name, pct, "" if amt is None else amt, theme, tg, news])  # 그날 나온 테마만

    log(f"시트 이력: 새 행 {len(appends)}, 빈 칸 채우기 {len(updates)}")
    ws2 = sh.worksheet("종목")
    have = set(ws2.col_values(1)[1:])
    new_codes = sorted({a[1] for a in appends} - have)
    log(f"시트 종목: 새 코드 {len(new_codes)}")
    if dry:
        log("--dry-run: 시트에는 쓰지 않았습니다")
        return
    if updates:
        ws.batch_update(updates, value_input_option="RAW")
    if appends:
        ws.append_rows(appends, value_input_option="RAW", table_range="A1")
    if new_codes:
        start = len(have) + 2
        ws2.update(range_name=f"A{start}", values=[[c] for c in new_codes], raw=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    day = args[0] if args else date.today().isoformat()
    dry, no_sheet = "--dry-run" in sys.argv, "--no-sheet" in sys.argv
    log(f"{day} 시작")

    rc = step_csv(day)
    if rc == 1:
        log("데이터가 없습니다(휴장일이거나 수집 전). 끝냅니다.")
        return 1
    if rc != 0:
        log("DB 를 읽지 못했습니다. 수집이 끝난 뒤 다시 실행하세요.")
        return 2
    if not step_json(day):
        log("텔레그램·JSON 단계가 실패했습니다.")
        return 2

    path = DAILY / "data" / f"{day}.json"
    if not path.exists():
        log(f"{path} 가 없습니다.")
        return 2
    rows, n_tg, locked = S.build_day(path, use_db=True)
    rows = [r[:5] + [S.extract_themes((r[6] or "").lstrip("* ")), r[6].lstrip("* "), ""] for r in rows]
    log(f"{day}: {len(rows)}행 (텔레그램에만 {n_tg}){' — DB 잠김, 거래대금 빈칸' if locked else ''}")

    if no_sheet:
        S.main()  # CSV 도 갱신
        return 0
    if not KEY.exists():
        log(f"서비스 계정 키가 없어 시트 단계는 건너뜁니다: {KEY}")
        return 0
    try:
        sheet_sync(rows, dry)
    except Exception as e:  # 시트 공유·키 문제 등
        log(f"시트 단계 오류: {type(e).__name__}: {str(e)[:300]}")
        return 2
    log("끝")
    return 0


if __name__ == "__main__":
    sys.exit(main())

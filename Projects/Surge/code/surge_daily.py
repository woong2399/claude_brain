"""그날 전일 종가 대비 10% 이상 오른 종목을 surge.main.picks 에 넣고 날짜별 CSV 를 만든다.

실행 (MotherDuck 은 DuckDB 1.5.x 가 필요해서 Storage 의 .venv-md 로 돌린다):
  C:\\Users\\Jinwo\\Documents\\storage\\.venv-md\\Scripts\\python surge_daily.py            # 오늘
  C:\\Users\\Jinwo\\Documents\\storage\\.venv-md\\Scripts\\python surge_daily.py 2026-11-03  # 그날

- storage.daily / storage.stocks 는 조회만 한다. 쓰는 곳은 surge.main.picks 뿐이다.
- 같은 날을 여러 번 돌려도 그날 행을 지우고 다시 넣으므로 중복되지 않는다.
- 토큰은 Storage 의 .env (MOTHERDUCK_TOKEN) 에서 읽기만 한다. 이 파일에 적지 않는다.
- 종료 코드: 0 성공, 1 데이터 없음·부족(수집 전이거나 휴장일), 2 그 밖의 오류.
"""
import csv
import sys
from datetime import date
from pathlib import Path

import duckdb

ENV = Path(r"C:\Users\Jinwo\Documents\storage\.env")
OUT = Path(__file__).resolve().parent
MIN_ROWS = 1000  # 그날 daily 행이 이보다 적으면 수집이 덜 된 것으로 본다


def token() -> str:
    for line in ENV.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("MOTHERDUCK_TOKEN="):
            return line.split("=", 1)[1].strip()
    sys.exit("Storage .env 에 MOTHERDUCK_TOKEN 이 없습니다")


def main() -> int:
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    con = duckdb.connect(f"md:?motherduck_token={token()}")
    try:
        n = con.execute("SELECT count(*) FROM storage.main.daily WHERE date = ?", [d]).fetchone()[0]
        if n < MIN_ROWS:
            print(f"{d}: storage.daily 에 {n}행뿐입니다. 수집 전이거나 휴장일이라 건너뜁니다.")
            return 1
        con.execute("BEGIN")
        con.execute("DELETE FROM surge.main.picks WHERE date = ?", [d])
        con.execute("""
            INSERT INTO surge.main.picks
            WITH x AS (
              SELECT code, date, close, amount,
                     lag(close) OVER (PARTITION BY code ORDER BY date) AS prev
              FROM storage.main.daily
              WHERE close > 0 AND date <= ?
            )
            SELECT x.date, x.code, s.name,
                   round((x.close * 1.0 / x.prev - 1) * 100, 2) AS pct, x.amount
            FROM x JOIN storage.main.stocks s USING (code)
            WHERE x.date = ? AND x.prev > 0 AND x.close * 1.0 / x.prev - 1 >= 0.10
            ORDER BY pct DESC
        """, [d, d])
        con.execute("COMMIT")
        rows = con.execute(
            "SELECT date, code, name, pct, amount FROM surge.main.picks WHERE date = ? ORDER BY pct DESC", [d]
        ).fetchall()
    except Exception as e:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        print(f"오류: {e}")
        return 2
    finally:
        con.close()

    path = OUT / f"{d.year}년 {d.month}월 {d.day}일.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "code", "name", "pct", "amount"])
        w.writerows(rows)
    rng = f", 등락률 {rows[-1][3]} ~ {rows[0][3]}%" if rows else ""
    print(f"{d}: {len(rows)}종목{rng} → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

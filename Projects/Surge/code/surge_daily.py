"""그날 전일 종가 대비 10% 이상 오른 종목을 날짜별 CSV 로 만든다.

실행 (로컬 DuckDB 는 2.0 형식이라 Storage 의 .venv 로 돌린다):
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_daily.py            # 오늘
  C:\\Users\\Jinwo\\Documents\\storage\\.venv\\Scripts\\python surge_daily.py 2026-11-03  # 그날

- Storage 의 로컬 DuckDB(data/storage.duckdb)를 읽기 전용으로 연다. 어디에도 쓰지 않는다 (CSV 만 만든다).
- 등락률: 정규장 종가(KRX_REG 수정주가) 기준, 전 거래일 종가 대비.
- 거래대금 amount_est: 정규장(09:00~15:30) 분봉 추정 거래대금, 백만 원. 애프터마켓은 들어가지 않는다.
- 수집 중(평일 16:00~17:20경, 21:00~22:35경)에는 DB 가 잠겨 읽을 수 없다. 1600 수집이 끝난 뒤 돌린다.
- 같은 날을 다시 돌리면 그날 CSV 를 새로 덮어쓴다.
- 종료 코드: 0 성공, 1 데이터 없음·부족(수집 전이거나 휴장일), 2 그 밖의 오류(DB 잠김 포함).
"""
import csv
import sys
from datetime import date
from pathlib import Path

import duckdb

DB = Path(r"C:\Users\Jinwo\Documents\storage\data\storage.duckdb")
OUT = Path(__file__).resolve().parent
MIN_ROWS = 1000  # 그날 정규장 일봉이 이보다 적으면 수집이 덜 된 것으로 본다


def main() -> int:
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    try:
        con = duckdb.connect(str(DB), read_only=True)
    except duckdb.IOException as e:
        print(f"DB 를 열 수 없습니다 (수집 중이면 끝난 뒤 다시 실행): {e}")
        return 2
    try:
        n = con.execute("SELECT count(*) FROM daily_bar WHERE venue = 'KRX_REG' AND adjusted AND date = ?",
                        [d]).fetchall()[0][0]
        if n < MIN_ROWS:
            print(f"{d}: 정규장 일봉이 {n}행뿐입니다. 수집 전이거나 휴장일이라 건너뜁니다.")
            return 1
        rows = con.execute("""
            WITH x AS (
              SELECT code, date, close, amount_est,
                     lag(close) OVER (PARTITION BY code ORDER BY date) AS prev
              FROM daily_bar
              WHERE venue = 'KRX_REG' AND adjusted AND close > 0 AND date <= ?
            )
            SELECT x.date, x.code, s.name, round((x.close * 1.0 / x.prev - 1) * 100, 2) AS pct, x.amount_est
            FROM x JOIN stocks s USING (code)
            WHERE x.date = ? AND x.prev > 0 AND x.close * 1.0 / x.prev - 1 >= 0.10
            ORDER BY pct DESC
        """, [d, d]).fetchall()
    except Exception as e:
        print(f"오류: {e}")
        return 2
    finally:
        con.close()

    path = OUT / f"{d.year}년 {d.month}월 {d.day}일.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "code", "name", "pct", "amount_est"])
        w.writerows(rows)
    rng = f", 등락률 {rows[-1][3]} ~ {rows[0][3]}%" if rows else ""
    print(f"{d}: {len(rows)}종목{rng} → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

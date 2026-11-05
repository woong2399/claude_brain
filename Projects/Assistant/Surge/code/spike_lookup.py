import sys

import duckdb

D = sys.argv[1] if len(sys.argv) > 1 else "2026-11-04"
MULT = float(sys.argv[2]) if len(sys.argv) > 2 else 10
MIN_AMT = float(sys.argv[3]) if len(sys.argv) > 3 else 1000  # 백만 원
START = sys.argv[4] if len(sys.argv) > 4 else "09:30"  # 이 시각부터 판정 (시초 혼잡 제외)

con = duckdb.connect(r"C:\Users\Jinwo\Documents\storage\data\storage.duckdb", read_only=True)
con.execute("""
create temp table bars as
select code, ts, open, close, (open+high+low+close)/4.0*volume/1e6 as amt
from minute_bar
where cast(ts as date)=? and venue='KRX' and cast(ts as time) between time '09:00' and time '15:29'
""", [D])
con.execute("""
create temp table grid as
select m.ts, c.code from (select distinct ts from bars) m cross join (select distinct code from bars) c
""")
con.execute("""
create temp table s as
select g.ts, g.code, coalesce(b.amt, 0) as amt, b.open, b.close,
       avg(coalesce(b.amt, 0)) over (partition by g.code order by g.ts rows between 30 preceding and 1 preceding) as base,
       sum(coalesce(b.amt, 0)) over (partition by g.code order by g.ts) as cum
from grid g left join bars b using (ts, code)
""")
names = dict(con.execute("select code, name from stocks").fetchall())
rows = con.execute(f"""
select code, ts, amt, base, amt / nullif(base, 0) as mult, round((close * 1.0 / open - 1) * 100, 2) as bar_pct, cum
from s
where cast(ts as time) >= time '{START}' and amt >= ? and (base = 0 or amt >= ? * base)
order by ts, amt desc
""", [MIN_AMT, MULT]).fetchall()
print(f"조건: {START}~15:29, 1분 거래대금 ≥ {MIN_AMT:,.0f}백만 & ≥ 직전 30분 평균의 {MULT:g}배 → {len(rows)}건")

by = {}
for code, ts, amt, base, mult, pct, cum in rows:
    by.setdefault(code, []).append((ts, amt, base, mult, pct, cum))
print(f"종목 수 {len(by)}")
summary = []
for code, ev in by.items():
    peak = max(ev, key=lambda e: e[1])
    summary.append((ev[0][0], code, len(ev), peak))
summary.sort()
for first, code, n, peak in summary:
    mult = "신규(직전 거래 없음)" if not peak[2] else f"{peak[3]:.0f}배"
    print(f"{first:%H:%M} {names.get(code, code)} ({code}) 급증 {n}분 / 최대 {peak[0]:%H:%M} {peak[1]:,.0f}백만 ({mult}), 그 분 봉 {peak[4]:+.2f}%")

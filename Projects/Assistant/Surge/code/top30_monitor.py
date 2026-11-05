import sys
from datetime import date

import duckdb

D = sys.argv[1] if len(sys.argv) > 1 else "2026-11-04"
con = duckdb.connect(r"C:\Users\Jinwo\Documents\storage\data\storage.duckdb", read_only=True)

print("venue:", con.execute("select venue, source, count(*) from minute_bar where cast(ts as date)=? group by 1,2", [D]).fetchall())
print("범위:", con.execute(
    "select min(ts), max(ts), count(distinct ts), count(distinct code) from minute_bar where cast(ts as date)=?", [D]).fetchall())

con.execute("""
create temp table bars as
select code, ts, (open+high+low+close)/4.0*volume as est
from minute_bar
where cast(ts as date)=? and venue='KRX'
  and cast(ts as time) between time '09:00' and time '15:30'
""", [D])
print("KRX 09:00~15:30 봉:", con.execute("select count(*), min(ts), max(ts), count(distinct ts) from bars").fetchall())

con.execute("""
create temp table grid as
select m.ts, c.code from (select distinct ts from bars) m cross join (select distinct code from bars) c
""")
con.execute("""
create temp table cum as
select g.ts, g.code,
       sum(coalesce(b.est, 0)) over (partition by g.code order by g.ts) as cum_amt
from grid g left join bars b using (ts, code)
""")
con.execute("""
create temp table top as
select ts, code, cum_amt, row_number() over (partition by ts order by cum_amt desc) as rk
from cum
qualify rk <= 30
""")
con.execute("""
create temp table ev as
with t as (select ts, code, rk from top),
tm as (select ts, lead(ts) over (order by ts) as nxt from (select distinct ts from top)),
ins as (
  select tm.nxt as ts, t.code, 'IN' as kind, t.rk as rk_prev from t join tm using (ts)
  where tm.nxt is not null
),
-- IN: 이번 분에는 있고 직전 분에는 없음 / OUT: 직전 분에는 있고 이번 분에는 없음
ent as (
  select t.ts, t.code, 'IN' as kind, t.rk from t
  join (select ts, lag(ts) over (order by ts) as prv from (select distinct ts from top)) p using (ts)
  where p.prv is not null and not exists (select 1 from t t2 where t2.ts = p.prv and t2.code = t.code)
),
lft as (
  select p.ts, t.code, 'OUT' as kind, t.rk from t
  join (select ts, lead(ts) over (order by ts) as nxt from (select distinct ts from top)) p on p.ts = t.ts
  where p.nxt is not null and not exists (select 1 from t t2 where t2.ts = p.nxt and t2.code = t.code)
)
select * from ent
union all
select nxt_ts as ts, code, kind, rk from (
  select (select min(ts2) from (select distinct ts as ts2 from top) where ts2 > l.ts) as nxt_ts, l.code, l.kind, l.rk from lft l
)
""")

names = dict(con.execute("select code, name from stocks").fetchall())
first_ts = con.execute("select min(ts) from top").fetchone()[0]
last_ts = con.execute("select max(ts) from top").fetchone()[0]

print(f"\n== {first_ts:%H:%M} 시작 30위 ==")
for ts, code, amt, rk in con.execute("select ts, code, cum_amt, rk from top where ts=? order by rk", [first_ts]).fetchall():
    print(f"{rk:2d} {names.get(code, code)} ({code}) {amt/1e6:,.0f}백만")

events = con.execute("select ts, code, kind, rk from ev order by ts, kind desc, rk").fetchall()
print(f"\n== 순위권 변동 총 {len(events)}건 (IN {sum(1 for e in events if e[2]=='IN')}, OUT {sum(1 for e in events if e[2]=='OUT')}) ==")
for ts, code, kind, rk in events:
    print(f"{ts:%H:%M} {kind:3s} {names.get(code, code)} ({code}) rk{rk}")

print(f"\n== {last_ts:%H:%M} 마감 30위 ==")
for ts, code, amt, rk in con.execute("select ts, code, cum_amt, rk from top where ts=? order by rk", [last_ts]).fetchall():
    print(f"{rk:2d} {names.get(code, code)} ({code}) {amt/1e6:,.0f}백만")

print("\n== 하루 동안 30위권에 들었던 종목 (머문 분 수) ==")
for code, mins, first, last in con.execute("""
    select code, count(*), min(ts), max(ts) from top group by code order by count(*) desc
""").fetchall():
    print(f"{names.get(code, code)} ({code}) {mins}분 {first:%H:%M}~{last:%H:%M}")

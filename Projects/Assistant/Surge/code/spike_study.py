import time
from datetime import date

import duckdb

t0 = time.time()
con = duckdb.connect(r"C:\Users\Jinwo\Documents\storage\data\storage.duckdb", read_only=True)
con.execute("create temp table dstat (code varchar, d date, close double, amt double)")
con.execute("create temp table cand (code varchar, d date, ts timestamp, amt double, base double, c double)")

months = []
y, m = 2025, 10
while (y, m) <= (2026, 11):
    s = date(y, m, 1)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    months.append((s, date(ny, nm, 1)))
    y, m = ny, nm

for s, e in months:
    con.execute("""
    create or replace temp table m as
    select code, ts, cast(ts as date) d, (open+high+low+close)/4.0*volume/1e6 as amt, close
    from minute_bar
    where venue='KRX' and ts >= ? and ts < ? and cast(ts as time) between time '09:00' and time '15:30'
    """, [s, e])
    con.execute("insert into dstat select code, d, arg_max(close, ts), sum(amt) from m group by code, d")
    con.execute("""
    insert into cand
    select code, d, ts, amt, coalesce(base, 0), close from (
      select *, sum(amt) over (partition by code, d order by ts
             range between interval 30 minutes preceding and interval 1 minute preceding) / 30.0 as base
      from m
    ) where cast(ts as time) >= time '09:30' and cast(ts as time) < time '15:30'
        and amt >= 500 and (base is null or base = 0 or amt >= 5 * base)
    """)
    print(f"{s} done {time.time()-t0:.0f}s", flush=True)

con.execute("""
create temp table ds as
select code, d, close, amt,
  lag(close) over (partition by code order by d) as prev,
  lead(close) over (partition by code order by d) as nxt
from dstat
""")
print("일 수:", con.execute("select count(distinct d) from ds").fetchone())
print("종목-일 수:", con.execute("select count(*) from ds").fetchone())

# 기준선
tot_days = con.execute("select count(distinct d) from ds where prev is not null and nxt is not null").fetchone()[0]
base = con.execute("""
select count(*), avg((close/prev-1>=0.10)::int)*100, avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100
from ds where prev>0 and nxt is not null and close>0""").fetchone()
print(f"기준선(전 종목-일 {base[0]}): 당일+10%↑ {base[1]:.2f}% 내일+10%↑ {base[2]:.2f}% 내일±10% {base[3]:.2f}%")
bl = con.execute("""
select count(*)*1.0/?, avg((close/prev-1>=0.10)::int)*100, avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100
from ds where prev>0 and nxt is not null and close>0 and amt>=10000""", [tot_days]).fetchone()
print(f"기준선(일 거래대금 100억↑ 종목, 하루 {bl[0]:.0f}개): 당일+10%↑ {bl[1]:.2f}% 내일+10%↑ {bl[2]:.2f}% 내일±10% {bl[3]:.2f}%")
tot_up1 = con.execute("select sum((nxt/close-1>=0.10)::int) from ds where prev>0 and nxt is not null and close>0").fetchone()[0]
tot_dayup = con.execute("select sum((close/prev-1>=0.10)::int) from ds where prev>0 and nxt is not null and close>0").fetchone()[0]

print("\n== 급증 조건별: 첫 급증 분 기준 (종목-일당 1건) ==")
print("배수 최소금액(백만) | 하루종목수 | 급증시점까지 이미 등락 | 급증 후 종가까지 평균 | 상승비율 | 당일+10%↑ | 내일+10%↑ | 내일±10% | 내일+10%포착")
for M in (5, 10, 20):
    for A in (500, 1000, 3000):
        r = con.execute(f"""
        with f as (
          select c.code, c.d, min(c.ts) ts, count(*) nsp from cand c
          where c.amt >= {A} and (c.base = 0 or c.amt >= {M} * c.base) group by 1, 2
        ), j as (
          select f.code, f.d, f.nsp, ds.close, ds.prev, ds.nxt, k.c as c_sp from f
          join cand k on k.code=f.code and k.d=f.d and k.ts=f.ts
          join ds on ds.code=f.code and ds.d=f.d
          where ds.prev>0 and ds.nxt is not null and ds.close>0
        )
        select count(*)*1.0/{tot_days}, avg(c_sp/prev-1)*100, avg(close/c_sp-1)*100,
               avg((close>c_sp)::int)*100, avg((close/prev-1>=0.10)::int)*100,
               avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100,
               sum((nxt/close-1>=0.10)::int)*100.0/{tot_up1}
        from j""").fetchone()
        print(f"{M}배 {A:>5} | {r[0]:6.1f} | {r[1]:+6.2f}% | {r[2]:+6.2f}% | {r[3]:5.1f}% | {r[4]:5.2f}% | {r[5]:5.2f}% | {r[6]:5.2f}% | {r[7]:5.1f}%")

print("\n== 연속 분 수(급증 분 개수), 10배·1000백만 ==")
for lo, hi in ((1, 1), (2, 2), (3, 99)):
    r = con.execute(f"""
    with f as (
      select c.code, c.d, min(c.ts) ts, count(*) nsp from cand c
      where c.amt >= 1000 and (c.base = 0 or c.amt >= 10 * c.base) group by 1, 2
      having count(*) between {lo} and {hi}
    ), j as (
      select f.code, f.d, ds.close, ds.prev, ds.nxt, k.c as c_sp from f
      join cand k on k.code=f.code and k.d=f.d and k.ts=f.ts
      join ds on ds.code=f.code and ds.d=f.d
      where ds.prev>0 and ds.nxt is not null and ds.close>0
    )
    select count(*)*1.0/{tot_days}, avg(close/c_sp-1)*100, avg((close/prev-1>=0.10)::int)*100,
           avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100 from j""").fetchone()
    print(f"급증 {lo}~{hi if hi<99 else '+'}분 | 하루 {r[0]:.1f} | 급증 후 종가 {r[1]:+.2f}% | 당일+10%↑ {r[2]:.2f}% | 내일+10%↑ {r[3]:.2f}% | 내일±10% {r[4]:.2f}%")

print("\n== 급증 시각별, 10배·1000백만 ==")
for nm, lo, hi in (("09:30~10:59", "09:30", "10:59"), ("11:00~12:59", "11:00", "12:59"), ("13:00~15:29", "13:00", "15:29")):
    r = con.execute(f"""
    with f as (
      select c.code, c.d, min(c.ts) ts from cand c
      where c.amt >= 1000 and (c.base = 0 or c.amt >= 10 * c.base) group by 1, 2
    ), j as (
      select f.code, f.d, ds.close, ds.prev, ds.nxt, k.c as c_sp, f.ts from f
      join cand k on k.code=f.code and k.d=f.d and k.ts=f.ts
      join ds on ds.code=f.code and ds.d=f.d
      where ds.prev>0 and ds.nxt is not null and ds.close>0
        and cast(f.ts as time) between time '{lo}' and time '{hi}'
    )
    select count(*)*1.0/{tot_days}, avg(close/c_sp-1)*100, avg((close/prev-1>=0.10)::int)*100,
           avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100 from j""").fetchone()
    print(f"{nm} | 하루 {r[0]:.1f} | 급증 후 종가 {r[1]:+.2f}% | 당일+10%↑ {r[2]:.2f}% | 내일+10%↑ {r[3]:.2f}% | 내일±10% {r[4]:.2f}%")

print("\n== 급증 시점에 이미 얼마나 올랐나(전일 종가 대비), 10배·1000백만 ==")
for nm, lo, hi in (("-5% 미만", -9, -0.05), ("-5~0%", -0.05, 0), ("0~5%", 0, 0.05), ("5~15%", 0.05, 0.15), ("15% 이상", 0.15, 9)):
    r = con.execute(f"""
    with f as (
      select c.code, c.d, min(c.ts) ts from cand c
      where c.amt >= 1000 and (c.base = 0 or c.amt >= 10 * c.base) group by 1, 2
    ), j as (
      select f.code, f.d, ds.close, ds.prev, ds.nxt, k.c as c_sp from f
      join cand k on k.code=f.code and k.d=f.d and k.ts=f.ts
      join ds on ds.code=f.code and ds.d=f.d
      where ds.prev>0 and ds.nxt is not null and ds.close>0
        and k.c/ds.prev-1 >= {lo} and k.c/ds.prev-1 < {hi}
    )
    select count(*)*1.0/{tot_days}, avg(close/c_sp-1)*100, avg((close>c_sp)::int)*100, avg((close/prev-1>=0.10)::int)*100,
           avg((nxt/close-1>=0.10)::int)*100, avg((abs(nxt/close-1)>=0.10)::int)*100 from j""").fetchone()
    print(f"{nm:8s} | 하루 {r[0]:.1f} | 급증 후 종가 {r[1]:+.2f}% | 상승비율 {r[2]:.1f}% | 당일+10%↑ {r[3]:.2f}% | 내일+10%↑ {r[4]:.2f}% | 내일±10% {r[5]:.2f}%")
print(f"\n총 {time.time()-t0:.0f}s")

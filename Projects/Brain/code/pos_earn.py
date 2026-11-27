"""기준봉(500억·고가+15%·고저+15%·몸통+9%) × 위치(240/480선) × 실적(신호일 전에 공시된 최근 두 분기) 비교. 읽기 전용."""
import csv
import json
from datetime import date, datetime
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
d = json.loads((HERE / "op.json").read_text(encoding="utf-8"))
cmap, op = d["map"], d["op"]


def quarters(cc):
    r = op.get(cc, {})
    qs = []
    for k in ("25Q1", "25Q2", "25Q3"):
        if k in r and r[k]["cur"] is not None:
            qs.append((k, r[k]["cur"], r[k]["prev"], r[k]["date"]))
    if "25FY" in r and "25Q3" in r and None not in (r["25FY"]["cur"], r["25Q3"]["cur_add"]):
        prev = None if None in (r["25FY"]["prev"], r["25Q3"]["prev_add"]) else r["25FY"]["prev"] - r["25Q3"]["prev_add"]
        qs.append(("25Q4", r["25FY"]["cur"] - r["25Q3"]["cur_add"], prev, r["25FY"]["date"]))
    for k in ("26Q1", "26Q2", "26Q3"):
        if k in r and r[k]["cur"] is not None:
            qs.append((k, r[k]["cur"], r[k]["prev"], r[k]["date"]))
    return qs


def earn(code, day):
    cc = cmap.get(code)
    if not cc:
        return "자료없음", ""
    ds = day.strftime("%Y%m%d")
    av = [q for q in quarters(cc) if q[3] and q[3] < ds]
    if len(av) < 2:
        return "자료없음", ""
    last = av[-2:]
    good = all(cur > 0 and (prev is None or prev <= 0 or cur > prev) for _, cur, prev, _ in last)
    txt = " / ".join(f"{k} {cur:.0f}억" + (f"({cur / prev - 1:+.0%})" if prev and prev > 0 else "(흑전)" if prev is not None and prev <= 0 and cur > 0 else "")
                     for k, cur, prev, _ in last)
    return ("좋음" if good else "나쁨"), txt


c = duckdb.connect("C:/Users/Jinwo/Documents/storage/data/storage.duckdb", read_only=True)
c.execute("""create temp table b as select d.code, s.name, d.date, d.open, d.high, d.low, d.close, d.amount_est amt, m.ma240, m.ma480,
  lag(d.close) over w pc, lag(m.ma240) over w p240, lag(m.ma480) over w p480,
  lead(d.close, 20) over w c20,
  max(d.close) over (partition by d.code order by d.date rows between 1 following and 40 following) mx40,
  min(d.close) over (partition by d.code order by d.date rows between 1 following and 40 following) mn40,
  last_value(d.close) over (partition by d.code order by d.date rows between unbounded preceding and unbounded following) now
  from daily_bar d join stocks s using(code) left join ma_daily m using(code, date)
  where d.venue='KRX_REG' and d.adjusted and d.date>='2025-10-01' window w as (partition by d.code order by d.date)""")
c.execute("""create temp table x as select *,
  max(((pc<=p240 and close>ma240) or (pc<=p480 and close>ma480))::int) over (partition by code order by date rows between 5 preceding and current row) cross5
  from b""")
rows = c.execute("""select code, name, date, close, amt, ma240, ma480, cross5, c20, mx40, mn40, now from x
  where date>='2025-11-01' and amt>=50000 and high>=pc*1.15 and high>=low*1.15 and close>=open*1.09 order by date""").fetchall()


def position(close, m240, m480, cross5):
    if m240 is None and m480 is None:
        return "판단불가"
    if cross5:
        return "돌파"
    near = any(m and 0 <= close / m - 1 <= 0.10 for m in (m240, m480))
    return "주변" if near else "아님"


groups, listing = {}, []
for code, name, day, close, amt, m240, m480, cross5, c20, mx40, mn40, now in rows:
    pos = position(close, m240, m480, cross5)
    e, etxt = earn(code, day)
    g = ("위치O" if pos in ("돌파", "주변") else "위치X" if pos == "아님" else "위치?") + "·" + ("실적O" if e == "좋음" else "실적X" if e == "나쁨" else "실적?")
    rec = dict(code=code, name=name, date=day, close=close, amt=amt / 100, pos=pos, earn=etxt,
               r20=(c20 / close - 1) if c20 else None, up40=(mx40 / close - 1) if mx40 else None,
               dn40=(mn40 / close - 1) if mn40 else None, now=now / close - 1)
    groups.setdefault(g, []).append(rec)
    if g == "위치O·실적O":
        listing.append(rec)


def stat(rs):
    v = [r for r in rs if r["r20"] is not None]
    if not v:
        return f"{len(rs)}건 (20일 지난 것 없음)"
    avg = lambda k: sum(r[k] for r in v) / len(v)
    return (f"{len(rs)}건 | 20일 뒤 {len(v)}건: 상승 {sum(r['r20'] > 0 for r in v) / len(v):.0%}, 평균 {avg('r20'):+.1%}, "
            f"40일 최고 평균 {avg('up40'):+.0%}, 최저 평균 {avg('dn40'):+.0%}, 40일 내 +30% 도달 {sum(r['up40'] >= 0.3 for r in v) / len(v):.0%}")


for g in ("위치O·실적O", "위치O·실적X", "위치X·실적O", "위치X·실적X", "위치?·실적O", "위치O·실적?"):
    if g in groups:
        print(g, stat(groups[g]))
print("기타:", {g: len(v) for g, v in groups.items() if g not in ("위치O·실적O", "위치O·실적X", "위치X·실적O", "위치X·실적X", "위치?·실적O", "위치O·실적?")})
print("\n위치O·실적O 중 돌파만:", stat([r for r in listing if r["pos"] == "돌파"]))
print("위치O·실적O 중 주변만:", stat([r for r in listing if r["pos"] == "주변"]))
with open(HERE / "pos_earn_list.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(listing[0].keys()))
    w.writeheader()
    w.writerows(listing)
print("\n목록 저장:", HERE / "pos_earn_list.csv", len(listing), "건")
for r in listing:
    f = lambda x: f"{x:+.0%}" if x is not None else "  -"
    print(f"{r['date']} {r['name']:10s} {r['pos']} {r['amt']:.0f}억 | {r['earn']} | 20일 {f(r['r20'])} 40일최고 {f(r['up40'])} 최저 {f(r['dn40'])} 현재 {f(r['now'])}")

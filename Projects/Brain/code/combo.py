"""기준봉 × 시총비율 30~50% × 위치(선 근처 -5~+15%) × 실적. 읽기 전용."""
import csv
import json
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
d = json.loads((HERE / "op.json").read_text(encoding="utf-8"))
cmap, op = d["map"], d["op"]


def quarters(cc):
    r = op.get(cc, {})
    qs = [(k, r[k]["cur"], r[k]["prev"], r[k]["date"]) for k in ("25Q1", "25Q2", "25Q3") if k in r and r[k]["cur"] is not None]
    if "25FY" in r and "25Q3" in r and None not in (r["25FY"]["cur"], r["25Q3"]["cur_add"]):
        prev = None if None in (r["25FY"]["prev"], r["25Q3"]["prev_add"]) else r["25FY"]["prev"] - r["25Q3"]["prev_add"]
        qs.append(("25Q4", r["25FY"]["cur"] - r["25Q3"]["cur_add"], prev, r["25FY"]["date"]))
    qs += [(k, r[k]["cur"], r[k]["prev"], r[k]["date"]) for k in ("26Q1", "26Q2", "26Q3") if k in r and r[k]["cur"] is not None]
    return qs


def earn(code, day):
    cc = cmap.get(code)
    if not cc:
        return None, ""
    av = [q for q in quarters(cc) if q[3] and q[3] < day.strftime("%Y%m%d")]
    if len(av) < 2:
        return None, ""
    last = av[-2:]
    good = all(cur > 0 and (prev is None or prev <= 0 or cur > prev) for _, cur, prev, _ in last)
    txt = " / ".join(f"{k} {cur:.0f}억" + (f"({cur / prev - 1:+.0%})" if prev and prev > 0 else "(흑전)" if prev is not None and prev <= 0 and cur > 0 else "")
                     for k, cur, prev, _ in last)
    return good, txt


c = duckdb.connect("C:/Users/Jinwo/Documents/storage/data/storage.duckdb", read_only=True)
c.execute("""create temp table b as select d.code, s.name, d.date, d.open, d.high, d.low, d.close, d.amount_est amt, m.ma240, m.ma480,
  lag(d.close) over w pc, lag(m.ma240) over w p240, lag(m.ma480) over w p480, lead(d.close, 20) over w c20,
  max(d.close) over (partition by d.code order by d.date rows between 1 following and 40 following) mx40,
  min(d.close) over (partition by d.code order by d.date rows between 1 following and 40 following) mn40,
  last_value(d.close) over (partition by d.code order by d.date rows between unbounded preceding and unbounded following) now
  from daily_bar d join stocks s using(code) left join ma_daily m using(code, date)
  where d.venue='KRX_REG' and d.adjusted and d.date>='2025-10-01' window w as (partition by d.code order by d.date)""")
c.execute("""create temp table x as select *,
  max(((pc<=p240 and close>ma240) or (pc<=p480 and close>ma480))::int) over (partition by code order by date rows between 5 preceding and current row) cross5
  from b""")
rows = c.execute("""select x.code, name, x.date, close, amt, ma240, ma480, cross5, c20, mx40, mn40, now, k.krx_amount*1.0/k.krx_mktcap r
  from x join krx_daily k on k.code=x.code and k.date=x.date
  where x.date>='2025-11-01' and amt>=50000 and high>=pc*1.15 and high>=low*1.15 and close>=open*1.09 and k.krx_mktcap>0""").fetchall()

recs = []
for code, name, day, close, amt, m240, m480, cross5, c20, mx40, mn40, now, r in rows:
    g240 = close / m240 - 1 if m240 else None
    g480 = close / m480 - 1 if m480 else None
    near = any(g is not None and -0.05 <= g <= 0.15 for g in (g240, g480))
    good, etxt = earn(code, day)
    recs.append(dict(code=code, name=name, date=day, amt=amt / 100, ratio=r, g240=g240, g480=g480, near=near, cross5=bool(cross5),
                     good=good, earn=etxt, r20=(c20 / close - 1) if c20 else None, up40=mx40 / close - 1 if mx40 else None,
                     dn40=mn40 / close - 1 if mn40 else None, now=now / close - 1))


def stat(v, lab):
    t = [x for x in v if x["r20"] is not None]
    if not t:
        print(f"{lab}: {len(v)}건 (20일 지난 것 없음)")
        return
    a = lambda k, s=t: sum(x[k] for x in s) / len(s)
    print(f"{lab}: {len(v)}건 | 20일 뒤 {len(t)}건 상승 {sum(x['r20'] > 0 for x in t) / len(t):.0%} 평균 {a('r20'):+.1%} "
          f"| 40일 최고 평균 {a('up40'):+.0%} 최저 평균 {a('dn40'):+.0%} +30%도달 {sum(x['up40'] >= 0.3 for x in t) / len(t):.0%} "
          f"| 현재까지 평균 {a('now', v):+.0%} 상승 {sum(x['now'] > 0 for x in v)}건")


R = lambda x: x["ratio"] is not None and 0.3 <= x["ratio"] < 0.5
stat(recs, "기준봉 전체")
stat([x for x in recs if R(x)], "① 시총비율 30~50%")
stat([x for x in recs if R(x) and x["near"]], "② ① + 위치(240/480선 -5~+15%)")
stat([x for x in recs if R(x) and x["good"]], "③ ① + 실적")
stat([x for x in recs if x["near"] and x["good"]], "④ 위치 + 실적 (비율 무관)")
final = [x for x in recs if R(x) and x["near"] and x["good"]]
stat(final, "⑤ ① + 위치 + 실적")
stat([x for x in final if x["cross5"]], "⑥ ⑤ 중 5일 내 돌파도 있음")

path = HERE / "기준봉_비율위치실적.csv"
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["기준봉일", "종목", "코드", "거래대금(억)", "시총비율", "240선 대비", "480선 대비", "5일내 돌파", "실적", "20일 뒤", "40일 최고", "40일 최저", "현재까지"])
    p = lambda v: f"{v:+.0%}" if v is not None else "-"
    for x in sorted(final, key=lambda x: x["date"]):
        w.writerow([x["date"], x["name"], x["code"], round(x["amt"]), f"{x['ratio']:.0%}", p(x["g240"]), p(x["g480"]), "O" if x["cross5"] else "",
                    x["earn"], p(x["r20"]), p(x["up40"]), p(x["dn40"]), p(x["now"])])
        print(f"{x['date']} {x['name']:10s} 비율 {x['ratio']:.0%} 240 {p(x['g240'])} 480 {p(x['g480'])} {'돌파' if x['cross5'] else '    '} | {x['earn']} | 20일 {p(x['r20'])} 최고 {p(x['up40'])} 최저 {p(x['dn40'])} 현재 {p(x['now'])}")
print(path)

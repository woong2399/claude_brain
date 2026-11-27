"""9/14 기준봉 종목 + 모니터랩: 종목마다 사건 기준 기간으로 수급·위치·실적을 항목별로 본다 (읽기 전용).
기준점: 지니언스(좋은 예), 모니터랩(같은 재료, 실적 악화). 문턱값은 초안이다.
"""
import json
import urllib.parse
import urllib.request
from datetime import date

import duckdb

DB = "C:/Users/Jinwo/Documents/storage/data/storage.duckdb"
ENV = "C:/Users/Jinwo/Documents/assistant/news/.env"
D = date(2026, 9, 14)
NAMES = ["지니언스", "모니터랩", "라온시큐어", "샌즈랩", "빛샘전자", "티엠씨", "삼익제약", "광전자", "빛과전자"]

c = duckdb.connect(DB, read_only=True)
KEY = [l.split("=", 1)[1].strip() for l in open(ENV, encoding="utf-8-sig") if l.startswith("DART_API_KEY=")][0]


def dart(path, **q):
    q["crtfc_key"] = KEY
    return json.loads(urllib.request.urlopen("https://opendart.fss.or.kr/api/" + path + "?" + urllib.parse.urlencode(q), timeout=30).read())


def corp_codes(stock_codes):
    """8/10~8/18 정기공시(반기보고서) 목록에서 종목코드 → corp_code."""
    out, page = {}, 1
    while True:
        d = dart("list.json", bgn_de="20260810", end_de="20260818", pblntf_ty="A", page_no=page, page_count=100)
        for r in d.get("list", []):
            if r.get("stock_code") in stock_codes:
                out[r["stock_code"]] = r["corp_code"]
        if page >= d.get("total_page", 1) or len(out) == len(stock_codes):
            return out
        page += 1


def op_income(corp):
    """영업이익(억): 26.1Q, 26.2Q, 전년 같은 분기. 9/14 이전에 나온 반기까지만."""
    res = {}
    for yr, code, k in ((2026, "11013", "q1"), (2026, "11012", "q2")):
        f = dart("fnlttSinglAcnt.json", corp_code=corp, bsns_year=str(yr), reprt_code=code)
        rows = {(x["fs_div"], x["account_nm"]): x for x in f.get("list", [])}
        x = rows.get(("CFS", "영업이익")) or rows.get(("OFS", "영업이익"))
        if x:
            n = lambda v: int(str(v).replace(",", "")) / 1e8 if v not in (None, "", "-") else None
            res[k] = (n(x["thstrm_amount"]), n(x["frmtrm_amount"]))
    return res


def judge_op(res):
    tags = []
    for k, lab in (("q1", "1Q"), ("q2", "2Q")):
        if k not in res or res[k][0] is None:
            tags.append(f"{lab} 없음")
            continue
        cur, prev = res[k]
        if cur < 0:
            tags.append(f"{lab} 적자 {cur:.1f}억")
        elif prev is not None and prev <= 0:
            tags.append(f"{lab} 흑자전환 {cur:.1f}억")
        elif prev:
            tags.append(f"{lab} {cur:.1f}억({cur / prev - 1:+.0%})")
    good = sum(("흑자전환" in t) or ("(+" in t) for t in tags)
    bad = sum(("적자" in t) or ("(-" in t) for t in tags)
    return ("좋음" if good == 2 else "나쁨" if bad >= 1 and good == 0 else "섞임"), " / ".join(tags)


def bars(code):
    return c.execute("""select d.date, d.close, d.amount_est amt, m.ma240, m.ma480,
        avg(d.amount_est) over (order by d.date rows between 20 preceding and 1 preceding) avg20
        from daily_bar d left join ma_daily m using(code, date)
        where d.code=? and d.venue='KRX_REG' and d.adjusted and d.date between '2026-05-01' and '2026-10-15' order by d.date""", [code]).fetchall()


def anchor(rows):
    """기준일: 9/14 가 기준봉이면 9/14, 아니면 9/1~9/30 중 거래대금 최대일."""
    sep = [r for r in rows if date(2026, 9, 1) <= r[0] <= date(2026, 9, 30)]
    if any(r[0] == D for r in sep):
        return D
    return max(sep, key=lambda r: r[2] or 0)[0]


def start_of_move(rows, a):
    """기준일 전 40거래일 안에서 처음으로 거래대금이 평소 5배 이상 된 날. 없으면 기준일."""
    before = [r for r in rows if r[0] < a][-40:]
    for r in before:
        if r[2] and r[5] and r[2] >= r[5] * 5:
            return r[0]
    return a


def window_sum(code, a, b):
    return c.execute("""select sum(individual), sum(foreign_inv), sum(institution), sum(private_fund)+sum(trust)+sum(pension_etc)
        from investor_flow where code=? and date between ? and ?""", [code, a, b]).fetchone()


def amt_sum(code, a, b):
    return c.execute("select sum(amount_est) from daily_bar where code=? and venue='KRX_REG' and adjusted and date between ? and ?",
                     [code, a, b]).fetchone()[0] or 0


def tag(v, base, applicable=True):
    if not applicable:
        return "해당없음"
    if v is None or not base:
        return "자료없음"
    r = v / base
    return f"매수 {r:+.1%}" if r >= 0.01 else f"매도 {r:+.1%}" if r <= -0.01 else f"약함 {r:+.1%}"


codes = dict(c.execute(f"select name, code from stocks where name in ({','.join('?' * len(NAMES))})", NAMES).fetchall())
cc = corp_codes(set(codes.values()))
for name in NAMES:
    code = codes[name]
    rows = bars(code)
    a = anchor(rows)
    s = start_of_move(rows, a)
    dates = [r[0] for r in rows]
    i_s = dates.index(s)
    pre_a, pre_b = dates[max(0, i_s - 20)], dates[i_s - 1]  # 움직이기 전 조용한 20거래일
    mid_b = dates[dates.index(a) - 1]
    ar = rows[dates.index(a)]
    fr = c.execute("select hold_ratio from foreign_holding where code=? and date<=? order by date desc limit 1", [code, pre_b]).fetchone()
    fr = fr[0] if fr else None
    frn_ok = fr is not None and fr >= 5  # 외국인 지분 5% 미만이면 외국인 항목은 보지 않는다
    pre, mid = window_sum(code, pre_a, pre_b), (window_sum(code, s, mid_b) if s < a else None)
    pre_amt, mid_amt = amt_sum(code, pre_a, pre_b), (amt_sum(code, s, mid_b) if s < a else 0)
    lq = "select balance_qty from loan_trading where code=? and date<=? order by date desc limit 1"
    loan = tuple((c.execute(lq, [code, d]).fetchone() or [None])[0] for d in (pre_a, mid_b))
    shrs = c.execute("select krx_list_shrs from krx_daily where code=? and date<=? order by date desc limit 1", [code, a]).fetchone()
    loan_tag = "자료없음"
    if loan[0] and loan[1] is not None and shrs:
        if loan[0] / shrs[0] < 0.005:
            loan_tag = "해당없음(잔고 작음)"
        else:
            ch = loan[1] / loan[0] - 1
            loan_tag = f"감소 {ch:+.0%}" if ch <= -0.03 else f"증가 {ch:+.0%}" if ch >= 0.03 else f"변화없음 {ch:+.0%}"
    pos = []
    for lab, ma in (("240", ar[3]), ("480", ar[4])):
        if ma:
            gap = ar[1] / ma - 1
            crossed = any(r[3 if lab == "240" else 4] and rows[k - 1][1] <= rows[k - 1][3 if lab == "240" else 4] < r[1]
                          for k, r in enumerate(rows) if k and 0 <= dates.index(a) - k <= 5)
            pos.append(f"{lab}선 {gap:+.0%}" + (" (5일내 돌파)" if crossed else ""))
    op = judge_op(op_income(cc[code])) if code in cc else ("자료없음", "corp_code 못 찾음")
    later = c.execute("""select (select close from daily_bar where code=? and venue='KRX_REG' and adjusted order by date desc limit 1)""", [code]).fetchone()[0]
    print(f"\n■ {name} ({code})  기준일 {a} 종가 {ar[1]:,} 거래대금 {ar[2] / 100 if ar[2] else 0:.0f}억 | 현재까지 {later / ar[1] - 1:+.0%}")
    print(f"  위치: {', '.join(pos) or '이동평균 없음(일봉 240일 미만, 신규상장 등)'}")
    print(f"  실적: {op[0]} — {op[1]}")
    print(f"  움직임 시작 {s}" + ("" if s < a else " (기준일 당일 처음)") + f" | 외국인 지분 {fr}%")
    print(f"  조용한 구간 {pre_a}~{pre_b}: 기관 {tag(pre[2], pre_amt)} · 외국인 {tag(pre[1], pre_amt, frn_ok)} · 개인 {tag(pre[0], pre_amt)} · 사모투신연기금 {tag(pre[3], pre_amt)}")
    if mid:
        print(f"  시작~기준일 전 {s}~{mid_b}: 기관 {tag(mid[2], mid_amt)} · 외국인 {tag(mid[1], mid_amt, frn_ok)} · 개인 {tag(mid[0], mid_amt)} · 사모투신연기금 {tag(mid[3], mid_amt)}")
    print(f"  대차잔고({pre_a}→{mid_b}): {loan_tag}")

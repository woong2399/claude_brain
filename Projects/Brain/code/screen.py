"""실적 선행 근거로 종목 뽑기 (읽기 전용, 2026-11-17 기준).
1) 실적: 26Q3 영업이익 흑자 + 전년비 증가/흑전 + 26Q3 > 26Q2(가속) + 26Q2 도 전년비 증가/흑전
2) 수주·공급계약, 신규시설투자 공시 (최근 6개월, DART 목록)
3) 계약부채(선수금): 26Q3 말 vs 25년 말 (후보만, 재무제표 전체 조회)
4) 참고: 시총, 240선 대비, 최근 60일 평균 거래대금, 시총/영업이익(최근 4분기)
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

HERE = Path(__file__).parent
ENV = "C:/Users/Jinwo/Documents/assistant/news/.env"
KEY = [l.split("=", 1)[1].strip() for l in open(ENV, encoding="utf-8-sig") if l.startswith("DART_API_KEY=")][0]
d = json.loads((HERE / "op.json").read_text(encoding="utf-8"))
cmap, op = d["map"], d["op"]
inv = {v: k for k, v in cmap.items()}


def get(path, **q):
    q["crtfc_key"] = KEY
    for _ in range(3):
        try:
            return json.loads(urllib.request.urlopen("https://opendart.fss.or.kr/api/" + path + "?" + urllib.parse.urlencode(q), timeout=60).read())
        except Exception:
            time.sleep(3)
    return {}


def up(cur, prev):
    return cur is not None and cur > 0 and (prev is None or prev <= 0 or cur > prev)


# 1) 실적
cands = {}
for cc, r in op.items():
    q3, q2 = r.get("26Q3"), r.get("26Q2")
    if not q3 or not q2 or q3["cur"] is None or q2["cur"] is None:
        continue
    if up(q3["cur"], q3["prev"]) and up(q2["cur"], q2["prev"]) and q3["cur"] > q2["cur"]:
        ttm = None
        q1 = r.get("26Q1")
        fy, q3_25 = r.get("25FY"), r.get("25Q3")
        if q1 and fy and q3_25 and None not in (q1["cur"], fy["cur"], q3_25["cur_add"]):
            ttm = q3["cur"] + q2["cur"] + q1["cur"] + (fy["cur"] - q3_25["cur_add"])
        cands[cc] = dict(q3=q3["cur"], q3p=q3["prev"], q2=q2["cur"], q2p=q2["prev"], ttm=ttm)
print("실적 통과:", len(cands), file=sys.stderr)

# 2) 공시 목록 (거래소 수시공시 I, 주요사항 B), 3개월씩 두 번
keys = {"수주": ("단일판매", "공급계약"), "시설투자": ("신규시설투자", "유형자산양수")}
disc = {}
for bgn, end in (("20260518", "20260816"), ("20260817", "20261117")):
    for ty in ("I", "B"):
        page = 1
        while True:
            res = get("list.json", bgn_de=bgn, end_de=end, pblntf_ty=ty, page_no=page, page_count=100)
            for x in res.get("list", []):
                nm = x.get("report_nm", "")
                if "정정" in nm or "해지" in nm:
                    continue
                for k, words in keys.items():
                    if any(w in nm for w in words):
                        disc.setdefault(x["corp_code"], {}).setdefault(k, []).append(x["rcept_dt"])
            if page >= res.get("total_page", 1):
                break
            page += 1
            time.sleep(0.1)
        print("공시", bgn, ty, page, "쪽", file=sys.stderr)

# 3) 계약부채
for cc in cands:
    res = get("fnlttSinglAcntAll.json", corp_code=cc, bsns_year="2026", reprt_code="11014", fs_div="CFS")
    if res.get("status") != "000":
        res = get("fnlttSinglAcntAll.json", corp_code=cc, bsns_year="2026", reprt_code="11014", fs_div="OFS")
    cl = None
    for x in res.get("list", []):
        if x.get("sj_div") == "BS" and x.get("account_nm", "").replace(" ", "") in ("계약부채", "유동계약부채", "선수금"):
            n = lambda v: int(str(v).replace(",", "")) / 1e8 if str(v or "").replace(",", "").lstrip("-").isdigit() else None
            cur, prev = n(x.get("thstrm_amount")), n(x.get("frmtrm_amount"))
            if cur is not None:
                cl = (cl[0] + cur, cl[1] + (prev or 0)) if cl else (cur, prev or 0)
    cands[cc]["cl"] = cl
    time.sleep(0.1)

# 4) 가격·규모
c = duckdb.connect("C:/Users/Jinwo/Documents/storage/data/storage.duckdb", read_only=True)
out = []
for cc, v in cands.items():
    code = inv.get(cc)
    if not code:
        continue
    row = c.execute("""select s.name, d.close, m.ma240,
        (select avg(amount_est) from daily_bar where code=? and venue='KRX_REG' and adjusted and date > current_date - 90) a60,
        (select krx_mktcap from krx_daily where code=? order by date desc limit 1) mcap
        from stocks s join daily_bar d on d.code=s.code and d.venue='KRX_REG' and d.adjusted
        left join ma_daily m on m.code=d.code and m.date=d.date
        where s.code=? order by d.date desc limit 1""", [code, code, code]).fetchone()
    if not row:
        continue
    name, close, ma240, a60, mcap = row
    dd = disc.get(cc, {})
    cl = v["cl"]
    cl_up = cl is not None and cl[1] > 0 and cl[0] / cl[1] - 1 >= 0.2
    score = (len(dd.get("수주", [])) > 0) + (len(dd.get("시설투자", [])) > 0) + cl_up
    out.append({
        "종목": name, "코드": code, "근거수": score,
        "26Q3 영업이익(억)": round(v["q3"], 1), "Q3 전년비": f"{v['q3'] / v['q3p'] - 1:+.0%}" if v["q3p"] and v["q3p"] > 0 else "흑전",
        "26Q2(억)": round(v["q2"], 1), "Q2 전년비": f"{v['q2'] / v['q2p'] - 1:+.0%}" if v["q2p"] and v["q2p"] > 0 else "흑전",
        "수주공시(6개월)": len(dd.get("수주", [])), "최근 수주일": max(dd.get("수주", [""])),
        "시설투자공시": len(dd.get("시설투자", [])),
        "계약부채 25말→26Q3(억)": f"{cl[1]:.0f}→{cl[0]:.0f} ({cl[0] / cl[1] - 1:+.0%})" if cl and cl[1] > 0 else (f"→{cl[0]:.0f}" if cl else "-"),
        "시총(억)": round(mcap / 1e8) if mcap else None,
        "시총/영업이익(4분기)": round(mcap / 1e8 / v["ttm"], 1) if mcap and v["ttm"] and v["ttm"] > 0 else None,
        "240선 대비": f"{close / ma240 - 1:+.0%}" if ma240 else "-",
        "최근 3개월 평균 거래대금(억)": round(a60 / 100, 1) if a60 else None,
    })
out.sort(key=lambda x: (-x["근거수"], x["시총/영업이익(4분기)"] or 999))
path = HERE / "실적선행_후보.csv"
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("후보", len(out), "근거 3개", sum(x["근거수"] == 3 for x in out), "2개", sum(x["근거수"] == 2 for x in out), "1개", sum(x["근거수"] == 1 for x in out))
for x in out[:45]:
    print(" | ".join(str(v) for v in x.values()))
print(path)

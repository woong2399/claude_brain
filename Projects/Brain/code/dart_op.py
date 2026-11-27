"""DART 분기 영업이익을 전 종목 받아 scratchpad 의 op.json 에 캐시한다 (읽기 전용 API).
분기별: (영업이익, 전년 같은 분기, 공시일). 4분기는 사업보고서 - 3분기 누적.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).with_name("op.json")
ENV = "C:/Users/Jinwo/Documents/assistant/news/.env"
KEY = [l.split("=", 1)[1].strip() for l in open(ENV, encoding="utf-8-sig") if l.startswith("DART_API_KEY=")][0]


def get(path, **q):
    q["crtfc_key"] = KEY
    for i in range(3):
        try:
            return json.loads(urllib.request.urlopen("https://opendart.fss.or.kr/api/" + path + "?" + urllib.parse.urlencode(q), timeout=60).read())
        except Exception as e:
            print("retry", path, type(e).__name__, file=sys.stderr)
            time.sleep(3)
    return {}


def corp_map():
    """정기공시 목록(반기·3분기·사업보고서 기간)에서 상장사 stock_code → corp_code."""
    m = {}
    for bgn, end in (("20260801", "20260818"), ("20251101", "20251118"), ("20260310", "20260331")):
        page = 1
        while True:
            d = get("list.json", bgn_de=bgn, end_de=end, pblntf_ty="A", corp_cls="Y", page_no=page, page_count=100)
            d2 = None
            for r in d.get("list", []):
                if r.get("stock_code"):
                    m[r["stock_code"]] = r["corp_code"]
            if page >= d.get("total_page", 1):
                break
            page += 1
        page = 1
        while True:
            d = get("list.json", bgn_de=bgn, end_de=end, pblntf_ty="A", corp_cls="K", page_no=page, page_count=100)
            for r in d.get("list", []):
                if r.get("stock_code"):
                    m[r["stock_code"]] = r["corp_code"]
            if page >= d.get("total_page", 1):
                break
            page += 1
        print("corp map", bgn, len(m), file=sys.stderr)
    return m


def n(v):
    s = str(v or "").replace(",", "").strip()
    return int(s) / 1e8 if s not in ("", "-") else None


def fetch(corps):
    """{corp: {report_key: {'cur','prev','cur_add','prev_add','date'}}}"""
    reps = [(2025, "11013", "25Q1"), (2025, "11012", "25Q2"), (2025, "11014", "25Q3"), (2025, "11011", "25FY"),
            (2026, "11013", "26Q1"), (2026, "11012", "26Q2"), (2026, "11014", "26Q3")]
    out = {}
    cl = sorted(corps)
    for yr, code, key in reps:
        for i in range(0, len(cl), 100):
            d = get("fnlttMultiAcnt.json", corp_code=",".join(cl[i:i + 100]), bsns_year=str(yr), reprt_code=code)
            best = {}
            for r in d.get("list", []):
                if r.get("account_nm") != "영업이익":
                    continue
                prev = best.get(r["corp_code"])
                if prev and prev["fs_div"] == "CFS":
                    continue  # 연결 우선
                best[r["corp_code"]] = r
            for cc, r in best.items():
                out.setdefault(cc, {})[key] = {"cur": n(r.get("thstrm_amount")), "prev": n(r.get("frmtrm_amount")),
                                               "cur_add": n(r.get("thstrm_add_amount")), "prev_add": n(r.get("frmtrm_add_amount")),
                                               "date": str(r.get("rcept_no", ""))[:8], "fs": r["fs_div"]}
            time.sleep(0.2)
        print("fetched", key, sum(key in v for v in out.values()), file=sys.stderr)
    return out


if __name__ == "__main__":
    m = corp_map()
    data = fetch(set(m.values()))
    OUT.write_text(json.dumps({"map": m, "op": data}, ensure_ascii=False), encoding="utf-8")
    print("saved", len(m), len(data))

"""시트 값(JSON) + 텔레그램 글 -> 옵시디언 일지 한 날짜분.

py sheet_to_journal.py            시험(파일을 쓰지 않고 결과를 scratchpad 에만 저장)
py sheet_to_journal.py --apply    보관함에 쓴다 (기존 일지는 먼저 백업)
"""
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

HERE = Path(__file__).resolve().parent
VAULT = Path(r"C:\Users\Jinwo\Documents\Obsidian\Daily")
DAY = next((a for a in sys.argv[1:] if not a.startswith("--")), "2026-11-02")
MD = DAY[5:].replace("-", "")   # 2026-11-03 -> 1103
APPLY = "--apply" in sys.argv

STOCK_NOTE = '''---
코드: "{code}"
---
## 정보
- 주요 사업:
- 시가총액:
- 메모:

## 날짜별 이슈
```query
path:일지 "[[{title}]]"
```
'''
THEME_NOTE = '''---
tags:
  - 테마
---
## 테마 설명
-

## 종목 · 급등 기록
```query
path:일지 "[[{title}]]"
```
'''


def norm_code(c):
    c = str(c).strip()
    return c.zfill(6) if c.isdigit() else c


def norm_text(s):
    return re.sub(r"[\s·/]", "", s)


def clean_url(u):
    u = u.strip()
    if not u:
        return ""
    p = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    u = urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
    return u.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def clean_headline(h):
    return re.sub(r"\s+", " ", h.strip()).replace("[", "(").replace("]", ")")


tele = {}
text = (HERE / f"telegram_{MD}.txt").read_text(encoding="utf-8")
for m in re.finditer(r"^(?P<name>[^\n]+)\n\((?P<code>[0-9A-Za-z]+)\)\n\(\+?(?P<pct>[\d.]+)%\)[ \t]*\n(?P<text>[^\n]+)", text, re.M):
    tele[norm_code(m["code"])] = {"name": m["name"].strip(), "pct": float(m["pct"]), "text": m["text"].strip()}

rows = json.loads((HERE / f"sheet_{MD}.json").read_text(encoding="utf-8"))

report = []
lines, h_col, themes_all, stocks_all = [], [], [], []
used_tele = set()
code_fix, pct_fill, no_tele, theme_mismatch, theme_unknown = [], [], [], [], []

for r in rows:
    r = [str(x) for x in r] + [""] * (7 - len(r))
    _, code0, name, pct, theme, headline, link = r[:7]
    code, name = norm_code(code0), name.strip()
    if code != code0.strip():
        code_fix.append(f"{name}: {code0} -> {code}")
    t = tele.get(code)
    if t:
        used_tele.add(code)
    if pct.strip():
        pctv = float(pct)
    elif t:
        pctv = t["pct"]
        pct_fill.append(f"{name}: 등락률 비어 있음 -> 텔레그램 {pctv}% 사용")
    else:
        pctv = None
        pct_fill.append(f"{name}: 등락률을 알 수 없음")
    ths = [x.strip() for x in theme.split(",") if x.strip()]
    for th in ths:
        themes_all.append(th)
        if t:
            nt = norm_text(t["text"])
            if norm_text(th)[:6] not in nt:
                theme_mismatch.append(f"{name}: 시트 테마 '{th}' 가 텔레그램 문장에 없음 ({t['text']})")
        else:
            theme_unknown.append(f"{name}: 테마 '{th}' (텔레그램에 이 종목이 없어 확인 불가)")
    if not ths and t and "테마" in t["text"]:
        report_theme_hint = f"{name}: 테마 칸이 비어 있고 텔레그램은 '{t['text']}'"
        report.append(report_theme_hint)
    if not t:
        no_tele.append(name)
    stocks_all.append((name, code))

    head = "- " + (" ".join(f"[[{x}]]" for x in ths) or "[[Null]]") + f" || [[{name}({code})]]"
    if pctv is not None:
        head += f" +{pctv:.2f}%"
    h, u = clean_headline(headline), clean_url(link)
    if h and u:
        news = f"[{h}]({u})"
    elif h:
        news = h
    elif u:
        news = f"[기사]({u})"
    else:
        news = ""
    # 순서: 종목 -> 뉴스 -> 텔레그램. 비어 있어도 두 칸은 남긴다.
    IND = "  "  # em 공백 두 칸: 화면에서 들여쓰기로 보인다
    lines.append(f"{head}<br>{IND}뉴스: {news}<br>{IND}텔레그램: {t['text'] if t else ''}")
    h_col.append(t["text"] if t else "")

journal = f"---\n날짜: {DAY}\n---\n" + "\n".join(lines) + "\n"
(HERE / f"journal_{DAY}.md").write_text(journal, encoding="utf-8", newline="\n")
(HERE / f"h_column_{MD}.json").write_text(json.dumps(h_col, ensure_ascii=False), encoding="utf-8")

tele_only = [f"{v['name']}({k}) +{v['pct']}%" for k, v in tele.items() if k not in used_tele]
out = [f"시트 11/02 행: {len(rows)}   텔레그램 종목: {len(tele)}   서로 맞은 것: {len(used_tele)}",
       f"텔레그램에는 있고 시트에는 없는 종목: {tele_only or '없음'}",
       f"시트에는 있고 텔레그램에는 없는 종목({len(no_tele)}): {', '.join(no_tele)}",
       "", "[코드 앞자리 0 보정]", *(code_fix or ["없음"]),
       "", "[등락률 채움]", *(pct_fill or ["없음"]),
       "", "[테마 확인 필요: 시트 테마가 텔레그램 문장에 없음]", *(theme_mismatch or ["없음"]),
       "", "[테마 확인 불가: 텔레그램에 종목이 없음]", *(theme_unknown or ["없음"]),
       "", "[테마 칸이 비었고 텔레그램이 '테마'를 언급함]", *(report or ["없음"])]
(HERE / f"report_{MD}.txt").write_text("\n".join(out), encoding="utf-8")

new_stock = new_theme = 0
if APPLY:
    jp = VAULT / "일지" / f"{DAY}.md"
    if jp.exists():
        shutil.copy2(jp, HERE / f"백업-{DAY}.md")
    jp.write_text(journal, encoding="utf-8", newline="\n")
    (VAULT / "종목").mkdir(parents=True, exist_ok=True)
    (VAULT / "테마").mkdir(parents=True, exist_ok=True)
    for name, code in stocks_all:
        title = f"{name}({code})"
        p = VAULT / "종목" / f"{title}.md"
        if not p.exists():
            p.write_text(STOCK_NOTE.format(code=code, title=title), encoding="utf-8", newline="\n")
            new_stock += 1
    for th in sorted(set(themes_all) | {"Null"}):
        p = VAULT / "테마" / f"{th}.md"
        if not p.exists():
            body = THEME_NOTE.format(title=th)
            if th == "Null":
                body = body.replace("- \n", "- 테마를 아직 정하지 못한 종목. 테마가 정해지면 일지에서 [[Null]]을 지우고 테마로 바꾼다.\n", 1)
            p.write_text(body, encoding="utf-8", newline="\n")
            new_theme += 1
    print(f"적용함: 일지 {jp.name}, 새 종목 노트 {new_stock}, 새 테마 노트 {new_theme}")
else:
    print("시험 실행: 보관함에는 아무것도 쓰지 않았습니다")
print("\n".join(out))

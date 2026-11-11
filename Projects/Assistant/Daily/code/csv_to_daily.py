"""Surge 날짜별 CSV -> 옵시디언 Daily 보관함 일지.

일지 줄 형식 (테마·이슈·기사는 직접 입력):
    - [[Null]] || [[종목(코드)]] +00.00%<br>이슈<br>관련 기사

사용법 (Windows 에서는 python 대신 py):
    py csv_to_daily.py                  CSV_DIR(Documents/assistant/surge)의 모든 CSV
    py csv_to_daily.py 2026-11-04       그 날짜만 (여러 개 가능)
    py csv_to_daily.py --dry-run        파일은 쓰지 않고 무엇을 할지만 보여 줌

규칙
  - 이미 있는 일지는 덮어쓰지 않는다. 그 일지에 아직 없는 종목 줄만 맨 아래에 붙인다.
  - 이미 있는 종목·테마 노트는 건드리지 않는다. 없는 종목 노트만 새로 만든다.
  - 이 스크립트는 CSV 와 보관함 밖의 것을 읽거나 쓰지 않는다.
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

VAULT = Path(r"C:\Users\Jinwo\Documents\Obsidian\Daily")
CSV_DIR = Path(r"C:\Users\Jinwo\Documents\assistant\surge")  # surge_daily.py 가 날짜별 CSV 를 만드는 폴더

NO_THEME = "Null"   # 테마를 아직 모를 때 쓰는 링크 (테마/Null.md)
ISSUE_LABEL = ""    # 예: "이슈: " 로 바꾸면 줄에 "이슈: " 가 미리 들어간다
ARTICLE_LABEL = ""  # 예: "기사: "

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

NULL_NOTE = '''---
tags:
  - 테마
---
## 테마 설명
- 테마를 아직 정하지 못한 종목. 테마가 정해지면 일지에서 [[Null]]을 지우고 테마로 바꾼다.

## 종목 · 급등 기록
```query
path:일지 "[[Null]]"
```
'''

BAD_CHARS = re.compile(r'[\\/:*?"<>|\[\]#^]')


def safe(name):
    """파일·링크 이름에 못 쓰는 글자를 ·로 바꾼다."""
    return BAD_CHARS.sub("·", name).strip()


def read_rows(csv_dir, only_dates):
    by_date = defaultdict(list)
    for path in sorted(csv_dir.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if not row.get("date") or not row.get("code"):
                    continue
                if only_dates and row["date"] not in only_dates:
                    continue
                by_date[row["date"]].append(row)
    return by_date


def stock_title(row):
    return f'{safe(row["name"])}({row["code"].strip()})'


def line_for(row):
    pct = float(row["pct"])
    return (f"- [[{NO_THEME}]] || [[{stock_title(row)}]] {pct:+.2f}%"
            f"<br>{ISSUE_LABEL}<br>{ARTICLE_LABEL}")


def write(path, text, dry):
    if dry:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="*", help="YYYY-MM-DD (없으면 CSV 의 모든 날짜)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vault", type=Path, default=VAULT)
    ap.add_argument("--csv-dir", type=Path, default=CSV_DIR)
    a = ap.parse_args()

    if not a.vault.exists():
        sys.exit(f"보관함을 찾을 수 없습니다: {a.vault}")
    by_date = read_rows(a.csv_dir, set(a.dates))
    if not by_date:
        sys.exit("읽을 행이 없습니다 (CSV 가 없거나 날짜가 맞지 않음).")

    null_note = a.vault / "테마" / f"{NO_THEME}.md"
    if not null_note.exists():
        write(null_note, NULL_NOTE, a.dry_run)
        print(f"새 테마 노트: {null_note.name}")

    for day in sorted(by_date):
        rows = by_date[day]
        journal = a.vault / "일지" / f"{day}.md"
        new_notes = 0
        for row in rows:
            note = a.vault / "종목" / f"{stock_title(row)}.md"
            if not note.exists():
                write(note, STOCK_NOTE.format(code=row["code"].strip(),
                                              title=stock_title(row)), a.dry_run)
                new_notes += 1

        if journal.exists():
            text = journal.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
            todo = [r for r in rows if f"[[{stock_title(r)}]]" not in text]
            if todo:
                if not text.endswith("\n"):
                    text += "\n"
                text += "\n".join(line_for(r) for r in todo) + "\n"
                write(journal, text, a.dry_run)
            print(f"{day}: 일지가 이미 있음 -> {len(todo)}줄 추가, "
                  f"{len(rows) - len(todo)}줄은 이미 있어서 건너뜀, 종목 노트 {new_notes}개 새로 만듦")
        else:
            body = f"---\n날짜: {day}\n---\n" + "\n".join(line_for(r) for r in rows) + "\n"
            write(journal, body, a.dry_run)
            print(f"{day}: 일지 새로 만듦 ({len(rows)}줄), 종목 노트 {new_notes}개 새로 만듦")

    if a.dry_run:
        print("(--dry-run: 아무것도 쓰지 않았습니다)")


if __name__ == "__main__":
    main()

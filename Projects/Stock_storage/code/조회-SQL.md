---
project: Stock_storage
kind: code
---
# MotherDuck 조회 SQL 모음

```sql
-- 최근 20일 일봉
SELECT d.date, d.open, d.high, d.low, d.close, d.volume, d.amount
FROM woong_stock.main.daily d JOIN woong_stock.main.stocks s USING (code)
WHERE s.name = '삼성전자' ORDER BY d.date DESC LIMIT 20;
```

```sql
-- 조건 캔들 (거래대금 150억↑, 고가≥전일종가×1.15, 고가≥저가×1.15, 종가≥시가×1.09)
WITH b AS (SELECT *, lag(close) OVER (PARTITION BY code ORDER BY date) AS prev_close FROM woong_stock.main.daily)
SELECT code, date, open, high, low, close, amount FROM b
WHERE date >= '2015-06-15' AND amount >= 15000 AND high >= prev_close * 1.15
  AND high >= low * 1.15 AND close >= open * 1.09
ORDER BY date DESC LIMIT 50;
```

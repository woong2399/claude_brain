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

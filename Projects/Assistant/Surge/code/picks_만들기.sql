-- Surge: 전일 종가 대비 10% 이상 오른 종목을 surge.main.picks 에 저장한다.
-- 데이터는 storage.main.daily / storage.main.stocks 를 조회만 한다 (storage 에는 쓰지 않는다).
-- 기간을 넓히려면 아래 날짜(2026-11-01)만 바꿔서 다시 실행한다. 전체를 다시 만든다.
-- amount 단위: 백만 원.
CREATE DATABASE IF NOT EXISTS surge;

CREATE OR REPLACE TABLE surge.main.picks AS
WITH x AS (
  SELECT code, date, close, amount,
         lag(close) OVER (PARTITION BY code ORDER BY date) AS prev
  FROM storage.main.daily
  WHERE close > 0
)
SELECT x.date, x.code, s.name,
       round((x.close * 1.0 / x.prev - 1) * 100, 2) AS pct,
       x.amount
FROM x
JOIN storage.main.stocks s USING (code)
WHERE x.date >= '2026-11-01'
  AND x.prev > 0
  AND x.close * 1.0 / x.prev - 1 >= 0.10
ORDER BY x.date, pct DESC;

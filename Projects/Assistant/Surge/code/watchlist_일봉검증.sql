-- 변동성 추적 목록 검증 (마더덕 storage.daily, 2021-01 ~)
-- 목록 R(순위 급상승) / P(당일 ±10%↑ & 500위내) / H(최근 20일 ±10% 2번↑ & 500위내)를
-- 하루 종목수·적중률·포착률로 비교한다. 결과는 docs/변동성-수급-지표정리 와 Sessions 노트 참고.
-- 적중 기준: 내일(n1) +10%↑, 내일 ±10%, 5일 내(up5) +10%↑. 거래대금 amount 는 2026-09-14 이후 에프터마켓 포함.

with base as materialized (
  select code, date, close, amount,
    row_number() over (partition by date order by amount desc) rk,
    close*1.0/lag(close) over w - 1 as r0,
    count(amount) over (partition by code order by date rows between 20 preceding and 1 preceding) as hist
  from daily where date>='2020-12-01' and amount>0 and close>0
  window w as (partition by code order by date)
), b as materialized (
  select *,
    avg(rk) over (partition by code order by date rows between 20 preceding and 1 preceding) avgrk20,
    sum((abs(r0)>=0.10)::int) over (partition by code order by date rows between 19 preceding and current row) c20,
    lead(r0,1) over w n1,
    greatest(lead(r0,1) over w, lead(r0,2) over w, lead(r0,3) over w, lead(r0,4) over w, lead(r0,5) over w) up5
  from base window w as (partition by code order by date)
), e as materialized (
  select *, (avgrk20>500 and rk<=200) as R, (abs(r0)>=0.10 and rk<=500) as P, (c20>=2 and rk<=500) as H
  from b where date>='2021-01-01' and n1 is not null and up5 is not null and r0 is not null and hist>=15),
tot as (select count(distinct date) nd, sum((n1>=0.10)::int) up1, sum((abs(n1)>=0.10)::int) bg1, sum((up5>=0.10)::int) u5 from e),
s as (
  select 'P 당일±10%↑ & 500위내' as nm, * from e where P
  union all select 'R+P+H 합집합', * from e where R or P or H
  union all select '조건 2개 이상 충족', * from e where (R::int+P::int+H::int)>=2
)
select nm as 목록, round(count(*)*1.0/(select nd from tot),1) as 하루종목수,
  round(avg((n1>=0.10)::int)*100,2) as 적중_내일상승10,
  round(avg((abs(n1)>=0.10)::int)*100,2) as 적중_내일pm10,
  round(avg((up5>=0.10)::int)*100,2) as 적중_5일내상승10,
  round(sum((n1>=0.10)::int)*100.0/(select up1 from tot),1) as 포착_내일상승10
from s group by nm order by nm;

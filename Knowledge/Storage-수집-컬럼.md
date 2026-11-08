---
updated: 2026-11-08
---
# Storage — 새로 받는 표의 컬럼 (영어 : 한국어)

모든 표 공통: `code` 종목코드 · `date` 날짜 · `fetched_at` 받은 시각 (`ma_daily` 는 `fetched_at` 없음). 단위는 대부분 **미확인**.

## program_trading — 프로그램 매매 (ka90004)
`market` 시장 · `buy_qty` 매수 수량 · `buy_amt` 매수 금액 · `sell_qty` 매도 수량 · `sell_amt` 매도 금액 · `net_amt` 순매수 금액 · `ratio` 비율

## investor_flow — 투자자별 순매수 (ka10059, 금액, 음수=순매도)
`individual` 개인 · `foreign_inv` 외국인 · `institution` 기관계 · `financial_inv` 금융투자 · `insurance` 보험 · `trust` 투신 · `other_fin` 기타금융 · `bank` 은행 · `pension_etc` 연기금 등 · `private_fund` 사모펀드 · `nation` 국가 · `other_corp` 기타법인 · `native_foreign` 내국인(외국인 중 내국인 표기, 의미 미확인)

## foreign_holding — 외국인 보유 (ka10008)
`net_qty` 순매매 수량 · `hold_qty` 보유 수량 · `hold_ratio` 보유 비중(%) · `room_qty` 보유 가능 수량 · `limit_qty` 한도 수량 · `limit_used_ratio` 한도 소진율(%)

## short_selling — 공매도 (ka10014)
`short_qty` 공매도 수량 · `short_ratio` 공매도 비중 · `short_amt` 공매도 금액 · `short_avg_price` 공매도 평균가 (누적은 구간마다 값이 달라 저장 안 함)

## loan_trading — 대차거래 (ka20068)
`new_qty` 신규 수량 · `repay_qty` 상환 수량 · `change_qty` 증감 수량 · `balance_qty` 잔고 수량 · `balance_amt` 잔고 금액

## ma_daily — 이동평균 (정규장 수정주가 종가, 단순)
`ma5` 5일선 · `ma20` 20일선 · `ma60` 60일선 · `ma120` 120일선 · `ma240` 240일선 · `ma480` 480일선 (N일 안 쌓이면 NULL)

(`investor_flow` 의 일부 한국어 이름은 열 이름에서 추정한 것. 키움 응답 이름과 대조 안 함.)

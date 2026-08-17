-- Воронка участия своей компании по месяцам: сколько лотов заявлено, сколько
-- выиграно, как менялась конверсия, с какой скидкой от начальной цены брались
-- победы и сколько исполнителей на них поставлено.
--
-- Допущения:
--   компания — единственная строка с companies.is_self;
--   период   — месяц подведения итогов; идущие закупки не учитываются, их
--              исход ещё неизвестен;
--   участие  — количество лотов, а не ставок: повторная ставка на тот же лот
--              не является новым участием;
--   скидка   — отклонение победившей ставки от начальной цены лота, считается
--              только по победам; в месяце без побед пусто, а не ноль.
--
-- Изменение конверсии — в процентных пунктах к предыдущему месяцу выборки.

WITH self_company AS (
    SELECT id FROM companies WHERE is_self
),
own_bids AS (
    SELECT date_trunc('month', t.decided_at) AS month,
           l.id AS lot_id,
           l.start_price,
           b.amount,
           b.is_winner
    FROM bids b
    JOIN lots l ON l.id = b.lot_id
    JOIN tenders t ON t.id = l.tender_id
    JOIN self_company s ON s.id = b.company_id
    WHERE t.decided_at IS NOT NULL
),
won_lots AS (
    SELECT month, lot_id
    FROM own_bids
    WHERE is_winner
),
assigned AS (
    SELECT w.month,
           count(DISTINCT lp.performer_id) AS performers_assigned
    FROM won_lots w
    JOIN lot_performers lp ON lp.lot_id = w.lot_id
    GROUP BY w.month
),
monthly AS (
    SELECT month,
           count(DISTINCT lot_id) AS lots_entered,
           count(*) FILTER (WHERE is_winner) AS wins,
           coalesce(sum(amount) FILTER (WHERE is_winner), 0) AS won_amount,
           round(
               avg((start_price - amount) / start_price * 100)
                   FILTER (WHERE is_winner),
               1
           ) AS avg_win_discount_pct
    FROM own_bids
    GROUP BY month
),
rates AS (
    SELECT month,
           lots_entered,
           wins,
           won_amount,
           avg_win_discount_pct,
           round(100.0 * wins / lots_entered, 1) AS win_rate_pct
    FROM monthly
)
SELECT r.month::date AS month,
       r.lots_entered,
       r.wins,
       r.win_rate_pct,
       r.win_rate_pct - lag(r.win_rate_pct) OVER (ORDER BY r.month)
           AS win_rate_delta_pp,
       r.won_amount,
       r.avg_win_discount_pct,
       coalesce(a.performers_assigned, 0) AS performers_assigned
FROM rates r
LEFT JOIN assigned a ON a.month = r.month
ORDER BY r.month;

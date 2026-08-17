-- Топ-3 компании по сумме выигранных тендеров за прошлый календарный месяц.
--
-- Допущения:
--   период  — прошлый календарный месяц, полуинтервал [начало, конец):
--             запись за 23:59:59 последнего дня входит, за 00:00:00 первого
--             дня следующего месяца — нет;
--   дата    — подведение итогов (tenders.decided_at), а не публикация:
--             закупка, объявленная в мае и решённая в июле, относится к июлю;
--   сумма   — сумма победивших ставок, а не начальных цен лотов: в аукционе
--             на понижение это разные числа;
--   единица — лот, а не тендер: лоты одного тендера могут достаться разным
--             компаниям.
--
-- Мест ровно три, но при равных суммах место делится, и строк может быть
-- больше трёх. Отсечение LIMIT 3 выкинуло бы одну из равных компаний
-- произвольно.
--
-- Другой период задаётся сдвигом границ в CTE period.

SET client_encoding = 'UTF8';

WITH period AS (
    SELECT date_trunc('month', now()) - interval '1 month' AS starts_at,
           date_trunc('month', now())                      AS ends_at
),
won AS (
    SELECT b.company_id,
           b.amount,
           t.id AS tender_id
    FROM bids b
    JOIN lots l ON l.id = b.lot_id
    JOIN tenders t ON t.id = l.tender_id
    CROSS JOIN period p
    WHERE b.is_winner
      AND t.decided_at >= p.starts_at
      AND t.decided_at < p.ends_at
),
totals AS (
    -- count(*) считает выигранные лоты: уникальный индекс
    -- bids_single_winner_per_lot_idx допускает одну победившую ставку на лот.
    SELECT company_id,
           sum(amount) AS won_amount,
           count(*) AS won_lots,
           count(DISTINCT tender_id) AS won_tenders
    FROM won
    GROUP BY company_id
),
ranked AS (
    SELECT company_id,
           won_amount,
           won_lots,
           won_tenders,
           dense_rank() OVER (ORDER BY won_amount DESC) AS place
    FROM totals
)
SELECT r.place,
       c.name AS company,
       c.inn,
       r.won_amount,
       r.won_lots,
       r.won_tenders
FROM ranked r
JOIN companies c ON c.id = r.company_id
WHERE r.place <= 3
ORDER BY r.place, c.name;

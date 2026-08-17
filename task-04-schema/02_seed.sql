-- Демонстрационные данные для аналитических запросов.
-- Применяется после 01_schema.sql: psql -d tender_registry -f 02_seed.sql
--
-- Даты заданы относительно начала текущего месяца, а не константами,
-- поэтому запрос «за последний месяц» возвращает непустой результат в любой
-- день, когда бы данные ни загружали. Обозначения в CTE: cm — начало
-- текущего месяца, pm — прошлого, ppm — позапрошлого.

INSERT INTO companies (id, name, inn, is_self) VALUES
    (1, 'Департамент информационных технологий', '7710000001', false),
    (2, 'ГБУ «Городские сервисы»',               '7710000002', false),
    (3, 'ООО «Вектор»',                          '7712345678', true),
    (4, 'ООО «Дельта»',                          '7723456789', false),
    (5, 'ООО «Меридиан»',                        '7734567890', false),
    (6, 'ООО «Аргус»',                           '7745678901', false),
    (7, 'ИП Соколов Артём Владимирович',         '771234567890', false);

WITH a AS (
    SELECT date_trunc('month', now())                       AS cm,
           date_trunc('month', now()) - interval '1 month'  AS pm,
           date_trunc('month', now()) - interval '2 months' AS ppm
)
INSERT INTO tenders (id, registry_number, customer_id, title, status,
                     published_at, bids_close_at, decided_at)
SELECT 1, '0173200001426000101', 1, 'Поставка серверного оборудования',
       'won'::tender_status,
       pm - interval '20 days', pm + interval '5 days', pm + interval '10 days'
FROM a
UNION ALL
SELECT 2, '0173200001426000102', 2, 'Разработка информационной системы',
       'lost'::tender_status,
       pm - interval '10 days', pm + interval '8 days', pm + interval '14 days'
FROM a
UNION ALL
-- Итоги за десять минут до конца прошлого месяца: строка должна попасть
-- в отбор за прошлый месяц.
SELECT 3, '0173200001426000103', 1, 'Сопровождение прикладного ПО',
       'lost'::tender_status,
       pm + interval '2 days', cm - interval '3 days', cm - interval '10 minutes'
FROM a
UNION ALL
-- Итоги через десять минут после начала текущего месяца: в отбор за прошлый
-- месяц строка попасть не должна, хотя процедура шла в прошлом месяце.
SELECT 4, '0173200001426000104', 2, 'Поставка вычислительной техники',
       'lost'::tender_status,
       pm + interval '1 day', cm - interval '2 days', cm + interval '10 minutes'
FROM a
UNION ALL
SELECT 5, '0173200001426000105', 1, 'Текущий ремонт помещений',
       'lost'::tender_status,
       pm - interval '5 days', pm + interval '12 days', pm + interval '18 days'
FROM a
UNION ALL
SELECT 6, '0173200001426000106', 2, 'Услуги технической поддержки',
       'lost'::tender_status,
       pm + interval '1 day', pm + interval '15 days', pm + interval '20 days'
FROM a
UNION ALL
SELECT 7, '0173200001426000107', 1, 'Модернизация сетевой инфраструктуры',
       'won'::tender_status,
       ppm - interval '15 days', ppm + interval '6 days', ppm + interval '12 days'
FROM a
UNION ALL
SELECT 8, '0173200001426000108', 2, 'Поставка лицензий на ПО',
       'lost'::tender_status,
       ppm - interval '5 days', ppm + interval '10 days', ppm + interval '16 days'
FROM a
UNION ALL
SELECT 9, '0173200001426000109', 1, 'Обслуживание рабочих станций',
       'active'::tender_status,
       now() - interval '8 days', now() + interval '7 days', NULL
FROM a
UNION ALL
-- Черновик: на площадке ещё не опубликован, поэтому номера и дат нет.
SELECT 10, NULL, 2, 'Разработка мобильного приложения',
       'draft'::tender_status,
       NULL, NULL, NULL
FROM a;

INSERT INTO lots (id, tender_id, lot_number, title, start_price) VALUES
    (1,  1,  1, 'Серверы',                        3500000.00),
    (2,  1,  2, 'Системы хранения данных',        2500000.00),
    (3,  2,  1, 'Разработка и внедрение',         2600000.00),
    (4,  3,  1, 'Сопровождение, 12 месяцев',      3200000.00),
    (5,  4,  1, 'Рабочие станции',                9000000.00),
    (6,  5,  1, 'Ремонт помещений',               2400000.00),
    (7,  6,  1, 'Техническая поддержка',           600000.00),
    (8,  7,  1, 'Активное сетевое оборудование',  1800000.00),
    (9,  8,  1, 'Лицензии на ПО',                 1000000.00),
    (10, 9,  1, 'Обслуживание, первая площадка',  4000000.00),
    (11, 9,  2, 'Обслуживание, вторая площадка',  1200000.00),
    (12, 10, 1, 'Разработка приложения',           800000.00);

-- Время подачи считается от закрытия приёма заявок, чтобы ставки не
-- оказались поданными после срока при любой дате загрузки данных.
INSERT INTO bids (id, lot_id, company_id, amount, submitted_at, is_winner)
SELECT v.id, v.lot_id, v.company_id, v.amount,
       t.bids_close_at - v.hours_before * interval '1 hour', v.is_winner
FROM (VALUES
    (1,  1,  4, 3000000.00, 24,  true),
    (2,  1,  5, 3200000.00, 48,  false),
    (3,  1,  6, 3400000.00, 72,  false),
    -- Три ставки одной компании на один лот: в зачёт идёт только победившая.
    (4,  2,  3, 2300000.00, 72,  false),
    (5,  2,  3, 2100000.00, 48,  false),
    (6,  2,  3, 2000000.00, 24,  true),
    (7,  2,  4, 2200000.00, 36,  false),
    (8,  3,  4, 2000000.00, 24,  true),
    (9,  3,  3, 2100000.00, 48,  false),
    (10, 4,  5, 3000000.00, 24,  true),
    (11, 4,  3, 3100000.00, 48,  false),
    (12, 5,  6, 8000000.00, 24,  true),
    (13, 5,  3, 8500000.00, 48,  false),
    (14, 6,  6, 2000000.00, 24,  true),
    (15, 6,  3, 2050000.00, 48,  false),
    (16, 7,  7,  500000.00, 24,  true),
    (17, 7,  3,  520000.00, 48,  false),
    (18, 8,  3, 1500000.00, 24,  true),
    (19, 8,  5, 1600000.00, 48,  false),
    (20, 9,  4,  800000.00, 24,  true),
    (21, 9,  3,  900000.00, 48,  false),
    -- Приём заявок ещё идёт, победителя нет.
    (22, 10, 3, 3700000.00, 240, false),
    (23, 10, 4, 3800000.00, 216, false),
    (24, 11, 5, 1150000.00, 240, false),
    (25, 11, 7, 1100000.00, 216, false)
) AS v (id, lot_id, company_id, amount, hours_before, is_winner)
JOIN lots l ON l.id = v.lot_id
JOIN tenders t ON t.id = l.tender_id;

INSERT INTO performers (id, full_name, inn) VALUES
    (1, 'Иванов Сергей Петрович',   '771234567801'),
    (2, 'Петрова Анна Игоревна',    '771234567802'),
    (3, 'Сидоров Дмитрий Львович',  '771234567803');

-- Исполнители назначаются на выигранные лоты своей компании; Иванов занят
-- на двух лотах, на лоте 2 работают двое.
INSERT INTO lot_performers (lot_id, performer_id, assigned_at)
SELECT v.lot_id, v.performer_id, t.decided_at + interval '3 days'
FROM (VALUES (2, 1), (2, 2), (8, 1), (8, 3)) AS v (lot_id, performer_id)
JOIN lots l ON l.id = v.lot_id
JOIN tenders t ON t.id = l.tender_id;

-- Идентификаторы вставлены явно, поэтому последовательности нужно перевести
-- за максимум — иначе первая вставка без id упрётся в занятое значение.
SELECT setval(pg_get_serial_sequence('companies',  'id'), max(id)) FROM companies;
SELECT setval(pg_get_serial_sequence('tenders',    'id'), max(id)) FROM tenders;
SELECT setval(pg_get_serial_sequence('lots',       'id'), max(id)) FROM lots;
SELECT setval(pg_get_serial_sequence('bids',       'id'), max(id)) FROM bids;
SELECT setval(pg_get_serial_sequence('performers', 'id'), max(id)) FROM performers;

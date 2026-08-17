-- Схема сервиса трекинга статусов тендеров.
-- Применяется на пустой базе: psql -d tender_tracker -f schema/01_schema.sql
--
-- Таблица tenders содержит только то, что нужно трекингу статусов. Схема
-- задания 4 не переиспользуется: задания проверяются независимо, а её тендер
-- требует заказчика, без которого создание тендера через API невозможно.

SET client_encoding = 'UTF8';

CREATE TYPE tender_status AS ENUM ('draft', 'active', 'won', 'lost');

CREATE TABLE tenders (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title      text NOT NULL,
    status     tender_status NOT NULL DEFAULT 'draft',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT tenders_title_not_blank CHECK (btrim(title) <> '')
);

CREATE TABLE tender_status_history (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tender_id  bigint NOT NULL REFERENCES tenders (id) ON DELETE CASCADE,
    old_status tender_status,
    new_status tender_status NOT NULL,
    changed_by text NOT NULL,
    reason     text NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now(),
    -- Запись о создании тендера — единственная с пустым старым статусом.
    -- IS DISTINCT FROM сравнивает с учётом NULL, в отличие от <>.
    CONSTRAINT tender_status_history_status_changed
        CHECK (old_status IS DISTINCT FROM new_status),
    CONSTRAINT tender_status_history_changed_by_not_blank
        CHECK (btrim(changed_by) <> ''),
    CONSTRAINT tender_status_history_reason_not_blank
        CHECK (btrim(reason) <> '')
);

-- Чтение истории одного тендера в порядке времени.
CREATE INDEX tender_status_history_tender_changed_at_idx
    ON tender_status_history (tender_id, changed_at);

COMMENT ON TABLE tenders IS
    'Тендеры: черновик, активен, выигран, проигран';
COMMENT ON TABLE tender_status_history IS
    'История изменений статуса: кто изменил, когда и почему';
COMMENT ON COLUMN tender_status_history.old_status IS
    'Предыдущий статус; пусто у записи о создании тендера';

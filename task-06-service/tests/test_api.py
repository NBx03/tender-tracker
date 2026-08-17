"""Проверка эндпоинтов на отдельной тестовой базе."""

import pytest


def change_status(client, tender_id: int, target: str, **overrides):
    body = {"status": target, "changed_by": "petrov", "reason": f"перевод в {target}"}
    body.update(overrides)
    return client.patch(f"/tenders/{tender_id}/status", json=body)


def test_created_tender_is_draft(tender: dict) -> None:
    assert tender["status"] == "draft"


def test_creation_is_logged_with_empty_old_status(client, tender: dict) -> None:
    history = client.get(f"/tenders/{tender['id']}/history").json()

    assert len(history) == 1
    assert history[0]["old_status"] is None
    assert history[0]["new_status"] == "draft"
    assert history[0]["changed_by"] == "ivanov"
    assert history[0]["reason"] == "закупка подходит по профилю"


def test_status_change_is_logged(client, tender: dict) -> None:
    response = change_status(client, tender["id"], "active")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    history = client.get(f"/tenders/{tender['id']}/history").json()
    assert len(history) == 2
    assert history[1]["old_status"] == "draft"
    assert history[1]["new_status"] == "active"
    assert history[1]["changed_by"] == "petrov"


def test_history_keeps_chain_in_order(client, tender: dict) -> None:
    change_status(client, tender["id"], "active")
    change_status(client, tender["id"], "lost")

    history = client.get(f"/tenders/{tender['id']}/history").json()

    chain = [(change["old_status"], change["new_status"]) for change in history]
    assert chain == [(None, "draft"), ("draft", "active"), ("active", "lost")]


def test_forbidden_transition_rejected(client, tender: dict) -> None:
    response = change_status(client, tender["id"], "won")

    assert response.status_code == 409
    assert "недопустим" in response.json()["detail"]


def test_transition_to_same_status_rejected(client, tender: dict) -> None:
    assert change_status(client, tender["id"], "draft").status_code == 409


def test_transition_from_final_status_rejected(client, tender: dict) -> None:
    change_status(client, tender["id"], "active")
    change_status(client, tender["id"], "won")

    assert change_status(client, tender["id"], "lost").status_code == 409


def test_rejected_transition_leaves_no_history(client, tender: dict) -> None:
    before = client.get(f"/tenders/{tender['id']}/history").json()
    change_status(client, tender["id"], "won")
    after = client.get(f"/tenders/{tender['id']}/history").json()

    assert before == after


def test_rejected_transition_leaves_status_unchanged(client, tender: dict) -> None:
    change_status(client, tender["id"], "won")

    history = client.get(f"/tenders/{tender['id']}/history").json()
    assert history[-1]["new_status"] == "draft"


@pytest.mark.parametrize("path", ["/tenders/999999/status", "/tenders/999999/history"])
def test_unknown_tender_returns_404(client, path: str) -> None:
    if path.endswith("status"):
        response = change_status(client, 999999, "active")
    else:
        response = client.get(path)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"title": "   ", "changed_by": "ivanov", "reason": "пустое название"},
        {"title": "Тендер", "changed_by": "  ", "reason": "пустой автор"},
        {"title": "Тендер", "changed_by": "ivanov", "reason": "  "},
        {"title": "Тендер", "changed_by": "ivanov"},
    ],
)
def test_invalid_creation_body_rejected(client, body: dict) -> None:
    assert client.post("/tenders", json=body).status_code == 422


def test_unknown_status_value_rejected(client, tender: dict) -> None:
    assert change_status(client, tender["id"], "cancelled").status_code == 422

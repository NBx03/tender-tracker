"""Матрица переходов проверяется без базы и без HTTP."""

import pytest

from app.statuses import TenderStatus, is_allowed

ALLOWED = [
    (TenderStatus.DRAFT, TenderStatus.ACTIVE),
    (TenderStatus.ACTIVE, TenderStatus.WON),
    (TenderStatus.ACTIVE, TenderStatus.LOST),
]

FORBIDDEN = [
    (TenderStatus.DRAFT, TenderStatus.WON),
    (TenderStatus.DRAFT, TenderStatus.LOST),
    (TenderStatus.ACTIVE, TenderStatus.DRAFT),
    (TenderStatus.WON, TenderStatus.LOST),
    (TenderStatus.WON, TenderStatus.ACTIVE),
    (TenderStatus.LOST, TenderStatus.ACTIVE),
]


@pytest.mark.parametrize(("current", "target"), ALLOWED)
def test_allowed_transitions(current: TenderStatus, target: TenderStatus) -> None:
    assert is_allowed(current, target)


@pytest.mark.parametrize(("current", "target"), FORBIDDEN)
def test_forbidden_transitions(current: TenderStatus, target: TenderStatus) -> None:
    assert not is_allowed(current, target)


@pytest.mark.parametrize("status", list(TenderStatus))
def test_transition_to_same_status_is_forbidden(status: TenderStatus) -> None:
    assert not is_allowed(status, status)


@pytest.mark.parametrize("status", [TenderStatus.WON, TenderStatus.LOST])
def test_final_statuses_have_no_exits(status: TenderStatus) -> None:
    assert not any(is_allowed(status, target) for target in TenderStatus)

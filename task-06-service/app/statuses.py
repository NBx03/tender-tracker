from enum import StrEnum


class TenderStatus(StrEnum):
    DRAFT = "draft"      # Черновик
    ACTIVE = "active"    # Активен
    WON = "won"          # Выигран
    LOST = "lost"        # Проигран


# Черновик публикуется, активная закупка завершается одним из двух исходов.
# Из исхода переходов нет: он уже наступил и переписыванию не подлежит.
ALLOWED_TRANSITIONS: dict[TenderStatus, frozenset[TenderStatus]] = {
    TenderStatus.DRAFT: frozenset({TenderStatus.ACTIVE}),
    TenderStatus.ACTIVE: frozenset({TenderStatus.WON, TenderStatus.LOST}),
    TenderStatus.WON: frozenset(),
    TenderStatus.LOST: frozenset(),
}


def is_allowed(current: TenderStatus, target: TenderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]

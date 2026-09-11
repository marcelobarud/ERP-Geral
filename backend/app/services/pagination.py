from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginate(
    db: Session,
    query: Any,
    page: int,
    page_size: int,
) -> tuple[Sequence[Any], int, int]:
    total = db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    ) or 0
    total_pages = (total + page_size - 1) // page_size if total else 0
    items = db.scalars(
        query.limit(page_size).offset((page - 1) * page_size)
    ).all()
    return items, total, total_pages

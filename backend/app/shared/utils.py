from math import ceil

from app.shared.schemas import PaginationMeta


def build_pagination_meta(total: int, page: int, limit: int) -> dict:
    meta = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=ceil(total / limit) if limit > 0 else 0,
    )
    return meta.model_dump()

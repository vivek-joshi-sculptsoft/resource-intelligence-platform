from app.shared.schemas import PaginationParams
from app.shared.utils import build_pagination_meta


def test_pagination_params_defaults():
    params = PaginationParams()
    assert params.page == 1
    assert params.limit == 20
    assert params.offset == 0


def test_pagination_params_offset():
    params = PaginationParams(page=3, limit=10)
    assert params.offset == 20


def test_build_pagination_meta():
    meta = build_pagination_meta(total=45, page=2, limit=20)
    assert meta["total"] == 45
    assert meta["page"] == 2
    assert meta["limit"] == 20
    assert meta["total_pages"] == 3


def test_build_pagination_meta_exact_fit():
    meta = build_pagination_meta(total=40, page=1, limit=20)
    assert meta["total_pages"] == 2


def test_build_pagination_meta_single_page():
    meta = build_pagination_meta(total=5, page=1, limit=20)
    assert meta["total_pages"] == 1

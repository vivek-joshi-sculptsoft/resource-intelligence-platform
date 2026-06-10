from app.shared.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


def test_app_exception_defaults():
    exc = AppError(message="test error")
    assert exc.message == "test error"
    assert exc.status_code == 400
    assert exc.field is None


def test_app_exception_custom_status():
    exc = AppError(message="bad", status_code=422, field="email")
    assert exc.status_code == 422
    assert exc.field == "email"


def test_not_found_exception():
    exc = NotFoundError("Project")
    assert exc.status_code == 404
    assert "Project not found" in exc.message


def test_not_found_with_id():
    exc = NotFoundError("Project", "abc-123")
    assert "abc-123" in exc.message


def test_forbidden_exception():
    exc = ForbiddenError()
    assert exc.status_code == 403


def test_unauthorized_exception():
    exc = UnauthorizedError()
    assert exc.status_code == 401


def test_conflict_exception():
    exc = ConflictError("Duplicate entry", field="email")
    assert exc.status_code == 409
    assert exc.field == "email"


def test_validation_exception():
    exc = ValidationError("Invalid value", field="allocation_pct")
    assert exc.status_code == 422
    assert exc.field == "allocation_pct"

from app.shared.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


def test_app_exception_defaults():
    exc = AppException(message="test error")
    assert exc.message == "test error"
    assert exc.status_code == 400
    assert exc.field is None


def test_app_exception_custom_status():
    exc = AppException(message="bad", status_code=422, field="email")
    assert exc.status_code == 422
    assert exc.field == "email"


def test_not_found_exception():
    exc = NotFoundException("Project")
    assert exc.status_code == 404
    assert "Project not found" in exc.message


def test_not_found_with_id():
    exc = NotFoundException("Project", "abc-123")
    assert "abc-123" in exc.message


def test_forbidden_exception():
    exc = ForbiddenException()
    assert exc.status_code == 403


def test_unauthorized_exception():
    exc = UnauthorizedException()
    assert exc.status_code == 401


def test_conflict_exception():
    exc = ConflictException("Duplicate entry", field="email")
    assert exc.status_code == 409
    assert exc.field == "email"


def test_validation_exception():
    exc = ValidationException("Invalid value", field="allocation_pct")
    assert exc.status_code == 422
    assert exc.field == "allocation_pct"

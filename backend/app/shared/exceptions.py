class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        field: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, entity: str, entity_id: str | None = None):
        msg = f"{entity} not found" if not entity_id else f"{entity} with id {entity_id} not found"
        super().__init__(message=msg, status_code=404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message=message, status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ConflictError(AppError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message=message, status_code=409, field=field)


class ValidationError(AppError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message=message, status_code=422, field=field)

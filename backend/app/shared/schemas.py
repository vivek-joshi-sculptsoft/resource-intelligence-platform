from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel):
    data: list
    meta: dict


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    field: str | None = None


class SuccessResponse(BaseModel):
    data: dict | list | None = None
    meta: dict | None = None

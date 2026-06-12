import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RoleResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    permission_level: int

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleResponse
    resource_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    user: UserResponse


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role_id: uuid.UUID
    resource_id: uuid.UUID | None = None


class UserUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    role_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=128)


class UserListResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: RoleResponse
    resource_id: uuid.UUID | None
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    data_type: str
    access_level: str
    scope: str
    is_configurable: bool

    model_config = {"from_attributes": True}


class RoleDetailResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    permission_level: int
    is_active: bool
    permissions: list[PermissionResponse]

    model_config = {"from_attributes": True}

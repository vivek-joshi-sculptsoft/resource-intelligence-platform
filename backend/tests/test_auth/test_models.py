from app.modules.auth.models import (
    AccessLevel,
    Role,
    RolePermission,
    Scope,
    SystemConfig,
    User,
)


def test_role_table_name():
    assert Role.__tablename__ == "roles"


def test_role_has_required_columns():
    columns = {c.name for c in Role.__table__.columns}
    assert {"id", "name", "code", "permission_level", "is_active", "created_at"} <= columns


def test_role_name_is_unique():
    name_col = Role.__table__.c.name
    assert any(uc.columns == {name_col} for uc in Role.__table__.constraints if hasattr(uc, "columns"))


def test_role_permission_table_name():
    assert RolePermission.__tablename__ == "role_permissions"


def test_role_permission_unique_constraint():
    constraint_names = [c.name for c in RolePermission.__table__.constraints]
    assert "uq_role_data_type" in constraint_names


def test_access_level_enum_values():
    assert set(AccessLevel) == {AccessLevel.NONE, AccessLevel.VIEW, AccessLevel.EDIT}


def test_scope_enum_values():
    assert set(Scope) == {Scope.ALL, Scope.OWN_PORTFOLIO, Scope.SELF_ONLY}


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_user_has_password_hash():
    columns = {c.name for c in User.__table__.columns}
    assert "password_hash" in columns


def test_user_resource_id_nullable():
    resource_id_col = User.__table__.c.resource_id
    assert resource_id_col.nullable is True


def test_system_config_table_name():
    assert SystemConfig.__tablename__ == "system_config"


def test_system_config_key_unique():
    key_col = SystemConfig.__table__.c.key
    assert any(uc.columns == {key_col} for uc in SystemConfig.__table__.constraints if hasattr(uc, "columns"))


def test_user_role_id_indexed():
    indexes = {idx.name for idx in User.__table__.indexes}
    assert "ix_users_role_id" in indexes


def test_role_permission_role_id_indexed():
    indexes = {idx.name for idx in RolePermission.__table__.indexes}
    assert "ix_role_permissions_role_id" in indexes

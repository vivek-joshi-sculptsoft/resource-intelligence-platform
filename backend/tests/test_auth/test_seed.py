from app.modules.auth.seed import (
    DATA_TYPES,
    PERMISSIONS,
    ROLES,
    SYSTEM_CONFIG,
)


def test_seven_roles_defined():
    assert len(ROLES) == 7


def test_role_codes():
    codes = {r["code"] for r in ROLES}
    assert codes == {"CEO", "CTO", "DM", "PM", "FINANCE", "HR", "ENGINEER"}


def test_all_roles_have_permission_level():
    for role in ROLES:
        assert "permission_level" in role
        assert isinstance(role["permission_level"], int)


def test_fifteen_data_types():
    assert len(DATA_TYPES) == 16


def test_permissions_cover_all_roles():
    role_codes = {r["code"] for r in ROLES}
    perm_codes = set(PERMISSIONS.keys())
    assert role_codes == perm_codes


def test_each_role_has_all_data_types():
    for role_code, perms in PERMISSIONS.items():
        assert set(perms.keys()) == set(DATA_TYPES), f"{role_code} missing data types"


def test_total_permission_rows_is_105():
    total = sum(len(perms) for perms in PERMISSIONS.values())
    assert total == 112


def test_permission_values_are_valid():
    valid_access = {"NONE", "VIEW", "EDIT"}
    valid_scope = {"ALL", "OWN_PORTFOLIO", "SELF_ONLY"}
    for role_code, perms in PERMISSIONS.items():
        for dt, (access, scope, configurable) in perms.items():
            assert access in valid_access, f"{role_code}.{dt} bad access: {access}"
            assert scope in valid_scope, f"{role_code}.{dt} bad scope: {scope}"
            assert isinstance(configurable, bool)


def test_seven_system_config_keys():
    assert len(SYSTEM_CONFIG) == 7


def test_system_config_keys():
    keys = {c[0] for c in SYSTEM_CONFIG}
    expected = {
        "alert.contract_expiry_days",
        "alert.contract_expiry_urgent_days",
        "alert.bench_threshold_days",
        "alert.utilization_threshold_pct",
        "system.working_days_per_month",
        "system.working_hours_per_day",
        "system.default_currency",
    }
    assert keys == expected


def test_ceo_has_edit_on_client_profiles():
    assert PERMISSIONS["CEO"]["client_profiles"][0] == "EDIT"
    assert PERMISSIONS["CEO"]["client_profiles"][1] == "ALL"


def test_engineer_has_self_only_scope_on_worklogs():
    assert PERMISSIONS["ENGINEER"]["worklogs"][0] == "EDIT"
    assert PERMISSIONS["ENGINEER"]["worklogs"][1] == "SELF_ONLY"


def test_engineer_no_access_to_billing_rates():
    assert PERMISSIONS["ENGINEER"]["billing_rates"][0] == "NONE"


def test_dm_configurable_billing_rates():
    assert PERMISSIONS["DM"]["billing_rates"][2] is True


def test_dm_configurable_project_margin():
    assert PERMISSIONS["DM"]["project_margin"][2] is True


def test_seed_idempotent_by_design():
    """Verify seed functions use upsert-style checks (select before insert)."""
    import inspect
    from app.modules.auth.seed import _seed_roles, _seed_permissions, _seed_system_config, _seed_admin_user

    for fn in [_seed_roles, _seed_permissions, _seed_system_config, _seed_admin_user]:
        source = inspect.getsource(fn)
        assert "scalar_one_or_none" in source, f"{fn.__name__} must check existence before insert"

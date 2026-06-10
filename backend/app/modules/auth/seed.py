import uuid

from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AccessLevel, Role, RolePermission, Scope, SystemConfig, User

ph = PasswordHasher()

ROLES = [
    {"name": "CEO", "code": "CEO", "permission_level": 100},
    {"name": "CTO", "code": "CTO", "permission_level": 90},
    {"name": "Delivery Manager", "code": "DM", "permission_level": 70},
    {"name": "Project Manager", "code": "PM", "permission_level": 60},
    {"name": "Finance", "code": "FINANCE", "permission_level": 70},
    {"name": "HR", "code": "HR", "permission_level": 50},
    {"name": "Engineer", "code": "ENGINEER", "permission_level": 10},
]

DATA_TYPES = [
    "client_profiles",
    "project_details",
    "resource_profiles",
    "allocation",
    "billability",
    "billing_rates",
    "ctc_loaded_cost",
    "project_margin",
    "non_human_costs",
    "shadow_assignments",
    "resource_availability",
    "bench_data",
    "invoicing",
    "worklogs",
    "alerts",
]

# See shared/ACCESS-MATRIX.md — 7 roles x 15 data_types = 105 rows
PERMISSIONS: dict[str, dict[str, tuple[str, str, bool]]] = {
    "CEO": {
        "client_profiles": ("EDIT", "ALL", False),
        "project_details": ("EDIT", "ALL", False),
        "resource_profiles": ("EDIT", "ALL", False),
        "allocation": ("EDIT", "ALL", False),
        "billability": ("EDIT", "ALL", False),
        "billing_rates": ("VIEW", "ALL", False),
        "ctc_loaded_cost": ("VIEW", "ALL", False),
        "project_margin": ("VIEW", "ALL", False),
        "non_human_costs": ("EDIT", "ALL", False),
        "shadow_assignments": ("VIEW", "ALL", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("VIEW", "ALL", False),
        "worklogs": ("VIEW", "ALL", False),
        "alerts": ("VIEW", "ALL", False),
    },
    "CTO": {
        "client_profiles": ("EDIT", "ALL", False),
        "project_details": ("EDIT", "ALL", False),
        "resource_profiles": ("EDIT", "ALL", False),
        "allocation": ("EDIT", "ALL", False),
        "billability": ("EDIT", "ALL", False),
        "billing_rates": ("VIEW", "ALL", False),
        "ctc_loaded_cost": ("VIEW", "ALL", False),
        "project_margin": ("VIEW", "ALL", False),
        "non_human_costs": ("EDIT", "ALL", False),
        "shadow_assignments": ("VIEW", "ALL", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("VIEW", "ALL", False),
        "worklogs": ("VIEW", "ALL", False),
        "alerts": ("VIEW", "ALL", False),
    },
    "DM": {
        "client_profiles": ("VIEW", "OWN_PORTFOLIO", False),
        "project_details": ("EDIT", "OWN_PORTFOLIO", False),
        "resource_profiles": ("VIEW", "OWN_PORTFOLIO", False),
        "allocation": ("VIEW", "OWN_PORTFOLIO", False),
        "billability": ("VIEW", "OWN_PORTFOLIO", False),
        "billing_rates": ("VIEW", "OWN_PORTFOLIO", True),
        "ctc_loaded_cost": ("NONE", "ALL", False),
        "project_margin": ("VIEW", "OWN_PORTFOLIO", True),
        "non_human_costs": ("EDIT", "OWN_PORTFOLIO", False),
        "shadow_assignments": ("VIEW", "OWN_PORTFOLIO", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("NONE", "ALL", False),
        "worklogs": ("VIEW", "OWN_PORTFOLIO", False),
        "alerts": ("VIEW", "OWN_PORTFOLIO", False),
    },
    "PM": {
        "client_profiles": ("VIEW", "OWN_PORTFOLIO", False),
        "project_details": ("EDIT", "OWN_PORTFOLIO", False),
        "resource_profiles": ("VIEW", "OWN_PORTFOLIO", False),
        "allocation": ("EDIT", "OWN_PORTFOLIO", False),
        "billability": ("EDIT", "OWN_PORTFOLIO", False),
        "billing_rates": ("NONE", "ALL", False),
        "ctc_loaded_cost": ("NONE", "ALL", False),
        "project_margin": ("NONE", "ALL", False),
        "non_human_costs": ("EDIT", "OWN_PORTFOLIO", False),
        "shadow_assignments": ("VIEW", "OWN_PORTFOLIO", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("NONE", "ALL", False),
        "invoicing": ("NONE", "ALL", False),
        "worklogs": ("VIEW", "OWN_PORTFOLIO", False),
        "alerts": ("VIEW", "OWN_PORTFOLIO", False),
    },
    "FINANCE": {
        "client_profiles": ("VIEW", "ALL", False),
        "project_details": ("VIEW", "ALL", False),
        "resource_profiles": ("VIEW", "ALL", False),
        "allocation": ("VIEW", "ALL", False),
        "billability": ("VIEW", "ALL", False),
        "billing_rates": ("VIEW", "ALL", False),
        "ctc_loaded_cost": ("VIEW", "ALL", False),
        "project_margin": ("VIEW", "ALL", False),
        "non_human_costs": ("EDIT", "ALL", False),
        "shadow_assignments": ("VIEW", "ALL", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("EDIT", "ALL", False),
        "worklogs": ("NONE", "ALL", False),
        "alerts": ("VIEW", "ALL", False),
    },
    "HR": {
        "client_profiles": ("VIEW", "ALL", False),
        "project_details": ("VIEW", "ALL", False),
        "resource_profiles": ("EDIT", "ALL", False),
        "allocation": ("VIEW", "ALL", False),
        "billability": ("NONE", "ALL", False),
        "billing_rates": ("NONE", "ALL", False),
        "ctc_loaded_cost": ("NONE", "ALL", False),
        "project_margin": ("NONE", "ALL", False),
        "non_human_costs": ("NONE", "ALL", False),
        "shadow_assignments": ("NONE", "ALL", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("NONE", "ALL", False),
        "worklogs": ("NONE", "ALL", False),
        "alerts": ("VIEW", "ALL", False),
    },
    "ENGINEER": {
        "client_profiles": ("NONE", "ALL", False),
        "project_details": ("NONE", "ALL", False),
        "resource_profiles": ("VIEW", "SELF_ONLY", False),
        "allocation": ("VIEW", "SELF_ONLY", False),
        "billability": ("NONE", "ALL", False),
        "billing_rates": ("NONE", "ALL", False),
        "ctc_loaded_cost": ("NONE", "ALL", False),
        "project_margin": ("NONE", "ALL", False),
        "non_human_costs": ("NONE", "ALL", False),
        "shadow_assignments": ("NONE", "ALL", False),
        "resource_availability": ("VIEW", "ALL", False),
        "bench_data": ("VIEW", "ALL", False),
        "invoicing": ("NONE", "ALL", False),
        "worklogs": ("EDIT", "SELF_ONLY", False),
        "alerts": ("NONE", "ALL", False),
    },
}

SYSTEM_CONFIG = [
    ("alert.contract_expiry_days", "30", "Days before contract end for first alert"),
    ("alert.contract_expiry_urgent_days", "7", "Days before contract end for urgent alert"),
    ("alert.bench_threshold_days", "7", "Days on bench before alerting"),
    ("alert.utilization_threshold_pct", "70", "Company utilization below this triggers alert"),
    ("system.working_days_per_month", "22", "Used in revenue/utilization calculations"),
    ("system.working_hours_per_day", "8", "Used in hourly revenue calculations"),
    ("system.default_currency", "INR", "Default billing currency for new projects"),
]


async def seed_all(db: AsyncSession) -> None:
    await _seed_roles(db)
    await _seed_permissions(db)
    await _seed_system_config(db)
    await _seed_admin_user(db)
    await db.commit()


async def _seed_roles(db: AsyncSession) -> None:
    for role_data in ROLES:
        existing = await db.execute(select(Role).where(Role.code == role_data["code"]))
        if existing.scalar_one_or_none() is None:
            db.add(Role(id=uuid.uuid4(), **role_data))


async def _seed_permissions(db: AsyncSession) -> None:
    roles_result = await db.execute(select(Role))
    role_map = {r.code: r.id for r in roles_result.scalars().all()}

    for role_code, perms in PERMISSIONS.items():
        role_id = role_map.get(role_code)
        if not role_id:
            continue

        for data_type, (access, scope, configurable) in perms.items():
            existing = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.data_type == data_type,
                )
            )
            if existing.scalar_one_or_none() is None:
                db.add(
                    RolePermission(
                        id=uuid.uuid4(),
                        role_id=role_id,
                        data_type=data_type,
                        access_level=AccessLevel(access),
                        scope=Scope(scope),
                        is_configurable=configurable,
                    )
                )


async def _seed_system_config(db: AsyncSession) -> None:
    for key, value, description in SYSTEM_CONFIG:
        existing = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        if existing.scalar_one_or_none() is None:
            db.add(SystemConfig(id=uuid.uuid4(), key=key, value=value, description=description))


async def _seed_admin_user(db: AsyncSession) -> None:
    existing = await db.execute(select(User).where(User.email == "admin@ri-platform.com"))
    if existing.scalar_one_or_none() is not None:
        return

    ceo_role = await db.execute(select(Role).where(Role.code == "CEO"))
    ceo = ceo_role.scalar_one_or_none()
    if not ceo:
        return

    db.add(
        User(
            id=uuid.uuid4(),
            email="admin@ri-platform.com",
            name="System Admin",
            password_hash=ph.hash("ChangeMe123!"),
            role_id=ceo.id,
            resource_id=None,
        )
    )

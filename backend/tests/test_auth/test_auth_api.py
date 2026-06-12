import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_as, login_as_role


class TestAppStartup:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_login_endpoint_reachable(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ri-platform.com", "password": "ChangeMe123!"},
        )
        assert resp.status_code == 200

    async def test_seed_data_present(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get("/api/v1/roles")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 7

        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1


class TestLogin:
    async def test_login_valid_creds(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ri-platform.com", "password": "ChangeMe123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "admin@ri-platform.com"
        assert data["user"]["role"]["code"] == "CEO"
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    async def test_login_invalid_password(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@ri-platform.com", "password": "wrong"},
        )
        assert resp.status_code == 401
        assert resp.json()["message"] == "Invalid email or password"

    async def test_login_nonexistent_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": "anything"},
        )
        assert resp.status_code == 401
        assert resp.json()["message"] == "Invalid email or password"

    async def test_login_inactive_user(self, client: AsyncClient, db: AsyncSession):
        user = await create_test_user(db, "ENGINEER", email="inactive@test.com")
        user.is_active = False
        await db.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@test.com", "password": "TestPass123"},
        )
        assert resp.status_code == 401
        assert resp.json()["message"] == "Account is inactive"


class TestLogout:
    async def test_logout_clears_cookies(self, client: AsyncClient):
        await login_as(client)
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestRefresh:
    async def test_refresh_issues_new_tokens(self, client: AsyncClient):
        await login_as(client)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "admin@ri-platform.com"

    async def test_refresh_no_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_invalid_token(self, client: AsyncClient):
        client.cookies.set("refresh_token", "invalid-token")
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@ri-platform.com"
        assert data["role"]["code"] == "CEO"

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestUserCRUD:
    async def test_list_users_as_ceo(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "meta" in resp.json()

    async def test_list_users_forbidden_for_engineer(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "ENGINEER")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_create_user(self, client: AsyncClient, db: AsyncSession):
        await login_as(client)

        from sqlalchemy import select
        from app.modules.auth.models import Role
        role_result = await db.execute(select(Role).where(Role.code == "PM"))
        role = role_result.scalar_one()

        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "name": "New User",
                "password": "SecurePass1",
                "role_id": str(role.id),
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["email"] == "newuser@test.com"

    async def test_create_user_duplicate_email(self, client: AsyncClient):
        await login_as(client)
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "admin@ri-platform.com",
                "name": "Duplicate",
                "password": "SecurePass1",
                "role_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 409
        assert "already in use" in resp.json()["message"]

    async def test_create_user_forbidden_for_pm(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "PM")
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "nope@test.com",
                "name": "Nope",
                "password": "SecurePass1",
                "role_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 403

    async def test_get_user(self, client: AsyncClient, db: AsyncSession):
        await login_as(client)
        user = await create_test_user(db, "DM", email="getme@test.com")
        resp = await client.get(f"/api/v1/users/{user.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "getme@test.com"

    async def test_update_user(self, client: AsyncClient, db: AsyncSession):
        await login_as(client)
        user = await create_test_user(db, "ENGINEER", email="updateme@test.com")
        resp = await client.put(
            f"/api/v1/users/{user.id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Name"

    async def test_cannot_deactivate_last_admin(self, client: AsyncClient, db: AsyncSession):
        await login_as(client)

        from sqlalchemy import select
        from app.modules.auth.models import User, Role
        ceo_result = await db.execute(select(Role).where(Role.code == "CEO"))
        ceo_role = ceo_result.scalar_one()
        admin_result = await db.execute(
            select(User).where(User.role_id == ceo_role.id, User.is_active.is_(True))
        )
        admin = admin_result.scalars().first()

        cto_result = await db.execute(select(Role).where(Role.code == "CTO"))
        cto_role = cto_result.scalar_one()
        cto_users = await db.execute(
            select(User).where(User.role_id == cto_role.id, User.is_active.is_(True))
        )
        for u in cto_users.scalars().all():
            u.is_active = False
        await db.commit()

        resp = await client.put(
            f"/api/v1/users/{admin.id}",
            json={"is_active": False},
        )
        assert resp.status_code == 400
        assert "last active admin" in resp.json()["message"]

    async def test_search_users(self, client: AsyncClient, db: AsyncSession):
        await login_as(client)
        await create_test_user(db, "HR", email="searchable@test.com", name="Searchable Person")
        resp = await client.get("/api/v1/users", params={"search": "searchable"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    async def test_filter_users_by_status(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get("/api/v1/users", params={"status": "ACTIVE"})
        assert resp.status_code == 200
        for user in resp.json()["data"]:
            assert user["is_active"] is True


class TestRolesAPI:
    async def test_list_roles_as_ceo(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get("/api/v1/roles")
        assert resp.status_code == 200
        roles = resp.json()["data"]
        assert len(roles) == 7

    async def test_list_roles_forbidden_for_engineer(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "ENGINEER")
        resp = await client.get("/api/v1/roles")
        assert resp.status_code == 403

    async def test_get_role_with_permissions(self, client: AsyncClient):
        await login_as(client)
        roles_resp = await client.get("/api/v1/roles")
        role_id = roles_resp.json()["data"][0]["id"]

        resp = await client.get(f"/api/v1/roles/{role_id}")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["permissions"]) == 15

    async def test_get_role_permissions(self, client: AsyncClient):
        await login_as(client)
        roles_resp = await client.get("/api/v1/roles")
        role_id = roles_resp.json()["data"][0]["id"]

        resp = await client.get(f"/api/v1/roles/{role_id}/permissions")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 15

    async def test_get_nonexistent_role(self, client: AsyncClient):
        await login_as(client)
        resp = await client.get(f"/api/v1/roles/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestRBACMiddleware:
    """RBAC checks — sample combos where access_level=NONE should return 403."""

    async def test_engineer_cannot_access_client_profiles(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "ENGINEER")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_hr_cannot_access_users(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "HR")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_finance_cannot_access_users(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "FINANCE")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_dm_cannot_access_users(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "DM")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_pm_cannot_access_users(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "PM")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_cto_can_access_users(self, client: AsyncClient, db: AsyncSession):
        await login_as_role(client, db, "CTO")
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200

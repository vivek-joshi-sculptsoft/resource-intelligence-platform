import json
import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.modules.audit.models import AuditAction
from app.modules.audit.service import audit_log


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_create_action_logs_single_entry(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="project",
        entity_id=entity_id,
        action=AuditAction.CREATE,
        changes={"name": "Project Phoenix"},
        user_id=user_id,
    )

    assert len(entries) == 1
    assert entries[0].action == AuditAction.CREATE
    assert entries[0].entity_type == "project"
    assert entries[0].field_name is None
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_update_action_logs_one_row_per_changed_field(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="resource",
        entity_id=entity_id,
        action=AuditAction.UPDATE,
        changes={
            "name": ("Old Name", "New Name"),
            "email": ("old@test.com", "new@test.com"),
        },
        user_id=user_id,
    )

    assert len(entries) == 2
    field_names = {e.field_name for e in entries}
    assert field_names == {"name", "email"}
    assert mock_db.add.call_count == 2


@pytest.mark.asyncio
async def test_update_skips_unchanged_fields(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="resource",
        entity_id=entity_id,
        action=AuditAction.UPDATE,
        changes={
            "name": ("Same", "Same"),
            "email": ("old@test.com", "new@test.com"),
        },
        user_id=user_id,
    )

    assert len(entries) == 1
    assert entries[0].field_name == "email"


@pytest.mark.asyncio
async def test_delete_action_logs_single_entry(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="client",
        entity_id=entity_id,
        action=AuditAction.DELETE,
        user_id=user_id,
    )

    assert len(entries) == 1
    assert entries[0].action == AuditAction.DELETE
    assert entries[0].old_value is None


@pytest.mark.asyncio
async def test_system_user_gets_zero_uuid(mock_db):
    entity_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="config",
        entity_id=entity_id,
        action=AuditAction.CREATE,
    )

    assert entries[0].changed_by == uuid.UUID(int=0)


@pytest.mark.asyncio
async def test_old_new_values_are_json_serialized(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="project",
        entity_id=entity_id,
        action=AuditAction.UPDATE,
        changes={"budget": (50000, 75000)},
        user_id=user_id,
    )

    assert entries[0].old_value == "50000"
    assert entries[0].new_value == "75000"


@pytest.mark.asyncio
async def test_update_with_no_changes_returns_empty(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()

    entries = await audit_log(
        mock_db,
        entity_type="project",
        entity_id=entity_id,
        action=AuditAction.UPDATE,
        changes=None,
        user_id=user_id,
    )

    assert len(entries) == 0
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_metadata_passed_through(mock_db):
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()
    meta = {"ip": "192.168.1.1", "source": "api"}

    entries = await audit_log(
        mock_db,
        entity_type="user",
        entity_id=entity_id,
        action=AuditAction.CREATE,
        metadata=meta,
        user_id=user_id,
    )

    assert entries[0].metadata_ == meta

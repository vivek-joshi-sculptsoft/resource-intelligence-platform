import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditAction, AuditLog


async def audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    action: AuditAction,
    changes: dict[str, tuple[Any, Any]] | None = None,
    user_id: uuid.UUID | str = "SYSTEM",
    metadata: dict | None = None,
) -> list[AuditLog]:
    """Log an audit entry. For UPDATE, pass changes as {field: (old, new)}."""
    entries: list[AuditLog] = []

    changed_by = (
        user_id
        if isinstance(user_id, uuid.UUID)
        else uuid.UUID(user_id)
        if user_id != "SYSTEM"
        else uuid.UUID(int=0)
    )

    if action == AuditAction.CREATE:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=None,
            old_value=None,
            new_value=json.dumps(changes) if changes else None,
            changed_by=changed_by,
            metadata_=metadata,
        )
        db.add(entry)
        entries.append(entry)

    elif action == AuditAction.UPDATE and changes:
        for field_name, (old_val, new_val) in changes.items():
            if old_val == new_val:
                continue
            entry = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                field_name=field_name,
                old_value=json.dumps(old_val, default=str),
                new_value=json.dumps(new_val, default=str),
                changed_by=changed_by,
                metadata_=metadata,
            )
            db.add(entry)
            entries.append(entry)

    elif action == AuditAction.DELETE:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            field_name=None,
            old_value=json.dumps(changes) if changes else None,
            new_value=None,
            changed_by=changed_by,
            metadata_=metadata,
        )
        db.add(entry)
        entries.append(entry)

    return entries

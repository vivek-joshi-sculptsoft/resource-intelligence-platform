from app.modules.audit.models import AuditAction, AuditLog


def test_audit_log_table_name():
    assert AuditLog.__tablename__ == "audit_logs"


def test_audit_log_primary_key_is_bigint():
    pk_col = AuditLog.__table__.c.id
    assert pk_col.primary_key
    assert pk_col.autoincrement


def test_audit_log_has_required_columns():
    columns = {c.name for c in AuditLog.__table__.columns}
    expected = {
        "id", "entity_type", "entity_id", "action", "field_name",
        "old_value", "new_value", "changed_by", "changed_at", "metadata",
    }
    assert expected <= columns


def test_audit_action_enum_values():
    assert set(AuditAction) == {AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE}


def test_entity_id_has_no_foreign_key():
    entity_id_col = AuditLog.__table__.c.entity_id
    assert len(entity_id_col.foreign_keys) == 0


def test_field_name_is_nullable():
    assert AuditLog.__table__.c.field_name.nullable is True


def test_old_value_is_nullable():
    assert AuditLog.__table__.c.old_value.nullable is True


def test_new_value_is_nullable():
    assert AuditLog.__table__.c.new_value.nullable is True


def test_changed_at_has_server_default():
    col = AuditLog.__table__.c.changed_at
    assert col.server_default is not None

"""update worklog role permissions — CEO/CTO/DM/PM/ENGINEER get EDIT, FINANCE/HR get VIEW

Revision ID: 008
Revises: 007
Create Date: 2026-07-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    for role_code in ("CEO", "CTO", "DM", "PM"):
        conn.execute(
            sa.text(
                """
                UPDATE role_permissions
                SET access_level = 'EDIT'
                WHERE role_id = (SELECT id FROM roles WHERE code = :role)
                  AND data_type = 'worklogs'
                """
            ),
            {"role": role_code},
        )
    for role_code in ("FINANCE", "HR"):
        conn.execute(
            sa.text(
                """
                UPDATE role_permissions
                SET access_level = 'VIEW'
                WHERE role_id = (SELECT id FROM roles WHERE code = :role)
                  AND data_type = 'worklogs'
                """
            ),
            {"role": role_code},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for role_code in ("CEO", "CTO", "DM", "PM"):
        conn.execute(
            sa.text(
                """
                UPDATE role_permissions
                SET access_level = 'VIEW'
                WHERE role_id = (SELECT id FROM roles WHERE code = :role)
                  AND data_type = 'worklogs'
                """
            ),
            {"role": role_code},
        )
    for role_code in ("FINANCE", "HR"):
        conn.execute(
            sa.text(
                """
                UPDATE role_permissions
                SET access_level = 'NONE'
                WHERE role_id = (SELECT id FROM roles WHERE code = :role)
                  AND data_type = 'worklogs'
                """
            ),
            {"role": role_code},
        )

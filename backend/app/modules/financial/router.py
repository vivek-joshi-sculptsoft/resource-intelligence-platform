"""See modules/08-financial-engine/API.md — GET /api/projects/:projectId/financials."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.financial.service import get_project_financials
from app.modules.projects.models import Project
from app.shared.access_control import can_see_field, check_access, has_access
from app.shared.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/api/v1/projects", tags=["financial"])


@router.get("/{project_id}/financials")
async def get_project_financials_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See ACCESS-MATRIX.md — project_margin: CEO/CTO/Finance (ALL), DM (OWN_PORTFOLIO)
    permission = await check_access(db, current_user, "project_margin")

    project = (
        await db.execute(select(Project).where(Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project", str(project_id))

    # See FSD §10 — OWN_PORTFOLIO for project_margin means dm_id = user's resource_id
    if permission.is_own_portfolio:
        if not current_user.resource_id or project.dm_id != current_user.resource_id:
            raise ForbiddenError()

    role_code = current_user.role.code
    data = await get_project_financials(
        db,
        project,
        can_see_cost=can_see_field(role_code, "loaded_cost_monthly"),
        can_see_rate=can_see_field(role_code, "billing_rate"),
        can_see_invoicing=await has_access(db, current_user, "invoicing"),
        can_see_nonhuman=await has_access(db, current_user, "non_human_costs"),
    )
    return {"data": data.model_dump()}

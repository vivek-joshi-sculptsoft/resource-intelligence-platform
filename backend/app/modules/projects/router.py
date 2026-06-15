import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.projects.schemas import (
    ProjectCreateRequest,
    ProjectStatusRequest,
    ProjectUpdateRequest,
)
from app.modules.projects.service import (
    _project_to_detail,
    create_project,
    get_project,
    list_projects,
    transition_project_status,
    update_project,
)
from app.shared.access_control import check_access
from app.shared.exceptions import ForbiddenError
from app.shared.utils import build_pagination_meta

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

# See FSD §10 — PM can only edit these fields on projects
PM_EDITABLE_FIELDS = {"worklog_enabled", "notes"}


def _check_portfolio_scope(project, permission, current_user: User) -> None:
    """See FSD §10 — OWN_PORTFOLIO means dm_id or pm_id = user's resource_id."""
    if not permission.is_own_portfolio:
        return
    if current_user.resource_id and (
        project.dm_id == current_user.resource_id or project.pm_id == current_user.resource_id
    ):
        return
    raise ForbiddenError()


@router.get("")
async def list_projects_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    client_id: uuid.UUID | None = Query(None),
    type: str | None = Query(None),
    dm_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See FSD §10 — project_details access check
    permission = await check_access(db, current_user, "project_details")

    items, total = await list_projects(
        db,
        permission=permission,
        current_user=current_user,
        page=page,
        limit=limit,
        status=status,
        client_id=client_id,
        project_type=type,
        dm_id=dm_id,
        search=search,
    )

    return {
        "data": items,
        "meta": build_pagination_meta(total, page, limit),
    }


@router.post("", status_code=201)
async def create_project_endpoint(
    body: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "project_details", require_edit=True)
    role_code = current_user.role.code

    # See VRIP-46 — PM cannot create projects
    if role_code == "PM":
        raise ForbiddenError()

    # See VRIP-46 — DM creating project must set dm_id to self
    dm_id = body.dm_id
    if role_code == "DM" and current_user.resource_id:
        dm_id = current_user.resource_id

    project = await create_project(
        db,
        name=body.name,
        client_id=body.client_id,
        project_type=body.type.value,
        billing_currency=body.billing_currency,
        start_date=body.start_date,
        contract_end_date=body.contract_end_date,
        dm_id=dm_id,
        pm_id=body.pm_id,
        worklog_enabled=body.worklog_enabled,
        notes=body.notes,
        current_user_id=current_user.id,
    )
    return {"data": _project_to_detail(project)}


@router.get("/{project_id}")
async def get_project_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "project_details")
    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)
    return {"data": _project_to_detail(project)}


@router.put("/{project_id}")
async def update_project_endpoint(
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "project_details", require_edit=True)
    role_code = current_user.role.code

    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    fields = body.model_dump(exclude_unset=True)
    if "type" in fields and fields["type"] is not None:
        fields["type"] = fields["type"].value

    # See VRIP-46 — PM can only edit worklog_enabled and notes
    if role_code == "PM":
        disallowed = set(fields.keys()) - PM_EDITABLE_FIELDS
        if disallowed:
            raise ForbiddenError(f"PM cannot edit fields: {', '.join(sorted(disallowed))}")

    project = await update_project(
        db,
        project_id=project_id,
        current_user_id=current_user.id,
        **fields,
    )
    return {"data": _project_to_detail(project)}


@router.put("/{project_id}/status")
async def transition_project_status_endpoint(
    project_id: uuid.UUID,
    body: ProjectStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "project_details", require_edit=True)
    role_code = current_user.role.code

    # See VRIP-46 — PM cannot transition project status
    if role_code == "PM":
        raise ForbiddenError()

    project = await get_project(db, project_id)
    _check_portfolio_scope(project, permission, current_user)

    project = await transition_project_status(
        db,
        project_id=project_id,
        new_status=body.status.value,
        current_user_id=current_user.id,
    )
    return {"data": _project_to_detail(project)}

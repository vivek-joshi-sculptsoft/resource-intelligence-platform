import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.models import User
from app.modules.resources.schemas import (
    ResourceCreateRequest,
    ResourceUpdateRequest,
    TagRequest,
)
from app.modules.resources.service import (
    add_tag,
    create_resource,
    deactivate_resource,
    get_resource,
    list_resources,
    remove_tag,
    update_resource,
)
from app.shared.access_control import can_see_field, check_access
from app.shared.utils import build_pagination_meta

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


def _resource_to_list_item(r: dict, role_code: str) -> dict:
    item = dict(r)
    if not can_see_field(role_code, "loaded_cost_monthly"):
        item["loaded_cost_monthly"] = None
    return item


def _resource_to_detail(resource, role_code: str, alloc_pct: int) -> dict:
    mgr = None
    if resource.reporting_manager:
        mgr = {"id": resource.reporting_manager.id, "name": resource.reporting_manager.name}

    detail = {
        "id": resource.id,
        "employee_id": resource.employee_id,
        "name": resource.name,
        "designation": resource.designation,
        "technical_expertise": resource.technical_expertise,
        "date_of_joining": (
            resource.date_of_joining.isoformat() if resource.date_of_joining else None
        ),
        "reporting_manager": mgr,
        "loaded_cost_monthly": (
            float(resource.loaded_cost_monthly)
            if resource.loaded_cost_monthly and can_see_field(role_code, "loaded_cost_monthly")
            else None
        ),
        "is_active": resource.is_active,
        "tags": [t.tag for t in resource.tags],
        "total_allocation_pct": alloc_pct,
        "created_at": resource.created_at.isoformat() if resource.created_at else "",
    }
    return detail


@router.get("")
async def list_resources_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    designation: str | None = Query(None),
    expertise: str | None = Query(None),
    tag: str | None = Query(None),
    availability: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # See FSD §10 — resource_profiles access check
    permission = await check_access(db, current_user, "resource_profiles")

    items, total = await list_resources(
        db,
        permission=permission,
        current_user=current_user,
        page=page,
        limit=limit,
        status=status,
        designation=designation,
        expertise=expertise,
        tag=tag,
        availability=availability,
        search=search,
    )

    role_code = current_user.role.code
    return {
        "data": [_resource_to_list_item(r, role_code) for r in items],
        "meta": build_pagination_meta(total, page, limit),
    }


@router.post("", status_code=201)
async def create_resource_endpoint(
    body: ResourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "resource_profiles", require_edit=True)

    # See FSD §10 — loaded_cost_monthly restricted to CEO/CTO/Finance
    role_code = current_user.role.code
    cost_value = None
    if body.loaded_cost_monthly is not None:
        if not can_see_field(role_code, "loaded_cost_monthly"):
            from app.shared.exceptions import ForbiddenError

            raise ForbiddenError("Not authorized to set loaded_cost_monthly")
        cost_value = body.loaded_cost_monthly

    resource = await create_resource(
        db,
        employee_id=body.employee_id,
        name=body.name,
        designation=body.designation,
        technical_expertise=body.technical_expertise,
        date_of_joining=body.date_of_joining,
        reporting_manager_id=body.reporting_manager_id,
        tags=body.tags,
        current_user_id=current_user.id,
        loaded_cost_monthly=cost_value,
    )
    from app.modules.resources.service import _get_total_allocation

    alloc = await _get_total_allocation(db, resource.id)
    return {"data": _resource_to_detail(resource, role_code, alloc)}


@router.get("/{resource_id}")
async def get_resource_endpoint(
    resource_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    permission = await check_access(db, current_user, "resource_profiles")

    if permission.is_self_only and current_user.resource_id != resource_id:
        from app.shared.exceptions import ForbiddenError

        raise ForbiddenError()

    resource = await get_resource(db, resource_id)

    from app.modules.resources.service import _get_total_allocation

    alloc = await _get_total_allocation(db, resource.id)
    return {"data": _resource_to_detail(resource, current_user.role.code, alloc)}


@router.put("/{resource_id}")
async def update_resource_endpoint(
    resource_id: uuid.UUID,
    body: ResourceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    fields = body.model_dump(exclude_unset=True)
    role_code = current_user.role.code
    has_cost_field = "loaded_cost_monthly" in fields
    has_profile_fields = any(k != "loaded_cost_monthly" for k in fields)

    # See FSD §10 — Profile fields require resource_profiles EDIT
    if has_profile_fields:
        await check_access(db, current_user, "resource_profiles", require_edit=True)
    elif has_cost_field:
        # Finance has VIEW on resource_profiles but can edit loaded_cost_monthly
        await check_access(db, current_user, "resource_profiles")

    # See FSD §10 — loaded_cost_monthly write restricted to CEO/CTO/Finance
    if has_cost_field and not can_see_field(role_code, "loaded_cost_monthly"):
        from app.shared.exceptions import ForbiddenError

        raise ForbiddenError("Not authorized to update loaded_cost_monthly")

    resource = await update_resource(
        db,
        resource_id=resource_id,
        current_user_id=current_user.id,
        **fields,
    )

    from app.modules.resources.service import _get_total_allocation

    alloc = await _get_total_allocation(db, resource.id)
    return {"data": _resource_to_detail(resource, role_code, alloc)}


@router.delete("/{resource_id}")
async def delete_resource_endpoint(
    resource_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "resource_profiles", require_edit=True)
    await deactivate_resource(db, resource_id, current_user.id)
    return {"success": True}


@router.post("/{resource_id}/tags")
async def add_tag_endpoint(
    resource_id: uuid.UUID,
    body: TagRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "resource_profiles", require_edit=True)
    tags = await add_tag(db, resource_id, body.tag, current_user.id)
    return {"data": {"tags": tags}}


@router.delete("/{resource_id}/tags/{tag}")
async def remove_tag_endpoint(
    resource_id: uuid.UUID,
    tag: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await check_access(db, current_user, "resource_profiles", require_edit=True)
    tags = await remove_tag(db, resource_id, tag, current_user.id)
    return {"data": {"tags": tags}}

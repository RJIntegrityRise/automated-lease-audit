from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import CurrentUser, require_admin
from app.core.supabase import get_supabase_client


router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin Users"],
)


AdminAction = Literal[
    "approve",
    "reject",
    "enable",
    "disable",
    "set_role",
]

UserRole = Literal[
    "master_admin",
    "admin",
    "manager",
    "reviewer",
]


class AdminUserUpdate(BaseModel):
    action: AdminAction
    role: UserRole | None = None


def get_profile_or_404(user_id: str) -> dict:
    supabase = get_supabase_client()

    response = (
        supabase.table("profiles")
        .select(
            "id, full_name, role, active, "
            "approval_status, approved_by, "
            "approved_at, created_at"
        )
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return response.data[0]


def require_master_for_privileged_target(
    current_user: CurrentUser,
    target_profile: dict,
) -> None:
    target_role = target_profile["role"]

    if target_role in {
        "admin",
        "master_admin",
    } and current_user.role != "master_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only a master administrator can "
                "manage administrators."
            ),
        )


def count_active_master_admins() -> int:
    supabase = get_supabase_client()

    response = (
        supabase.table("profiles")
        .select("id")
        .eq("role", "master_admin")
        .eq("active", True)
        .eq("approval_status", "approved")
        .execute()
    )

    return len(response.data or [])


def protect_master_admin_count(
    target_profile: dict,
) -> None:
    if (
        target_profile["role"] == "master_admin"
        and target_profile["active"]
        and target_profile["approval_status"]
        == "approved"
        and count_active_master_admins() <= 2
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "At least two active master "
                "administrators must remain. "
                "Promote another master administrator "
                "before removing this one."
            ),
        )


@router.get("")
def list_users(
    current_user: CurrentUser = Depends(
        require_admin
    ),
) -> list[dict]:
    supabase = get_supabase_client()

    profiles_response = (
        supabase.table("profiles")
        .select(
            "id, full_name, role, active, "
            "approval_status, approved_by, "
            "approved_at, created_at"
        )
        .order("created_at")
        .execute()
    )

    profiles = profiles_response.data or []

    try:
        auth_users = (
            supabase.auth.admin.list_users()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load authentication users.",
        ) from exc

    email_by_id: dict[str, str | None] = {}

    for auth_user in auth_users:
        email_by_id[str(auth_user.id)] = (
            auth_user.email
        )

    return [
        {
            **profile,
            "email": email_by_id.get(
                str(profile["id"])
            ),
        }
        for profile in profiles
    ]


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    current_user: CurrentUser = Depends(
        require_admin
    ),
) -> dict:
    supabase = get_supabase_client()

    target = get_profile_or_404(user_id)

    require_master_for_privileged_target(
        current_user,
        target,
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    updates: dict = {
        "updated_at": now,
    }

    if payload.action == "approve":
        updates.update(
            {
                "approval_status": "approved",
                "active": True,
                "approved_by": current_user.id,
                "approved_at": now,
            }
        )

    elif payload.action == "reject":
        protect_master_admin_count(target)

        updates.update(
            {
                "approval_status": "rejected",
                "active": False,
            }
        )

    elif payload.action == "enable":
        updates["active"] = True

    elif payload.action == "disable":
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot disable your own "
                    "account."
                ),
            )

        protect_master_admin_count(target)

        updates["active"] = False

    elif payload.action == "set_role":
        if payload.role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A role is required.",
            )

        if current_user.role != "master_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only a master administrator "
                    "can change user roles."
                ),
            )

        if (
            target["role"] == "master_admin"
            and payload.role != "master_admin"
        ):
            if user_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "You cannot demote your own "
                        "master administrator account."
                    ),
                )

            protect_master_admin_count(target)

        updates["role"] = payload.role

    response = (
        supabase.table("profiles")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed.",
        )

    return {
        "message": "User updated successfully.",
        "user": response.data[0],
    }
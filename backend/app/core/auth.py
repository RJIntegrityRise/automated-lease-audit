from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.supabase import get_supabase_client


security = HTTPBearer()


UserRole = Literal[
    "master_admin",
    "admin",
    "manager",
    "reviewer",
]


class CurrentUser(BaseModel):
    id: str
    email: str | None = None
    full_name: str | None = None
    role: UserRole
    active: bool
    approval_status: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    token = credentials.credentials
    supabase = get_supabase_client()

    try:
        user_response = supabase.auth.get_user(token)
        auth_user = user_response.user
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    response = (
        supabase.table("profiles")
        .select(
            "id, full_name, role, active, approval_status"
        )
        .eq("id", str(auth_user.id))
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile not found.",
        )

    profile = response.data[0]

    if not profile["active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled.",
        )

    if profile["approval_status"] != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not approved.",
        )

    return CurrentUser(
        id=str(auth_user.id),
        email=auth_user.email,
        full_name=profile.get("full_name"),
        role=profile["role"],
        active=profile["active"],
        approval_status=profile[
            "approval_status"
        ],
    )


def require_admin(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
) -> CurrentUser:
    if current_user.role not in {
        "admin",
        "master_admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user


def require_master_admin(
    current_user: CurrentUser = Depends(
        get_current_user
    ),
) -> CurrentUser:
    if current_user.role != "master_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master administrator access required.",
        )

    return current_user
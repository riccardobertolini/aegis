"""Security API router — auth, sessions, audit, model integrity, key rotation, backup."""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from backend.infrastructure.security.dependencies import (
    CurrentUser,
    require_permission,
)
from backend.infrastructure.security.service import SecurityService
from backend.domain.ports.security import Permission

router = APIRouter(prefix="/security", tags=["security"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=12)
    role_names: list[str] = Field(default_factory=lambda: ["viewer"])


class UserResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class RoleAssignRequest(BaseModel):
    user_id: str
    role_names: list[str]


class AuditQueryParams(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class KeyRotateRequest(BaseModel):
    new_passphrase: Optional[str] = None  # if None, reuses existing passphrase


class ModelRegisterRequest(BaseModel):
    model_path: str = Field(..., description="Absolute path on the local filesystem")
    model_id: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


def _get_security_service() -> SecurityService:
    """Placeholder — replaced by the DI container wiring in main.py."""
    raise RuntimeError("SecurityService not wired — call register_security(app, container)")


SecurityDep = Annotated[SecurityService, Depends(_get_security_service)]


@router.post("/login", response_model=TokenResponse, summary="Authenticate and obtain JWT")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    svc: SecurityDep,
):
    """Username + password → JWT access token (local, no external IdP)."""
    result = await svc.authenticate(form.username, form.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=result["token"],
        expires_in=result["expires_in"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke current session")
async def logout(
    current_user: CurrentUser,
    svc: SecurityDep,
    token: Annotated[str, Depends(require_permission(Permission.SYSTEM_VIEW))],
):
    await svc.revoke_session(current_user.session_id)


@router.get("/sessions", summary="List active sessions for current user")
async def list_sessions(
    current_user: CurrentUser,
    svc: SecurityDep,
):
    return await svc.list_user_sessions(current_user.user_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    current_user: CurrentUser,
    svc: SecurityDep,
):
    """Revoke any session owned by the current user (or any, if SUPERADMIN)."""
    await svc.revoke_session(session_id, requesting_user=current_user)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest,
    _: Annotated[None, Depends(require_permission(Permission.USER_WRITE))],
    svc: SecurityDep,
):
    return await svc.create_user(body.username, body.password, body.role_names)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: Annotated[None, Depends(require_permission(Permission.USER_READ))],
    svc: SecurityDep,
    active_only: bool = Query(default=True),
):
    return await svc.list_users(active_only=active_only)


@router.patch("/users/{user_id}/roles", response_model=UserResponse)
async def assign_roles(
    user_id: str,
    body: RoleAssignRequest,
    _: Annotated[None, Depends(require_permission(Permission.USER_WRITE))],
    svc: SecurityDep,
):
    return await svc.assign_roles(user_id, body.role_names)


@router.patch("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    _: Annotated[None, Depends(require_permission(Permission.USER_WRITE))],
    svc: SecurityDep,
):
    await svc.deactivate_user(user_id)


@router.post("/users/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    svc: SecurityDep,
):
    await svc.change_password(current_user.user_id, body.current_password, body.new_password)


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


@router.get("/audit", summary="Query immutable audit log")
async def query_audit(
    _: Annotated[None, Depends(require_permission(Permission.AUDIT_READ))],
    svc: SecurityDep,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    return await svc.query_audit(
        user_id=user_id,
        action=action,
        resource=resource,
        since=since,
        until=until,
        limit=limit,
    )


@router.post("/audit/verify", summary="Verify HMAC chain integrity")
async def verify_audit_chain(
    _: Annotated[None, Depends(require_permission(Permission.AUDIT_READ))],
    svc: SecurityDep,
):
    ok, first_broken = await svc.verify_audit_chain()
    return {"ok": ok, "first_broken_id": first_broken}


# ---------------------------------------------------------------------------
# Model integrity
# ---------------------------------------------------------------------------


@router.post("/models/register", status_code=status.HTTP_201_CREATED)
async def register_model(
    body: ModelRegisterRequest,
    _: Annotated[None, Depends(require_permission(Permission.MODEL_WRITE))],
    svc: SecurityDep,
):
    result = await svc.register_model_hash(body.model_id, body.model_path)
    return {"model_id": body.model_id, "sha256": result.expected_hash}


@router.post("/models/{model_id}/verify")
async def verify_model(
    model_id: str,
    model_path: str = Query(...),
    _: Annotated[None, Depends(require_permission(Permission.MODEL_READ))],
    svc: SecurityDep,
):
    result = await svc.verify_model_integrity(model_id, model_path)
    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "model_id": model_id,
                "expected": result.expected_hash,
                "actual": result.actual_hash,
                "message": "Model file hash mismatch — possible tampering",
            },
        )
    return {"ok": True, "model_id": model_id, "sha256": result.expected_hash}


# ---------------------------------------------------------------------------
# Encryption key management
# ---------------------------------------------------------------------------


@router.post("/keys/rotate", summary="Rotate encryption master key")
async def rotate_key(
    body: KeyRotateRequest,
    _: Annotated[None, Depends(require_permission(Permission.KEY_ROTATE))],
    svc: SecurityDep,
):
    new_kid = await svc.rotate_encryption_key(body.new_passphrase)
    return {"new_key_id": new_kid}


@router.get("/keys", summary="List key IDs (no secrets)")
async def list_keys(
    _: Annotated[None, Depends(require_permission(Permission.KEY_ROTATE))],
    svc: SecurityDep,
):
    return await svc.list_key_ids()


# ---------------------------------------------------------------------------
# Encrypted backup
# ---------------------------------------------------------------------------


@router.post("/backup/create", summary="Create encrypted offline backup (.aeb)")
async def create_backup(
    _: Annotated[None, Depends(require_permission(Permission.BACKUP_WRITE))],
    svc: SecurityDep,
    target_dir: str = Query(default="./backups"),
):
    path = await svc.create_backup(target_dir)
    return {"backup_path": path}


@router.post("/backup/restore", summary="Restore from encrypted backup")
async def restore_backup(
    _: Annotated[None, Depends(require_permission(Permission.BACKUP_WRITE))],
    svc: SecurityDep,
    backup_path: str = Query(...),
    restore_dir: str = Query(default="./restore"),
):
    await svc.restore_backup(backup_path, restore_dir)
    return {"restored_to": restore_dir}


@router.get("/backup/list", summary="List available local backups")
async def list_backups(
    _: Annotated[None, Depends(require_permission(Permission.BACKUP_READ))],
    svc: SecurityDep,
    backup_dir: str = Query(default="./backups"),
):
    return await svc.list_backups(backup_dir)

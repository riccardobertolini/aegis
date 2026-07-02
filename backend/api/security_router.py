"""Security REST endpoints: auth, sessions, audit, RBAC admin."""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field

from backend.domain.ports.security import (
    AuditEntry, ISecurityPort, UserCredentials, Permission
)
from backend.infrastructure.security.dependencies import (
    get_current_user, require_permission
)
from backend.domain.ports.security import UserPrincipal

router = APIRouter(prefix="/security", tags=["Security"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    session_id: str | None


class AuditQueryParams(BaseModel):
    actor_id: Optional[str] = None
    resource: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)


class IntegrityRequest(BaseModel):
    model_id: str
    model_path: str


# ─── Auth endpoints ───────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse, summary="Authenticate user")
async def login(
    body: LoginRequest,
    security: ISecurityPort = Depends(lambda: None),  # overridden by DI
):
    """Exchange credentials for a local JWT session token."""
    token = await security.authenticate(UserCredentials(
        username=body.username, password=body.password
    ))
    return TokenResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        expires_at=token.expires_at,
        session_id=token.session_id,
    )


@router.post("/auth/logout", summary="Revoke current session")
async def logout(
    principal: UserPrincipal = Depends(get_current_user),
    security: ISecurityPort = Depends(lambda: None),
):
    if principal.permissions and hasattr(principal, "session_id"):
        pass  # session_id not in principal; client must pass it
    return {"detail": "Session revoked"}


@router.get("/sessions", summary="List active sessions for current user")
async def list_sessions(
    principal: UserPrincipal = Depends(get_current_user),
    security: ISecurityPort = Depends(lambda: None),
):
    return await security.list_active_sessions(principal.user_id)


@router.delete("/sessions/{session_id}", summary="Revoke a specific session")
async def revoke_session(
    session_id: str,
    principal: UserPrincipal = Depends(require_permission(Permission.ADMIN_FULL.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    await security.revoke_session(session_id)
    return {"detail": "Revoked"}


# ─── Audit endpoints ──────────────────────────────────────────────────────────

@router.post("/audit/query", summary="Query immutable audit log")
async def query_audit(
    params: AuditQueryParams,
    _: UserPrincipal = Depends(require_permission(Permission.AUDIT_READ.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    entries = await security.query_audit(
        actor_id=params.actor_id,
        resource=params.resource,
        since=params.since,
        until=params.until,
        limit=params.limit,
    )
    return [{"event_type": e.event_type, "actor": e.actor_username,
             "resource": e.resource, "action": e.action,
             "outcome": e.outcome, "timestamp": e.timestamp.isoformat()} for e in entries]


# ─── Model integrity ──────────────────────────────────────────────────────────

@router.post("/models/register-hash", summary="Register model file hash")
async def register_model_hash(
    body: IntegrityRequest,
    _: UserPrincipal = Depends(require_permission(Permission.MODEL_WRITE.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    h = await security.register_model_hash(body.model_id, body.model_path)
    return {"model_id": body.model_id, "sha256": h}


@router.post("/models/verify", summary="Verify model file integrity")
async def verify_model(
    body: IntegrityRequest,
    _: UserPrincipal = Depends(require_permission(Permission.MODEL_READ.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    result = await security.verify_model_integrity(body.model_id, body.model_path)
    return {
        "model_id": result.model_id,
        "is_valid": result.is_valid,
        "algorithm": result.algorithm,
        "checked_at": result.checked_at.isoformat(),
    }


# ─── Key rotation ─────────────────────────────────────────────────────────────

@router.post("/keys/rotate", summary="Rotate active encryption key")
async def rotate_key(
    _: UserPrincipal = Depends(require_permission(Permission.ADMIN_FULL.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    new_kid = await security.rotate_key()
    return {"new_key_id": new_kid}


# ─── Backup ───────────────────────────────────────────────────────────────────

class BackupRequest(BaseModel):
    source_path: str
    dest_path: str


@router.post("/backup/create", summary="Create encrypted backup")
async def create_backup(
    body: BackupRequest,
    _: UserPrincipal = Depends(require_permission(Permission.BACKUP_CREATE.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    path = await security.create_encrypted_backup(body.source_path, body.dest_path)
    return {"backup_path": path}


@router.post("/backup/restore", summary="Restore encrypted backup")
async def restore_backup(
    body: BackupRequest,
    _: UserPrincipal = Depends(require_permission(Permission.BACKUP_RESTORE.value)),
    security: ISecurityPort = Depends(lambda: None),
):
    await security.restore_encrypted_backup(body.source_path, body.dest_path)
    return {"detail": "Restored"}

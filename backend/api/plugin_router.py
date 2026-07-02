"""Plugin Engine REST API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


def _get_plugin_service():
    raise HTTPException(status_code=503, detail="PluginService not initialised")


class CallIn(BaseModel):
    method: str = Field(..., min_length=1)
    payload: dict = Field(default_factory=dict)


class ManifestOut(BaseModel):
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    permissions: list[str]
    entry_point: str
    status: str
    installed_at: str | None
    checksum: str | None


class CallOut(BaseModel):
    plugin_id: str
    method: str
    result: dict
    elapsed_ms: float
    error: str | None = None


def _manifest_out(m) -> ManifestOut:
    return ManifestOut(
        plugin_id=m.plugin_id,
        name=m.name,
        version=m.version,
        description=m.description,
        author=m.author,
        permissions=m.permissions,
        entry_point=m.entry_point,
        status=m.status.value,
        installed_at=m.installed_at.isoformat() if m.installed_at else None,
        checksum=m.checksum,
    )


@router.get("", response_model=list[ManifestOut])
async def list_plugins(svc=Depends(_get_plugin_service)):
    return [_manifest_out(m) for m in await svc.list_plugins()]


@router.get("/{plugin_id}", response_model=ManifestOut)
async def get_plugin(plugin_id: str, svc=Depends(_get_plugin_service)):
    m = await svc.get_manifest(plugin_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
    return _manifest_out(m)


@router.post("/{plugin_id}/enable", status_code=204)
async def enable_plugin(plugin_id: str, svc=Depends(_get_plugin_service)):
    await svc.enable(plugin_id)


@router.post("/{plugin_id}/disable", status_code=204)
async def disable_plugin(plugin_id: str, svc=Depends(_get_plugin_service)):
    await svc.disable(plugin_id)


@router.post("/{plugin_id}/call", response_model=CallOut)
async def call_plugin(
    plugin_id: str, body: CallIn, svc=Depends(_get_plugin_service)
):
    result = await svc.call(plugin_id, body.method, body.payload)
    return CallOut(
        plugin_id=result.plugin_id,
        method=result.method,
        result=result.result,
        elapsed_ms=result.elapsed_ms,
        error=result.error,
    )


@router.get("/{plugin_id}/integrity")
async def check_integrity(plugin_id: str, svc=Depends(_get_plugin_service)):
    ok = await svc.verify_integrity(plugin_id)
    return {"plugin_id": plugin_id, "integrity_ok": ok}


@router.delete("/{plugin_id}", status_code=204)
async def uninstall_plugin(plugin_id: str, svc=Depends(_get_plugin_service)):
    await svc.uninstall(plugin_id)

"""DI factory for plugin engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.infrastructure.plugin.service import PluginService


@dataclass
class PluginContainer:
    service: PluginService


def build_plugin_container(
    plugins_root: Path,
    signing_key: bytes | None = None,
) -> PluginContainer:
    return PluginContainer(service=PluginService(plugins_root=plugins_root, signing_key=signing_key))

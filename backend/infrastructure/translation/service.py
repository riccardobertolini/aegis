"""TranslationService — local translation via Argos Translate (offline)."""
from __future__ import annotations

import logging

from backend.domain.ports.translation import ITranslationPort, TranslationRequest, TranslationResult

logger = logging.getLogger(__name__)


class ArgosTranslationService(ITranslationPort):
    """
    Fully offline translation using Argos Translate.
    Language packages must be pre-installed in the local Argos packages directory.
    No network calls; local_packages_dir controls where packages are loaded from.

    Fallback: if argostranslate is not installed, returns source text unchanged
    with a warning (allows the rest of the platform to function).
    """

    def __init__(self, packages_dir: str | None = None):
        self._packages_dir = packages_dir
        self._initialised = False

    def _init(self) -> None:
        if self._initialised:
            return
        try:
            import argostranslate.package  # type: ignore
            if self._packages_dir:
                import argostranslate.settings  # type: ignore
                argostranslate.settings.data_dir = self._packages_dir
            argostranslate.package.load_installed_packages()
            self._initialised = True
        except ImportError:
            logger.warning("argostranslate not installed; translation will be a no-op.")
            self._initialised = True

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        self._init()
        try:
            import argostranslate.translate as argt  # type: ignore
            translated = argt.translate(
                request.text,
                request.source_lang,
                request.target_lang,
            )
            return TranslationResult(
                text=translated,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
            )
        except Exception as exc:
            logger.warning("Translation failed (%s); returning source text.", exc)
            return TranslationResult(
                text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                error=str(exc),
            )

    async def list_language_pairs(self) -> list[tuple[str, str]]:
        self._init()
        try:
            import argostranslate.package as argopkg  # type: ignore
            return [
                (pkg.from_code, pkg.to_code)
                for pkg in argopkg.get_installed_packages()
            ]
        except Exception:
            return []

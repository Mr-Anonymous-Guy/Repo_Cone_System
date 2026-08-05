from pathlib import Path
from typing import Optional, Tuple

from repo_clone_system.services.sync_providers.base_provider import (
    BaseSyncProvider,
)


class OneDriveSyncProvider(BaseSyncProvider):
    """Placeholder interface for future Microsoft OneDrive API Sync Provider."""

    @property
    def name(self) -> str:
        return "Microsoft OneDrive Sync Provider"

    def is_configured(self) -> bool:
        return False

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        return (
            False,
            "OneDrive API integration placeholder. "
            "Use local folder sync for OneDrive sync folder.",
            None,
        )

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        return False, "OneDrive API integration placeholder.", None


class DropboxSyncProvider(BaseSyncProvider):
    """Placeholder interface for future Dropbox API Sync Provider."""

    @property
    def name(self) -> str:
        return "Dropbox Sync Provider"

    def is_configured(self) -> bool:
        return False

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        return (
            False,
            "Dropbox API integration placeholder. "
            "Use local folder sync for Dropbox sync folder.",
            None,
        )

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        return False, "Dropbox API integration placeholder.", None


class GoogleDriveSyncProvider(BaseSyncProvider):
    """Placeholder interface for future Google Drive API Sync Provider."""

    @property
    def name(self) -> str:
        return "Google Drive Sync Provider"

    def is_configured(self) -> bool:
        return False

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        return (
            False,
            "Google Drive API integration placeholder. "
            "Use local folder sync for Google Drive sync folder.",
            None,
        )

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        return False, "Google Drive API integration placeholder.", None


class GitHubGistSyncProvider(BaseSyncProvider):
    """Placeholder interface for future GitHub Gist Sync Provider."""

    @property
    def name(self) -> str:
        return "GitHub Gist Sync Provider"

    def is_configured(self) -> bool:
        return False

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        return False, "GitHub Gist API integration placeholder.", None

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        return False, "GitHub Gist API integration placeholder.", None


class CustomSyncProvider(BaseSyncProvider):
    """Placeholder interface for custom user sync providers."""

    @property
    def name(self) -> str:
        return "Custom Provider"

    def is_configured(self) -> bool:
        return False

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        return False, "Custom provider interface placeholder.", None

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        return False, "Custom provider interface placeholder.", None

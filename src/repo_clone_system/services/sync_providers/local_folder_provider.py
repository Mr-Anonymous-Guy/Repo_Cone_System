import datetime
import json
from pathlib import Path
from typing import Optional, Tuple

from repo_clone_system.services.sync_providers.base_provider import (
    BaseSyncProvider,
)


class LocalFolderSyncProvider(BaseSyncProvider):
    """Sync provider for local, network, OneDrive, Dropbox, or custom folders."""

    def __init__(self, target_folder_str: Optional[str] = None):
        self.target_folder = (
            Path(target_folder_str.strip().strip('"')) if target_folder_str else None
        )

    @property
    def name(self) -> str:
        return "Local / Drive Directory Sync Provider"

    def is_configured(self) -> bool:
        return self.target_folder is not None and self.target_folder.exists()

    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        if not self.target_folder:
            return False, "No sync folder configured.", None

        try:
            self.target_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return (
                False,
                f"Failed to create sync folder '{self.target_folder}': {e}",
                None,
            )

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"workspace-sync-{timestamp_str}.json"
        target_path = self.target_folder / filename

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=4)
            return (
                True,
                f"✓ Exported workspace sync file to '{target_path}'.",
                target_path,
            )
        except Exception as e:
            return False, f"Failed to write sync file: {e}", None

    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        if not self.is_configured():
            return False, "Sync directory is not configured or missing.", None

        files = list(self.target_folder.glob("*.json"))
        if not files:
            return (
                False,
                f"No backup JSON files found in '{self.target_folder}'.",
                None,
            )

        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest = files[0]
        return True, f"Found latest backup '{latest.name}'.", latest

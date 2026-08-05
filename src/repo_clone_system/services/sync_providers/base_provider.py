from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple


class BaseSyncProvider(ABC):
    """Abstract base class for Workspace Sync Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the sync provider."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Checks if provider is configured and available."""
        pass

    @abstractmethod
    def export_sync(self, export_payload: dict) -> Tuple[bool, str, Optional[Path]]:
        """Exports active workspace payload to provider storage."""
        pass

    @abstractmethod
    def locate_latest_backup(self) -> Tuple[bool, str, Optional[Path]]:
        """Locates the newest backup file in provider storage."""
        pass

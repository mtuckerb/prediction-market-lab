"""Configuration helpers for local lab runs."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "prediction-market-lab"


@dataclass(frozen=True)
class LabConfig:
    """Runtime configuration loaded from environment variables.

    The scaffold defaults to analysis-only mode. Trading remains disabled by
    default and should not be used to automate market actions.
    """

    log_level: str = "INFO"
    data_dir: Path = DEFAULT_DATA_DIR
    enable_trading: bool = False

    @classmethod
    def from_env(cls) -> "LabConfig":
        """Create config from PML_* environment variables."""
        return cls(
            log_level=os.getenv("PML_LOG_LEVEL", "INFO").upper(),
            data_dir=Path(os.getenv("PML_DATA_DIR", str(DEFAULT_DATA_DIR))).expanduser(),
            enable_trading=_parse_bool(os.getenv("PML_ENABLE_TRADING", "false")),
        )


def _parse_bool(raw: str) -> bool:
    """Parse a conservative boolean value from an environment string."""
    return raw.strip().lower() in {"1", "true", "yes", "on"}

"""Dotenv-style loader that populates os.environ from profile-specific .env files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


DEFAULT_ENV_DIR = Path(".")


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs."""
    result: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
    return result


def load_profile_env(
    profile: str,
    env_dir: Optional[Path] = None,
    override: bool = False,
) -> Dict[str, str]:
    """
    Load environment variables from a profile-specific .env file.

    Looks for files in the following order:
      1. .env.<profile>   (e.g. .env.dev, .env.staging)
      2. .env             (fallback base file)

    Args:
        profile:  Profile name such as 'dev', 'staging', or 'prod'.
        env_dir:  Directory to search for .env files. Defaults to CWD.
        override: If True, existing environment variables will be overwritten.

    Returns:
        A dict of variables that were loaded.
    """
    base_dir = env_dir or DEFAULT_ENV_DIR
    candidates = [
        base_dir / f".env.{profile}",
        base_dir / ".env",
    ]

    loaded: Dict[str, str] = {}
    for candidate in candidates:
        if candidate.exists():
            loaded = _parse_env_file(candidate)
            break

    for key, value in loaded.items():
        if override or key not in os.environ:
            os.environ[key] = value

    return loaded

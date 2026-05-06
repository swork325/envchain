"""Profile management for environment variable chains across dev/staging/prod."""

from __future__ import annotations

import os
from typing import Dict, Optional

from envchain.chain import EnvChain

KNOWN_PROFILES = ("dev", "staging", "prod")


class EnvProfile:
    """Represents a named environment profile (e.g. dev, staging, prod)."""

    def __init__(self, name: str, chain: Optional[EnvChain] = None) -> None:
        if name not in KNOWN_PROFILES:
            raise ValueError(
                f"Unknown profile '{name}'. Must be one of: {', '.join(KNOWN_PROFILES)}"
            )
        self.name = name
        self.chain: EnvChain = chain if chain is not None else EnvChain()

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvProfile(name={self.name!r}, vars={list(self.chain._vars.keys())})"


class ProfileRegistry:
    """Registry that holds multiple named profiles and resolves the active one."""

    PROFILE_ENV_VAR = "APP_ENV"

    def __init__(self) -> None:
        self._profiles: Dict[str, EnvProfile] = {}

    def register(self, profile: EnvProfile) -> None:
        """Register a profile in the registry."""
        self._profiles[profile.name] = profile

    def get(self, name: str) -> EnvProfile:
        """Retrieve a registered profile by name."""
        try:
            return self._profiles[name]
        except KeyError:
            raise KeyError(f"Profile '{name}' is not registered.")

    def active(self) -> EnvProfile:
        """Return the active profile based on the APP_ENV environment variable."""
        env_name = os.environ.get(self.PROFILE_ENV_VAR, "dev")
        return self.get(env_name)

    def validate_active(self) -> bool:
        """Validate the active profile's chain. Returns True if valid."""
        return self.active().chain.validate()

    @property
    def registered_names(self):
        return list(self._profiles.keys())

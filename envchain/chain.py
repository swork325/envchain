"""Core module for defining and validating environment variable chains."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvVar:
    """Represents a single environment variable definition."""

    name: str
    required: bool = True
    default: Optional[str] = None
    description: str = ""

    def resolve(self) -> Optional[str]:
        """Resolve the variable's value from the environment."""
        value = os.environ.get(self.name)
        if value is None and self.default is not None:
            return self.default
        return value


@dataclass
class EnvChain:
    """A named chain of environment variables for a specific environment."""

    name: str
    variables: List[EnvVar] = field(default_factory=list)

    def add(self, name: str, required: bool = True, default: Optional[str] = None, description: str = "") -> "EnvChain":
        """Add a variable definition to the chain."""
        self.variables.append(EnvVar(name=name, required=required, default=default, description=description))
        return self

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate all variables in the chain.

        Returns a dict with keys 'missing' and 'resolved'.
        """
        missing: List[str] = []
        resolved: List[str] = []

        for var in self.variables:
            value = var.resolve()
            if value is None and var.required:
                missing.append(var.name)
            else:
                resolved.append(var.name)

        return {"missing": missing, "resolved": resolved}

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Return all resolved variable values as a dictionary."""
        return {var.name: var.resolve() for var in self.variables}

    def is_valid(self) -> bool:
        """Return True if all required variables are present."""
        result = self.validate()
        return len(result["missing"]) == 0

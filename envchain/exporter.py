"""Export EnvChain configurations to various formats (shell, dotenv, JSON)."""

import json
from typing import Optional
from envchain.chain import EnvChain


SUPPORTED_FORMATS = ("shell", "dotenv", "json")


def export_chain(chain: EnvChain, fmt: str = "dotenv", profile: Optional[str] = None) -> str:
    """Export an EnvChain to a string in the specified format.

    Args:
        chain: The EnvChain instance to export.
        fmt: Output format — one of 'shell', 'dotenv', or 'json'.
        profile: Optional profile label to embed as a comment/key.

    Returns:
        A string representation of the chain in the requested format.

    Raises:
        ValueError: If an unsupported format is requested.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    resolved = {var.name: var.resolve() for var in chain._vars}

    if fmt == "json":
        return _to_json(resolved, profile)
    elif fmt == "shell":
        return _to_shell(resolved, profile)
    else:
        return _to_dotenv(resolved, profile)


def _to_dotenv(resolved: dict, profile: Optional[str]) -> str:
    lines = []
    if profile:
        lines.append(f"# profile: {profile}")
    for key, value in resolved.items():
        if value is None:
            lines.append(f"# {key}=")
        else:
            escaped = str(value).replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
    return "\n".join(lines)


def _to_shell(resolved: dict, profile: Optional[str]) -> str:
    lines = []
    if profile:
        lines.append(f"# profile: {profile}")
    for key, value in resolved.items():
        if value is None:
            lines.append(f"# export {key}=")
        else:
            escaped = str(value).replace('"', '\\"')
            lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines)


def _to_json(resolved: dict, profile: Optional[str]) -> str:
    data = {"vars": resolved}
    if profile:
        data["profile"] = profile
    return json.dumps(data, indent=2)

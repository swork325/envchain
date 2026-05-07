"""Render EnvChain variables as formatted tables or summaries for display."""

from __future__ import annotations

from typing import Literal

from envchain.chain import EnvChain

RenderFormat = Literal["table", "summary", "csv"]
SUPPORTED_FORMATS: tuple[str, ...] = ("table", "summary", "csv")


def render_chain(chain: EnvChain, fmt: RenderFormat = "table", redact: bool = False) -> str:
    """Render an EnvChain in the specified format.

    Args:
        chain: The EnvChain to render.
        fmt: Output format — 'table', 'summary', or 'csv'.
        redact: If True, mask non-None values with '***'.

    Returns:
        A formatted string representation.

    Raises:
        ValueError: If the format is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported render format: {fmt!r}. Choose from {SUPPORTED_FORMATS}."
        )

    items = list(chain)
    if fmt == "table":
        return _to_table(items, redact)
    if fmt == "csv":
        return _to_csv(items, redact)
    return _to_summary(items, redact)


def _mask(value: str | None, redact: bool) -> str:
    if value is None:
        return "<missing>"
    return "***" if redact else value


def _to_table(items: list, redact: bool) -> str:
    if not items:
        return "(empty chain)"

    col_key = max(len(var.name) for var in items)
    col_key = max(col_key, 3)  # minimum width for 'Key'
    col_val = max(len(_mask(var.resolve(), redact)) for var in items)
    col_val = max(col_val, 5)  # minimum width for 'Value'

    header = f"{'Key':<{col_key}}  {'Value':<{col_val}}  Required"
    sep = "-" * len(header)
    rows = [header, sep]
    for var in items:
        val = _mask(var.resolve(), redact)
        req = "yes" if var.required else "no"
        rows.append(f"{var.name:<{col_key}}  {val:<{col_val}}  {req}")
    return "\n".join(rows)


def _to_csv(items: list, redact: bool) -> str:
    lines = ["key,value,required"]
    for var in items:
        val = _mask(var.resolve(), redact)
        req = str(var.required).lower()
        lines.append(f"{var.name},{val},{req}")
    return "\n".join(lines)


def _to_summary(items: list, redact: bool) -> str:
    total = len(items)
    missing = sum(1 for var in items if var.resolve() is None)
    present = total - missing
    lines = [
        f"Total variables : {total}",
        f"Present         : {present}",
        f"Missing         : {missing}",
    ]
    if missing:
        missing_keys = [var.name for var in items if var.resolve() is None]
        lines.append("Missing keys    : " + ", ".join(missing_keys))
    return "\n".join(lines)

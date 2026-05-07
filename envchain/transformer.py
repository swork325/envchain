"""Value transformation pipeline for EnvChain variables."""

from typing import Callable, List, Optional
from envchain.chain import EnvChain


TransformFn = Callable[[Optional[str]], Optional[str]]


def strip_whitespace(value: Optional[str]) -> Optional[str]:
    """Strip leading and trailing whitespace from a value."""
    return value.strip() if value is not None else None


def to_uppercase(value: Optional[str]) -> Optional[str]:
    """Convert value to uppercase."""
    return value.upper() if value is not None else None


def to_lowercase(value: Optional[str]) -> Optional[str]:
    """Convert value to lowercase."""
    return value.lower() if value is not None else None


def mask_value(mask_char: str = "*", visible: int = 4) -> TransformFn:
    """Return a transform that masks all but the last `visible` characters."""
    def _transform(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if len(value) <= visible:
            return mask_char * len(value)
        return mask_char * (len(value) - visible) + value[-visible:]
    return _transform


def prefix(text: str) -> TransformFn:
    """Return a transform that prepends `text` to the value."""
    def _transform(value: Optional[str]) -> Optional[str]:
        return f"{text}{value}" if value is not None else None
    return _transform


def apply_transforms(chain: EnvChain, transforms: List[TransformFn]) -> EnvChain:
    """Apply a list of transform functions to every resolved value in a chain.

    Returns a new EnvChain with transformed values as defaults, preserving keys.
    """
    new_chain = EnvChain(chain.profile)
    for var in chain._vars:
        value = var.resolve()
        for fn in transforms:
            value = fn(value)
        from envchain.chain import EnvVar
        new_var = EnvVar(var.key, default=value)
        new_chain._vars.append(new_var)
    return new_chain


def transform_key(chain: EnvChain, key: str, transforms: List[TransformFn]) -> Optional[str]:
    """Apply transforms to the resolved value of a single key."""
    for var in chain._vars:
        if var.key == key:
            value = var.resolve()
            for fn in transforms:
                value = fn(value)
            return value
    raise KeyError(f"Key '{key}' not found in chain")

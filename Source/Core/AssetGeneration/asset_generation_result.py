"""Immutable outcome returned by an external asset-generation provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AssetGenerationResult:
    """A generated project-relative asset and the provider evidence for it."""

    output_path: str
    media_type: str
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)

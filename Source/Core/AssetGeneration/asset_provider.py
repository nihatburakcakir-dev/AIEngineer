"""Provider boundary for external media-generation backends.

Providers may create bytes outside Unity, but never choose the destination path:
the validated change-set owns that decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .asset_generation_result import AssetGenerationResult


class AssetProviderError(RuntimeError):
    """An external generator could not produce a usable asset."""


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    output_path: str
    project_root: str = ""
    model: str = "FLUX.2-klein-4B"
    width: int = 1024
    height: int = 1024
    transparent: bool = False
    overwrite: bool = False
    reference_image_path: str = ""
    edit_strength: float = 0.78


class AssetProvider(Protocol):
    """Minimal boundary shared by ComfyUI and future media providers."""

    @property
    def name(self) -> str:
        """Stable, user-visible provider identifier."""

    def generate_image(self, request: ImageGenerationRequest) -> AssetGenerationResult:
        """Generate a PNG at the already validated project-relative output path."""

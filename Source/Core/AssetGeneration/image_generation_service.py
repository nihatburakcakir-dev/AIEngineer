"""Validation-free orchestration around a configured image asset provider."""

from __future__ import annotations

from .asset_generation_result import AssetGenerationResult
from .asset_provider import AssetProvider, AssetProviderError, ImageGenerationRequest


class ImageGenerationService:
    """Runs an image request after the change-set has already validated its path."""

    def __init__(self, provider: AssetProvider):
        self.provider = provider

    def generate(self, request: ImageGenerationRequest) -> AssetGenerationResult:
        result = self.provider.generate_image(request)
        if result.media_type != "image/png":
            raise AssetProviderError(
                f"Image provider '{self.provider.name}' returned unsupported media type: {result.media_type}."
            )
        if result.output_path != request.output_path:
            raise AssetProviderError(
                f"Image provider '{self.provider.name}' returned a path outside the approved change-set output."
            )
        return result

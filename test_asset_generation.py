import unittest
import json
import tempfile
from pathlib import Path

from Source.Core.AssetGeneration import (
    AssetGenerationResult,
    AssetProviderError,
    ImageGenerationRequest,
    ImageGenerationService,
    ComfyUiProvider,
)


class FakeImageProvider:
    name = "fake"

    def __init__(self, result):
        self.result = result
        self.requests = []

    def generate_image(self, request):
        self.requests.append(request)
        return self.result


class AssetGenerationTests(unittest.TestCase):
    def setUp(self):
        self.request = ImageGenerationRequest(
            prompt="Blue wolf projectile", output_path="Assets/AIEngineerGenerated/Textures/Wolf.png",
            transparent=True,
        )

    def test_image_service_accepts_png_at_the_approved_destination(self):
        provider = FakeImageProvider(AssetGenerationResult(
            output_path=self.request.output_path, media_type="image/png", provider="fake",
        ))

        result = ImageGenerationService(provider).generate(self.request)

        self.assertEqual(result.provider, "fake")
        self.assertEqual(provider.requests, [self.request])

    def test_image_service_rejects_an_unapproved_destination(self):
        provider = FakeImageProvider(AssetGenerationResult(
            output_path="Assets/Elsewhere/Wolf.png", media_type="image/png", provider="fake",
        ))

        with self.assertRaisesRegex(AssetProviderError, "approved change-set output"):
            ImageGenerationService(provider).generate(self.request)

    def test_image_service_rejects_a_non_png_result(self):
        provider = FakeImageProvider(AssetGenerationResult(
            output_path=self.request.output_path, media_type="image/jpeg", provider="fake",
        ))

        with self.assertRaisesRegex(AssetProviderError, "unsupported media type"):
            ImageGenerationService(provider).generate(self.request)

    def test_comfyui_provider_substitutes_workflow_tokens_and_writes_png(self):
        calls = []

        def transport(method, path, data):
            calls.append((method, path, data))
            if path == "/prompt":
                return b'{"prompt_id":"job-1"}'
            if path == "/history/job-1":
                return b'{"job-1":{"outputs":{"9":{"images":[{"filename":"wolf.png","type":"output"}]}}}}'
            if path == "/view?filename=wolf.png&type=output":
                return b"PNG-BYTES"
            self.fail("Unexpected ComfyUI request: " + path)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Assets").mkdir()
            workflow = root / "workflow.json"
            workflow.write_text(json.dumps({"1": {"inputs": {"text": "$prompt", "model": "$model", "width": "$width", "alpha": "$transparent", "seed": "$seed"}}}), encoding="utf-8")
            request = ImageGenerationRequest(
                prompt="blue wolf", output_path="Assets/AIEngineerGenerated/Wolf.png", project_root=str(root),
                width=768, height=512, transparent=True,
            )

            result = ComfyUiProvider("http://127.0.0.1:8188", str(workflow), transport=transport).generate_image(request)

            submitted = json.loads(calls[0][2].decode("utf-8"))
            self.assertEqual(submitted["prompt"]["1"]["inputs"]["text"], "blue wolf")
            self.assertEqual(submitted["prompt"]["1"]["inputs"]["model"], "FLUX.2-klein-4B")
            self.assertEqual(submitted["prompt"]["1"]["inputs"]["width"], 768)
            self.assertTrue(submitted["prompt"]["1"]["inputs"]["alpha"])
            self.assertIsInstance(submitted["prompt"]["1"]["inputs"]["seed"], int)
            self.assertEqual((root / request.output_path).read_bytes(), b"PNG-BYTES")
            self.assertEqual(result.metadata["prompt_id"], "job-1")

    def test_comfyui_provider_substitutes_reference_workflow_tokens(self):
        request = ImageGenerationRequest(
            prompt="make the wolf yellow", output_path="Assets/AIEngineerGenerated/Wolf.png",
            reference_image_path="C:/reference.png", edit_strength=0.73,
        )
        workflow = ComfyUiProvider._substitute(
            {"image": "$reference_image", "denoise": "$edit_strength"}, request, "uploaded.png"
        )
        self.assertEqual(workflow["image"], "uploaded.png")
        self.assertEqual(workflow["denoise"], 0.73)


if __name__ == "__main__":
    unittest.main()

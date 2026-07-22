import unittest

from Source.Brain.prompt_builder import PromptBuilder


class PromptBuilderTests(unittest.TestCase):
    def test_includes_pipeline_rules_and_rejects_incompatible_request(self):
        prompt = PromptBuilder().build("HDRP materyal olustur", {
            "unity_expertise": {
                "render_pipeline": "URP",
                "expertise": [{"topic": "rendering", "rules": ["Use URP APIs only."], "pitfalls": ["HDRP makes materials pink."]}],
                "recommendation": {"allowed": False, "reason": "HDRP is incompatible with URP."},
                "documentation": [{"title": "Material", "section": "URP"}],
            },
        })

        self.assertIn("UNITY EXPERTISE", prompt)
        self.assertIn("Render Pipeline : URP", prompt)
        self.assertIn("Allowed : False", prompt)
        self.assertIn("HDRP is incompatible", prompt)
        self.assertIn("Pitfall: HDRP makes materials pink.", prompt)
        self.assertIn("Documentation : Material / URP", prompt)


if __name__ == "__main__":
    unittest.main()

"""Turn a character image analysis into an explicit Unity prefab build plan."""

import re
import unicodedata
from pathlib import Path

from Source.Core.Character.models import AnimatorSetup, CharacterPrefabPlan, CharacterProfile, PhysicsSetup


class CharacterClassifier:
    CREATURE_WORDS = {"wolf", "kurt", "animal", "creature", "monster", "beast", "dragon"}
    HUMANOID_WORDS = {"human", "person", "soldier", "hero", "warrior", "humanoid", "character"}

    def classify(self, analysis, image_path, name=None) -> CharacterProfile:
        source = Path(image_path)
        words = self._words(source.stem, analysis)
        dimension = self._dimension(analysis, words)
        archetype = "creature" if words & self.CREATURE_WORDS else "humanoid" if words & self.HUMANOID_WORDS else "simple"
        locomotion = "ground"
        character_name = name or self._class_name(source.stem) or "GeneratedCharacter"
        confidence = max(float(analysis.assets.confidence or 0), float(analysis.scene.confidence or 0), 0.5)
        return CharacterProfile(character_name, dimension, archetype, locomotion, str(source), confidence)

    @staticmethod
    def _words(stem, analysis):
        text = " ".join([stem, analysis.assets.style, *analysis.assets.asset_types, *analysis.scene.objects]).casefold()
        return set(re.findall(r"[\wçğıöşü]+", text))

    @staticmethod
    def _dimension(analysis, words):
        detected = analysis.assets.dimension.casefold()
        if detected in {"2d", "3d"}:
            return detected.upper()
        if detected == "mixed":
            return "3D" if words & (CharacterClassifier.CREATURE_WORDS | CharacterClassifier.HUMANOID_WORDS) else "2D"
        return "3D" if words & (CharacterClassifier.CREATURE_WORDS | CharacterClassifier.HUMANOID_WORDS) else "2D"

    @staticmethod
    def _class_name(value):
        value = value.translate(str.maketrans({"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G", "ü": "u", "Ü": "U", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C"}))
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        pieces = re.findall(r"[A-Za-z0-9]+", value)
        return "".join(piece.capitalize() for piece in pieces)


class CharacterPrefabGenerator:
    """Produces reviewable operations; Unity Editor performs the actual asset write."""

    def build_plan(self, profile: CharacterProfile, output_root="Assets/AIEngineerGenerated/Characters") -> CharacterPrefabPlan:
        safe_name = re.sub(r"[^A-Za-z0-9_]", "", profile.name) or "GeneratedCharacter"
        if profile.dimension == "2D":
            physics = PhysicsSetup("CapsuleCollider2D", "Rigidbody2D", 1.0, ["FreezeRotation"])
            controller = "GeneratedCharacterController2D"
        else:
            physics = PhysicsSetup("CapsuleCollider", "Rigidbody", 1.0, ["FreezeRotationX", "FreezeRotationZ"])
            controller = "GeneratedCharacterController3D"
        animator = AnimatorSetup(f"{output_root}/{safe_name}/{safe_name}.controller")
        prefab_path = f"{output_root}/{safe_name}/{safe_name}.prefab"
        operations = [
            {"action": "create_placeholder_root", "primitive": "Sprite" if profile.dimension == "2D" else "Capsule", "name": safe_name},
            {"action": "attach_source_image_reference", "image": profile.source_image},
            {"action": "add_component", "component": physics.collider},
            {"action": "add_component", "component": physics.rigidbody, "mass": physics.mass, "constraints": physics.constraints},
            {"action": "create_animator_controller", "path": animator.controller_path, "states": animator.states},
            {"action": "attach_controller_script", "class": controller},
            {"action": "save_prefab", "path": prefab_path},
        ]
        warnings = ["The source image is referenced for art direction; a single image is not treated as a generated rigged mesh."]
        if profile.needs_placeholder_mesh:
            warnings.append("A placeholder capsule/sprite is used until an authored model or sprite is assigned.")
        return CharacterPrefabPlan(profile, physics, animator, controller, prefab_path, operations, warnings)

    @staticmethod
    def controller_code(plan: CharacterPrefabPlan):
        if plan.profile.dimension == "2D":
            return CharacterPrefabGenerator._controller_2d(plan.controller_class)
        return CharacterPrefabGenerator._controller_3d(plan.controller_class)

    @staticmethod
    def _controller_3d(class_name):
        return f'''using UnityEngine;

[RequireComponent(typeof(Rigidbody))]
public sealed class {class_name} : MonoBehaviour
{{
    [SerializeField] private float speed = 5f;
    private Rigidbody body;
    private Vector3 input;

    private void Awake() => body = GetComponent<Rigidbody>();
    private void Update() => input = new Vector3(Input.GetAxisRaw("Horizontal"), 0f, Input.GetAxisRaw("Vertical")).normalized;
    private void FixedUpdate() => body.MovePosition(body.position + input * speed * Time.fixedDeltaTime);
}}
'''

    @staticmethod
    def _controller_2d(class_name):
        return f'''using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public sealed class {class_name} : MonoBehaviour
{{
    [SerializeField] private float speed = 5f;
    private Rigidbody2D body;
    private Vector2 input;

    private void Awake() => body = GetComponent<Rigidbody2D>();
    private void Update() => input = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical")).normalized;
    private void FixedUpdate() => body.linearVelocity = input * speed;
}}
'''

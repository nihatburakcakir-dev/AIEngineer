"""Unity domain rules and project-aware expertise retrieval."""

import json
from pathlib import Path


EXPERTISE = {
    "scene": {
        "keywords": {"scene", "gameobject", "component", "hierarchy"},
        "rules": ["Keep scene ownership explicit in the hierarchy.", "Prefer component references over global object searches."],
    },
    "prefab": {
        "keywords": {"prefab", "instantiate", "variant"},
        "rules": ["Keep reusable objects as prefabs.", "Use serialized references instead of scene-wide searches."],
    },
    "physics": {
        "keywords": {"rigidbody", "collider", "physics", "force"},
        "rules": ["Apply physics changes in FixedUpdate.", "Use the Rigidbody API instead of directly changing Transform for dynamic bodies."],
    },
    "timeline": {
        "keywords": {"timeline", "playable", "cinemachine"},
        "rules": ["Keep Timeline clips and bindings explicit.", "Validate PlayableDirector bindings before playback."],
    },
    "addressables": {
        "keywords": {"addressable", "addressables", "asset loading"},
        "rules": ["Release Addressables handles after use.", "Do not mix Resources and Addressables for the same runtime asset path."],
    },
    "rendering": {
        "keywords": {"shader", "material", "urp", "hdrp", "render pipeline"},
        "rules": ["Generate shaders and materials only for the detected render pipeline."],
    },
    "material": {
        "keywords": {"material", "materyal", "texture", "renderer"},
        "rules": ["Create materials that match the active render pipeline.", "Share material assets unless per-instance properties are required."],
    },
    "animation": {
        "keywords": {"animator", "animation", "blend tree"},
        "rules": ["Drive Animator parameters by stable hashes when used frequently.", "Keep gameplay state separate from animation state."],
    },
    "ui": {
        "keywords": {"ui", "canvas", "button", "layout"},
        "rules": ["Use layout components for responsive UI.", "Avoid rebuilding Canvas hierarchies every frame."],
    },
    "scriptableobject": {
        "keywords": {"scriptableobject", "configuration", "game data"},
        "rules": ["Store shared authoring data in ScriptableObjects.", "Do not keep mutable per-session state in shared assets."],
    },
    "build": {
        "keywords": {"build", "player settings", "build pipeline"},
        "rules": ["Validate the active build target before creating a player build."],
    },
    "asset_pipeline": {
        "keywords": {"import", "importer", "asset pipeline", "asset database"},
        "rules": ["Configure import settings per asset type.", "Avoid AssetDatabase APIs in runtime code."],
    },
    "audio": {
        "keywords": {"audio", "audioclip", "mixer", "sound"},
        "rules": ["Route runtime audio through an AudioMixer group.", "Pool short-lived audio sources where appropriate."],
    },
    "navigation": {
        "keywords": {"navmesh", "navigation", "agent"},
        "rules": ["Bake NavMesh data for the active scene.", "Set NavMeshAgent destinations only when a valid path is expected."],
    },
}

TEMPLATE_TOPICS = ("addressables", "physics", "ui", "timeline", "prefab")

PITFALLS = {
    "scene": ["Loading a scene additively without unloading it leaks scene objects."],
    "prefab": ["Editing an instantiated prefab does not update the prefab asset."],
    "physics": ["Calling AddForce from Update creates frame-rate-dependent movement."],
    "timeline": ["Unbound PlayableDirector tracks silently fail at runtime."],
    "addressables": ["Forgetting to release an Addressables handle leaks memory."],
    "rendering": ["Using HDRP shaders in a URP project creates pink materials."],
    "material": ["Using Renderer.material repeatedly creates unintended material instances."],
    "animation": ["Setting Animator strings every frame allocates unnecessarily."],
    "ui": ["Rebuilding a Canvas every frame causes UI performance spikes."],
    "scriptableobject": ["Mutating a shared ScriptableObject creates cross-session state leaks."],
    "build": ["Building for the wrong active target produces an unusable player."],
    "asset_pipeline": ["AssetDatabase calls are editor-only and must not ship in player code."],
    "audio": ["Creating AudioSource instances per sound causes avoidable allocations."],
    "navigation": ["Setting a NavMeshAgent destination without a baked NavMesh fails."],
}

CODE_TEMPLATES = {
    "scene": """using UnityEngine;\n\npublic sealed class SceneComponentLocator : MonoBehaviour\n{\n    [SerializeField] private Camera sceneCamera;\n    private void Awake() { if (sceneCamera == null) sceneCamera = Camera.main; }\n}""",
    "prefab": """using UnityEngine;\n\npublic sealed class PrefabSpawner : MonoBehaviour\n{\n    [SerializeField] private GameObject prefab;\n    public GameObject Spawn(Vector3 position) => Instantiate(prefab, position, Quaternion.identity);\n}""",
    "physics": """using UnityEngine;\n\n[RequireComponent(typeof(Rigidbody))]\npublic sealed class ForceMover : MonoBehaviour\n{\n    [SerializeField] private float force = 10f;\n    private Rigidbody body;\n    private void Awake() => body = GetComponent<Rigidbody>();\n    private void FixedUpdate() => body.AddForce(transform.forward * force, ForceMode.Acceleration);\n}""",
    "timeline": """using UnityEngine;\nusing UnityEngine.Playables;\n\npublic sealed class TimelineTrigger : MonoBehaviour\n{\n    [SerializeField] private PlayableDirector director;\n    public void Play() { if (director != null) director.Play(); }\n}""",
    "addressables": """using UnityEngine;\nusing UnityEngine.AddressableAssets;\nusing UnityEngine.ResourceManagement.AsyncOperations;\n\npublic sealed class AddressablePrefabLoader : MonoBehaviour\n{\n    [SerializeField] private AssetReferenceGameObject prefab;\n    private AsyncOperationHandle<GameObject> handle;\n    public async void Load() { handle = prefab.InstantiateAsync(); await handle.Task; }\n    private void OnDestroy() { if (handle.IsValid()) Addressables.ReleaseInstance(handle); }\n}""",
    "rendering": """using UnityEngine;\n\npublic sealed class PipelineMaterialFactory : MonoBehaviour\n{\n    public Material CreateLitMaterial() => new Material(Shader.Find(\"Universal Render Pipeline/Lit\"));\n}""",
    "material": """using UnityEngine;\n\npublic sealed class MaterialTint : MonoBehaviour\n{\n    [SerializeField] private Renderer targetRenderer;\n    private MaterialPropertyBlock properties;\n    private void Awake() => properties = new MaterialPropertyBlock();\n    public void SetColor(Color color) { targetRenderer.GetPropertyBlock(properties); properties.SetColor(\"_BaseColor\", color); targetRenderer.SetPropertyBlock(properties); }\n}""",
    "animation": """using UnityEngine;\n\npublic sealed class AnimatorDriver : MonoBehaviour\n{\n    [SerializeField] private Animator animator;\n    private static readonly int Speed = Animator.StringToHash(\"Speed\");\n    public void SetSpeed(float value) => animator.SetFloat(Speed, value);\n}""",
    "ui": """using TMPro;\nusing UnityEngine;\n\npublic sealed class ScoreView : MonoBehaviour\n{\n    [SerializeField] private TMP_Text scoreText;\n    public void SetScore(int score) => scoreText.text = score.ToString();\n}""",
    "scriptableobject": """using UnityEngine;\n\n[CreateAssetMenu(menuName = \"Game/Weapon Config\")]\npublic sealed class WeaponConfig : ScriptableObject\n{\n    [Min(0f)] public float damage = 10f;\n}""",
    "build": """#if UNITY_EDITOR\nusing UnityEditor;\n\npublic static class PlayerBuild\n{\n    [MenuItem(\"Build/Validate Active Target\")]\n    public static void Validate() { UnityEngine.Debug.Log(EditorUserBuildSettings.activeBuildTarget); }\n}\n#endif""",
    "asset_pipeline": """#if UNITY_EDITOR\nusing UnityEditor;\n\npublic sealed class TextureImportPolicy : AssetPostprocessor\n{\n    private void OnPreprocessTexture() => ((TextureImporter)assetImporter).sRGBTexture = true;\n}\n#endif""",
    "audio": """using UnityEngine;\n\n[RequireComponent(typeof(AudioSource))]\npublic sealed class SoundPlayer : MonoBehaviour\n{\n    [SerializeField] private AudioClip clip;\n    private AudioSource source;\n    private void Awake() => source = GetComponent<AudioSource>();\n    public void Play() => source.PlayOneShot(clip);\n}""",
    "navigation": """using UnityEngine;\nusing UnityEngine.AI;\n\n[RequireComponent(typeof(NavMeshAgent))]\npublic sealed class NavAgentMover : MonoBehaviour\n{\n    private NavMeshAgent agent;\n    private void Awake() => agent = GetComponent<NavMeshAgent>();\n    public void MoveTo(Vector3 destination) { if (NavMesh.SamplePosition(destination, out var hit, 1f, NavMesh.AllAreas)) agent.SetDestination(hit.position); }\n}""",
}


class UnityExpertise:
    def __init__(self, project_path, learned_rules_path="Data/learned_unity_rules.json"):
        self.project_path = Path(project_path)
        self.learned_rules_path = Path(learned_rules_path)

    def render_pipeline(self):
        graphics = self.project_path / "ProjectSettings" / "GraphicsSettings.asset"
        manifest = self.project_path / "Packages" / "manifest.json"
        graphics_text = graphics.read_text(encoding="utf-8", errors="ignore") if graphics.is_file() else ""
        manifest_data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {"dependencies": {}}
        dependencies = manifest_data.get("dependencies", {})
        if "UniversalRenderPipeline" in graphics_text or "com.unity.render-pipelines.universal" in dependencies:
            return "URP"
        if "HDRenderPipeline" in graphics_text or "com.unity.render-pipelines.high-definition" in dependencies:
            return "HDRP"
        return "Built-in"

    def has_package(self, package_id):
        manifest = self.project_path / "Packages" / "manifest.json"
        if not manifest.is_file():
            return False
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return package_id in data.get("dependencies", {})

    def retrieve(self, request):
        request_words = set(request.casefold().replace("-", " ").split())
        matches = []
        for topic, package in EXPERTISE.items():
            if request_words & package["keywords"]:
                matches.append({
                    "topic": topic,
                    "rules": package["rules"],
                    "pitfalls": PITFALLS[topic],
                })
        if any(word in request_words for word in {"shader", "material", "urp", "hdrp", "render"}):
            matches.append({"topic": "pipeline", "rules": [f"This project uses {self.render_pipeline()}; use only {self.render_pipeline()} compatible rendering APIs."]})
        for learned in self._learned_rules():
            if request_words & set(learned.get("keywords", [])):
                matches.append({"topic": "learned", "rules": [learned.get("rule", "")], "pitfalls": [learned.get("rationale", "")]})
        return matches

    def _learned_rules(self):
        if not self.learned_rules_path.is_file():
            return []
        try:
            return json.loads(self.learned_rules_path.read_text(encoding="utf-8")).get("rules", [])
        except json.JSONDecodeError:
            return []

    def context_for(self, request, documents=None):
        return {
            "render_pipeline": self.render_pipeline(),
            "expertise": self.retrieve(request),
            "recommendation": self.recommend(request),
            "documentation": self._relevant_documents(documents or []),
        }

    @staticmethod
    def _relevant_documents(documents):
        return [
            {"title": document.get("title", ""), "section": document.get("section", "")}
            for document in documents[:3]
        ]

    def recommend(self, request):
        normalized = request.casefold()
        pipeline = self.render_pipeline()
        wants_hdrp = "hdrp" in normalized
        wants_urp = "urp" in normalized
        if (wants_hdrp and pipeline != "HDRP") or (wants_urp and pipeline != "URP"):
            requested = "HDRP" if wants_hdrp else "URP"
            return {
                "allowed": False,
                "reason": f"Requested {requested} content is incompatible with this {pipeline} project.",
                "alternative": f"Generate {pipeline}-compatible material or shader content instead.",
            }
        if "addressable" in normalized:
            installed = self.has_package("com.unity.addressables")
            return {
                "allowed": installed,
                "action": "mark_addressable",
                "package": "com.unity.addressables",
                "reason": "Addressables package is available." if installed else "Install com.unity.addressables before converting a prefab.",
            }
        return {"allowed": True, "reason": f"Use {pipeline}-compatible Unity APIs."}

    def code_template(self, request):
        request_words = set(request.casefold().replace("-", " ").split())
        if request_words & EXPERTISE["addressables"]["keywords"]:
            return {
                "topic": "addressables",
                "pipeline": self.render_pipeline(),
                "code": CODE_TEMPLATES["addressables"],
            }
        for topic, package in EXPERTISE.items():
            if request_words & package["keywords"] and topic in CODE_TEMPLATES:
                code = CODE_TEMPLATES[topic]
                if topic == "rendering":
                    shader = {
                        "URP": "Universal Render Pipeline/Lit",
                        "HDRP": "HDRP/Lit",
                        "Built-in": "Standard",
                    }[self.render_pipeline()]
                    code = code.replace("Universal Render Pipeline/Lit", shader)
                return {"topic": topic, "pipeline": self.render_pipeline(), "code": code}
        if request_words & EXPERTISE["addressables"]["keywords"]:
            return {
                "topic": "addressables",
                "pipeline": self.render_pipeline(),
                "code": """using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

public sealed class AddressablePrefabLoader : MonoBehaviour
{
    [SerializeField] private AssetReferenceGameObject prefab;
    private AsyncOperationHandle<GameObject> handle;

    public async void Load()
    {
        handle = prefab.InstantiateAsync();
        await handle.Task;
    }

    private void OnDestroy()
    {
        if (handle.IsValid()) Addressables.ReleaseInstance(handle);
    }
}""",
            }
        if request_words & EXPERTISE["physics"]["keywords"]:
            return {
                "topic": "physics",
                "pipeline": self.render_pipeline(),
                "code": """using UnityEngine;

[RequireComponent(typeof(Rigidbody))]
public sealed class ForceMover : MonoBehaviour
{
    [SerializeField] private float force = 10f;
    private Rigidbody body;

    private void Awake() => body = GetComponent<Rigidbody>();
    private void FixedUpdate() => body.AddForce(transform.forward * force, ForceMode.Acceleration);
}""",
            }
        if request_words & EXPERTISE["ui"]["keywords"]:
            return {
                "topic": "ui",
                "pipeline": self.render_pipeline(),
                "code": """using TMPro;
using UnityEngine;

public sealed class ScoreView : MonoBehaviour
{
    [SerializeField] private TMP_Text scoreText;
    public void SetScore(int score) => scoreText.text = score.ToString();
}""",
            }
        if request_words & EXPERTISE["timeline"]["keywords"]:
            return {
                "topic": "timeline",
                "pipeline": self.render_pipeline(),
                "code": """using UnityEngine;
using UnityEngine.Playables;

public sealed class TimelineTrigger : MonoBehaviour
{
    [SerializeField] private PlayableDirector director;
    public void Play() { if (director != null) director.Play(); }
}""",
            }
        if request_words & EXPERTISE["prefab"]["keywords"]:
            return {
                "topic": "prefab",
                "pipeline": self.render_pipeline(),
                "code": """using UnityEngine;

public sealed class PrefabSpawner : MonoBehaviour
{
    [SerializeField] private GameObject prefab;
    public GameObject Spawn(Vector3 position) => Instantiate(prefab, position, Quaternion.identity);
}""",
            }
        return None

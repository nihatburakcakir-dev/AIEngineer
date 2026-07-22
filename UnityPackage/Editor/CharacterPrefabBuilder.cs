using System.IO;
using AIEngineer.Characters;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace AIEngineer.Editor
{
    /// <summary>Creates drag-and-drop-ready, capsule-masked character prefabs from a reviewed build request.</summary>
    public static class CharacterPrefabBuilder
    {
        // Generated characters belong to the user project, not the protected package.
        private const string OutputRoot = "Assets/AIEngineerGenerated/Characters";
        private const string PendingRequestPath = OutputRoot + "/CharacterBuildRequest.json";

        [System.Serializable]
        private sealed class CharacterBuildRequest
        {
            public string name;
            public string dimension;
            public string sourceImagePath;
        }

        [InitializeOnLoadMethod]
        private static void BuildPendingRequestAfterReload()
        {
            EditorApplication.delayCall += () =>
            {
                if (File.Exists(PendingRequestPath))
                    BuildPendingRequest();
            };
        }

        [MenuItem("AI Engineer/Characters/Create 3D Placeholder")]
        public static void Create3DPlaceholder()
        {
            Create3D("GeneratedCharacter", null);
        }

        [MenuItem("AI Engineer/Characters/Create Wolf Placeholder")]
        public static void CreateWolfPlaceholder()
        {
            Create3D("KirmiziKurt", "Assets/Scripts/Managers/Kırmızı kurt.png");
        }

        [MenuItem("AI Engineer/Characters/Create 2D Placeholder")]
        public static void Create2DPlaceholder()
        {
            Create2D("GeneratedCharacter2D", null);
        }

        [MenuItem("AI Engineer/Characters/Build Pending Character Request")]
        public static void BuildPendingRequest()
        {
            if (!File.Exists(PendingRequestPath))
            {
                Debug.LogWarning("AI Engineer character build request was not found: " + PendingRequestPath);
                return;
            }
            var request = JsonUtility.FromJson<CharacterBuildRequest>(File.ReadAllText(PendingRequestPath));
            if (request == null || string.IsNullOrWhiteSpace(request.name))
            {
                Debug.LogError("AI Engineer character build request is invalid.");
                return;
            }
            if (string.Equals(request.dimension, "2D", System.StringComparison.OrdinalIgnoreCase))
                Create2D(request.name, request.sourceImagePath);
            else
                Create3D(request.name, request.sourceImagePath);
            AssetDatabase.DeleteAsset(PendingRequestPath);
        }

        public static void BuildFromExternalImage(string name, string dimension, string sourceImagePath, string characterFolder)
        {
            if (string.IsNullOrWhiteSpace(name)) throw new System.ArgumentException("Character name is required.");
            var outputRoot = Path.GetDirectoryName(characterFolder)?.Replace('\\', '/') ?? "Assets/AIEngineerGenerated/Characters";
            var importedImage = ImportSourceImage(name, sourceImagePath, characterFolder, string.Equals(dimension, "2D", System.StringComparison.OrdinalIgnoreCase));
            if (string.Equals(dimension, "2D", System.StringComparison.OrdinalIgnoreCase))
                Create2D(name, importedImage, outputRoot);
            else
                Create3D(name, importedImage, outputRoot);
        }

        private static void Create2D(string name, string sourceImagePath, string outputRoot = OutputRoot)
        {
            EnsureFolder(outputRoot);
            var root = new GameObject(name, typeof(SpriteRenderer), typeof(CapsuleCollider2D), typeof(Rigidbody2D), typeof(Animator), typeof(GeneratedCharacterController2D), typeof(CharacterSourceImage));
            var body = root.GetComponent<Rigidbody2D>();
            body.mass = 1f;
            body.constraints = RigidbodyConstraints2D.FreezeRotation;
            if (!string.IsNullOrWhiteSpace(sourceImagePath))
            {
                root.GetComponent<CharacterSourceImage>().SetSourceImage(AssetDatabase.LoadAssetAtPath<Texture2D>(sourceImagePath));
                root.GetComponent<SpriteRenderer>().sprite = AssetDatabase.LoadAssetAtPath<Sprite>(sourceImagePath);
            }
            SavePrefab(root, name, outputRoot);
        }

        private static void Create3D(string name, string sourceImagePath, string outputRoot = OutputRoot)
        {
            EnsureFolder(outputRoot);
            var root = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            root.name = name;
            var body = root.AddComponent<Rigidbody>();
            body.mass = 1f;
            body.constraints = RigidbodyConstraints.FreezeRotationX | RigidbodyConstraints.FreezeRotationZ;
            root.AddComponent<Animator>();
            root.AddComponent<GeneratedCharacterController3D>();
            var source = root.AddComponent<CharacterSourceImage>();
            if (!string.IsNullOrWhiteSpace(sourceImagePath))
            {
                var image = AssetDatabase.LoadAssetAtPath<Texture2D>(sourceImagePath);
                source.SetSourceImage(image);
                CreateConceptArtBillboard(root, image, outputRoot);
            }
            SavePrefab(root, name, outputRoot);
        }

        private static void CreateConceptArtBillboard(GameObject root, Texture2D image, string outputRoot)
        {
            if (image == null)
                return;

            // Keep the capsule only for physics; render the supplied concept art instead.
            root.GetComponent<MeshRenderer>().enabled = false;
            var visual = GameObject.CreatePrimitive(PrimitiveType.Quad);
            visual.name = "ConceptArtVisual";
            visual.transform.SetParent(root.transform, false);
            var aspect = image.width / (float)image.height;
            visual.transform.localScale = new Vector3(1f, 2f, 1f);
            var shader = Shader.Find("AIEngineer/CapsulePortrait") ?? Shader.Find("Universal Render Pipeline/Unlit") ?? Shader.Find("Unlit/Texture");
            var folder = outputRoot + "/" + root.name;
            EnsureFolder(folder);
            var materialPath = folder + "/" + root.name + "ConceptArt.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null)
            {
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, materialPath);
            }
            material.shader = shader;
            if (material.HasProperty("_BaseMap"))
                material.SetTexture("_BaseMap", image);
            else
                material.mainTexture = image;
            var portraitAspect = 0.5f;
            var cropScale = Mathf.Min(1f, portraitAspect / aspect);
            material.mainTextureScale = new Vector2(cropScale, 1f);
            material.mainTextureOffset = new Vector2((1f - cropScale) * 0.5f, 0f);
            visual.GetComponent<MeshRenderer>().sharedMaterial = material;
            Object.DestroyImmediate(visual.GetComponent<Collider>());
        }

        private static void SavePrefab(GameObject root, string name, string outputRoot)
        {
            var folder = outputRoot + "/" + name;
            EnsureFolder(folder);
            var controllerPath = folder + "/" + name + ".controller";
            var animator = root.GetComponent<Animator>();
            animator.runtimeAnimatorController = CreateAnimatorController(controllerPath);
            var prefabPath = folder + "/" + name + ".prefab";
            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            Object.DestroyImmediate(root);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("AI Engineer character prefab created: " + prefabPath);
        }

        private static RuntimeAnimatorController CreateAnimatorController(string path)
        {
            var existing = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
            if (existing != null) return existing;
            var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            foreach (var state in new[] { "Idle", "Walk", "Run", "Jump" })
                controller.layers[0].stateMachine.AddState(state);
            return controller;
        }

        private static string ImportSourceImage(string name, string sourceImagePath, string characterFolder, bool sprite)
        {
            if (string.IsNullOrWhiteSpace(sourceImagePath)) return null;
            var normalized = sourceImagePath.Replace('\\', '/');
            if (normalized.StartsWith("Assets/", System.StringComparison.Ordinal)) return normalized;
            if (!File.Exists(sourceImagePath)) throw new FileNotFoundException("Character source image was not found.", sourceImagePath);
            EnsureFolder(characterFolder);
            var extension = Path.GetExtension(sourceImagePath);
            if (string.IsNullOrWhiteSpace(extension)) extension = ".png";
            var target = characterFolder + "/" + name + "Source" + extension.ToLowerInvariant();
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            var targetFullPath = Path.Combine(projectRoot, target.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(targetFullPath) ?? projectRoot);
            File.Copy(sourceImagePath, targetFullPath, true);
            AssetDatabase.ImportAsset(target, ImportAssetOptions.ForceSynchronousImport);
            if (sprite && AssetImporter.GetAtPath(target) is TextureImporter importer)
            {
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.SaveAndReimport();
            }
            return target;
        }

        private static void EnsureFolder(string path)
        {
            var parts = path.Split('/');
            var current = parts[0];
            for (var i = 1; i < parts.Length; i++)
            {
                var next = current + "/" + parts[i];
                if (!AssetDatabase.IsValidFolder(next))
                    AssetDatabase.CreateFolder(current, parts[i]);
                current = next;
            }
        }
    }
}

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using AIEngineer.Runtime;
using Object = UnityEngine.Object;

namespace AIEngineer.Editor.Autonomy
{
    internal static class AutonomousChangeSetExecutor
    {
        private static readonly HashSet<string> FileKinds = new(StringComparer.Ordinal)
        {
            "write_text", "replace_text", "delete_asset", "create_folder",
            "generate_image",
        };

        public static void ApplyFilePhase(AutonomousChangeSet changeSet, ChangeSetTransaction transaction)
        {
            foreach (var operation in changeSet.operations ?? Array.Empty<AutonomousChangeOperation>())
            {
                if (!FileKinds.Contains(operation.kind)) continue;
                ApplyFileOperation(operation, transaction);
            }
        }

        public static void ApplyUnityPhase(AutonomousChangeSet changeSet, ChangeSetTransaction transaction)
        {
            foreach (var operation in changeSet.operations ?? Array.Empty<AutonomousChangeOperation>())
            {
                if (FileKinds.Contains(operation.kind)) continue;
                ApplyUnityOperation(operation, transaction);
            }
            if (EditorSceneManager.GetActiveScene().isDirty) EditorSceneManager.SaveOpenScenes();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        }

        /// <summary>Verifies that every declared Unity operation left its expected artifact behind.</summary>
        public static void ValidateAppliedOperations(AutonomousChangeSet changeSet)
        {
            foreach (var operation in changeSet.operations ?? Array.Empty<AutonomousChangeOperation>())
            {
                switch (operation.kind)
                {
                    case "create_scene":
                        RequireAsset<SceneAsset>(operation.path, operation.kind);
                        break;
                    case "create_prefab":
                        RequireAsset<GameObject>(operation.assetPath, operation.kind);
                        break;
                    case "create_material":
                        RequireAsset<Material>(operation.assetPath, operation.kind);
                        break;
                    case "create_effect":
                        if (!string.IsNullOrWhiteSpace(operation.assetPath)) RequireAsset<GameObject>(operation.assetPath, operation.kind);
                        else RequireSceneObject(operation.name, operation.kind);
                        break;
                    case "create_ui_screen":
                        if (!string.IsNullOrWhiteSpace(operation.assetPath)) RequireAsset<GameObject>(operation.assetPath, operation.kind);
                        else if (!string.IsNullOrWhiteSpace(operation.scenePath)) RequireAsset<SceneAsset>(operation.scenePath, operation.kind);
                        else RequireSceneObject(operation.name, operation.kind);
                        break;
                    case "generate_image":
                        RequireAsset<Texture2D>(operation.outputPath, operation.kind);
                        if (string.Equals(operation.importType, "Sprite", StringComparison.OrdinalIgnoreCase))
                        {
                            var importer = AssetImporter.GetAtPath(operation.outputPath) as TextureImporter;
                            if (importer == null || importer.textureType != TextureImporterType.Sprite)
                                throw new InvalidOperationException($"Validation failed: {operation.kind} did not import a Sprite at '{operation.outputPath}'.");
                        }
                        break;
                    case "add_component":
                        var target = RequireSceneObject(operation.targetPath, operation.kind);
                        var componentType = ResolveComponentType(operation.component);
                        if (target.GetComponent(componentType) == null)
                            throw new InvalidOperationException($"Validation failed: {operation.kind} did not add {operation.component} to {operation.targetPath}.");
                        break;
                    case "set_property":
                        RequireSceneObject(operation.targetPath, operation.kind);
                        break;
                }
            }
        }

        private static T RequireAsset<T>(string path, string operationKind) where T : Object
        {
            var asset = AssetDatabase.LoadAssetAtPath<T>(path);
            if (asset == null) throw new InvalidOperationException($"Validation failed: {operationKind} did not create asset '{path}'.");
            return asset;
        }

        private static GameObject RequireSceneObject(string path, string operationKind)
        {
            var target = FindGameObject(path);
            if (target == null) throw new InvalidOperationException($"Validation failed: {operationKind} target was not found: '{path}'.");
            return target;
        }

        private static void ApplyFileOperation(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            switch (operation.kind)
            {
                case "write_text": WriteText(operation, transaction); break;
                case "replace_text": ReplaceText(operation, transaction); break;
                case "delete_asset": DeleteAsset(operation, transaction); break;
                case "create_folder": transaction.Snapshot(operation.path); CreateFolder(operation.path); break;
                case "generate_image": GenerateImage(operation, transaction); break;
                default: throw new InvalidOperationException("Unsupported file operation: " + operation.kind);
            }
        }

        private static void ApplyUnityOperation(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            switch (operation.kind)
            {
                case "create_scene": CreateScene(operation, transaction); break;
                case "create_game_object": CreateGameObject(operation, transaction); break;
                case "add_component": AddComponent(operation, transaction); break;
                case "set_property": SetProperty(operation, transaction); break;
                case "create_prefab": CreatePrefab(operation, transaction); break;
                case "instantiate_prefab": InstantiatePrefab(operation, transaction); break;
                case "create_material": CreateMaterial(operation, transaction); break;
                case "create_effect": CreateEffect(operation, transaction); break;
                case "create_ui_screen": CreateUiScreen(operation, transaction); break;
                case "build_character": BuildCharacter(operation, transaction); break;
                case "generate_prototype": AutonomousPrototypeBuilder.Build(operation, transaction); break;
                case "save_scene": transaction.SnapshotActiveScene(); EditorSceneManager.SaveOpenScenes(); break;
                default: throw new InvalidOperationException("Unsupported Unity operation: " + operation.kind);
            }
        }

        [Serializable]
        private sealed class GeneratedImageRequest
        {
            public string projectPath;
            public AutonomousChangeOperation operation;
        }

        private static void GenerateImage(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var outputPath = ChangeSetTransaction.NormalizeAssetPath(operation.outputPath);
            transaction.Snapshot(outputPath);
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            var payload = JsonUtility.ToJson(new GeneratedImageRequest { projectPath = projectRoot, operation = operation });
            var request = WebRequest.CreateHttp("http://127.0.0.1:8080/v1/assets/image");
            request.Method = "POST";
            request.ContentType = "application/json";
            request.Timeout = 195000;
            var bytes = System.Text.Encoding.UTF8.GetBytes(payload);
            request.ContentLength = bytes.Length;
            using (var stream = request.GetRequestStream()) stream.Write(bytes, 0, bytes.Length);
            try
            {
                using var response = (HttpWebResponse)request.GetResponse();
                using var reader = new StreamReader(response.GetResponseStream());
                var responseBody = reader.ReadToEnd();
                if (response.StatusCode != HttpStatusCode.OK)
                    throw new InvalidOperationException("Image generation backend returned " + response.StatusCode + ": " + responseBody);
            }
            catch (WebException error)
            {
                var responseBody = string.Empty;
                if (error.Response != null)
                {
                    using var reader = new StreamReader(error.Response.GetResponseStream());
                    responseBody = reader.ReadToEnd();
                }
                throw new InvalidOperationException("Image generation failed: " + responseBody, error);
            }
            if (!File.Exists(transaction.FullPath(outputPath)))
                throw new InvalidOperationException("Image generation completed without creating: " + outputPath);
            AssetDatabase.ImportAsset(outputPath, ImportAssetOptions.ForceSynchronousImport);
            if (string.Equals(operation.importType, "Sprite", StringComparison.OrdinalIgnoreCase))
            {
                var importer = AssetImporter.GetAtPath(outputPath) as TextureImporter;
                if (importer == null) throw new InvalidOperationException("Generated image has no TextureImporter: " + outputPath);
                importer.textureType = TextureImporterType.Sprite;
                importer.alphaIsTransparency = true;
                importer.SaveAndReimport();
            }
        }

        private static void WriteText(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.path);
            var fullPath = transaction.FullPath(path);
            if (File.Exists(fullPath) && !operation.overwrite)
                throw new InvalidOperationException("write_text refused to overwrite an existing file without overwrite=true: " + path);
            transaction.Snapshot(path);
            Directory.CreateDirectory(Path.GetDirectoryName(fullPath) ?? Application.dataPath);
            File.WriteAllText(fullPath, operation.content ?? string.Empty, new System.Text.UTF8Encoding(false));
        }

        private static void ReplaceText(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.path);
            var fullPath = transaction.FullPath(path);
            if (!File.Exists(fullPath)) throw new FileNotFoundException("replace_text target was not found.", path);
            var source = File.ReadAllText(fullPath);
            var search = operation.search ?? string.Empty;
            var first = source.IndexOf(search, StringComparison.Ordinal);
            if (first < 0) throw new InvalidOperationException("replace_text search block was not found in " + path);
            if (source.IndexOf(search, first + search.Length, StringComparison.Ordinal) >= 0)
                throw new InvalidOperationException("replace_text search block is ambiguous in " + path);
            transaction.Snapshot(path);
            source = source.Substring(0, first) + (operation.replacement ?? string.Empty) + source.Substring(first + search.Length);
            File.WriteAllText(fullPath, source, new System.Text.UTF8Encoding(false));
        }

        private static void DeleteAsset(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.path);
            var fullPath = transaction.FullPath(path);
            if (Directory.Exists(fullPath)) throw new InvalidOperationException("Autonomous folder deletion is not allowed: " + path);
            transaction.Snapshot(path);
            if (!AssetDatabase.DeleteAsset(path) && File.Exists(fullPath)) File.Delete(fullPath);
        }

        private static void CreateFolder(string path)
        {
            path = ChangeSetTransaction.NormalizeAssetPath(path);
            EnsureAssetFolder(path);
        }

        private static void CreateScene(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.path);
            transaction.Snapshot(path);
            EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            if (!EditorSceneManager.SaveScene(scene, path)) throw new InvalidOperationException("Scene could not be saved: " + path);
        }

        private static void CreateGameObject(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            transaction.SnapshotActiveScene();
            var gameObject = CreatePrimitive(operation.primitive, operation.name);
            ApplyTransform(gameObject.transform, operation);
            var parent = FindGameObject(operation.parentPath);
            if (parent != null) gameObject.transform.SetParent(parent.transform, true);
            ApplyComponents(gameObject, operation.components);
            Undo.RegisterCreatedObjectUndo(gameObject, "AI Engineer create GameObject");
            Selection.activeGameObject = gameObject;
            EditorSceneManager.MarkSceneDirty(gameObject.scene);
        }

        private static void AddComponent(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            transaction.SnapshotActiveScene();
            var target = FindGameObject(operation.targetPath) ?? throw new InvalidOperationException("GameObject not found: " + operation.targetPath);
            var component = AddComponent(target, operation.component);
            ApplyProperties(component, operation.properties);
            EditorSceneManager.MarkSceneDirty(target.scene);
        }

        private static void SetProperty(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            transaction.SnapshotActiveScene();
            var target = FindGameObject(operation.targetPath) ?? throw new InvalidOperationException("GameObject not found: " + operation.targetPath);
            Component component = target.transform;
            if (!string.IsNullOrWhiteSpace(operation.component))
            {
                var type = ResolveComponentType(operation.component);
                component = target.GetComponent(type) ?? throw new InvalidOperationException($"Component {operation.component} not found on {operation.targetPath}");
            }
            ApplyProperty(component, new AutonomousPropertySpec
            {
                name = operation.property, type = operation.valueType, value = operation.value, objectPath = operation.objectPath,
            });
            EditorSceneManager.MarkSceneDirty(target.scene);
        }

        private static void CreatePrefab(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
            transaction.Snapshot(path);
            EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
            var root = CreatePrimitive(operation.primitive, operation.name);
            ApplyTransform(root.transform, operation);
            ApplyComponents(root, operation.components);
            PrefabUtility.SaveAsPrefabAsset(root, path, out var success);
            Object.DestroyImmediate(root);
            if (!success) throw new InvalidOperationException("Prefab could not be saved: " + path);
        }

        private static void InstantiatePrefab(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            transaction.SnapshotActiveScene();
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path) ?? throw new InvalidOperationException("Prefab not found: " + path);
            var instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject ?? throw new InvalidOperationException("Prefab could not be instantiated: " + path);
            if (!string.IsNullOrWhiteSpace(operation.name)) instance.name = operation.name;
            ApplyTransform(instance.transform, operation);
            var parent = FindGameObject(operation.parentPath);
            if (parent != null) instance.transform.SetParent(parent.transform, true);
            EditorSceneManager.MarkSceneDirty(instance.scene);
        }

        private static void CreateMaterial(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
            transaction.Snapshot(path);
            EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
            var shader = Shader.Find(string.IsNullOrWhiteSpace(operation.shader) ? "Universal Render Pipeline/Lit" : operation.shader)
                         ?? Shader.Find("Standard") ?? Shader.Find("Unlit/Color");
            var material = new Material(shader) { name = operation.name ?? Path.GetFileNameWithoutExtension(path) };
            if (TryColor(operation.color, out var color))
            {
                if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
                else material.color = color;
            }
            AssetDatabase.CreateAsset(material, path);
        }

        private static void CreateEffect(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var root = new GameObject(string.IsNullOrWhiteSpace(operation.name) ? "Generated Effect" : operation.name);
            var particles = root.AddComponent<ParticleSystem>();
            var main = particles.main;
            main.duration = Mathf.Max(0.1f, operation.duration);
            main.startLifetime = Mathf.Max(0.1f, operation.duration * 0.7f);
            main.startSpeed = operation.startSpeed;
            main.startSize = Mathf.Max(0.01f, operation.startSize);
            main.maxParticles = Mathf.Max(1, operation.maxParticles);
            main.loop = false;
            if (TryColor(operation.color, out var color)) main.startColor = color;
            var emission = particles.emission;
            emission.rateOverTime = Mathf.Max(1, operation.maxParticles / Mathf.Max(0.1f, operation.duration));
            var shape = particles.shape;
            shape.shapeType = ParseShape(operation.shape);
            if (!string.IsNullOrWhiteSpace(operation.assetPath))
            {
                var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
                transaction.Snapshot(path);
                EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
                PrefabUtility.SaveAsPrefabAsset(root, path, out var success);
                Object.DestroyImmediate(root);
                if (!success) throw new InvalidOperationException("Effect prefab could not be saved: " + path);
            }
            else
            {
                transaction.SnapshotActiveScene();
                ApplyTransform(root.transform, operation);
                EditorSceneManager.MarkSceneDirty(root.scene);
            }
        }

        // Creates a mobile-first, safe-area-friendly game entrance screen. UI/TMP
        // types are discovered at runtime so the package supports UGUI or TMP.
        private static void CreateUiScreen(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var saveAsPrefab = !string.IsNullOrWhiteSpace(operation.assetPath);
            var saveAsScene = !string.IsNullOrWhiteSpace(operation.scenePath);
            if (saveAsPrefab && saveAsScene) throw new InvalidOperationException("A UI screen cannot use assetPath and scenePath together.");
            var originalScene = EditorSceneManager.GetActiveScene();
            var targetScenePath = string.Empty;
            var saveInGeneratedCopy = false;
            if (saveAsScene)
            {
                targetScenePath = ChangeSetTransaction.NormalizeAssetPath(operation.scenePath);
                transaction.Snapshot(targetScenePath);
                EnsureAssetFolder(Path.GetDirectoryName(targetScenePath)?.Replace('\\', '/') ?? "Assets");
                var createdScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
                EditorSceneManager.SetActiveScene(createdScene);
            }
            else if (!saveAsPrefab)
            {
                // The packaged AI Engineer sample scenes are read-only to autonomous jobs.
                // If the user is currently viewing one, clone it into the project's generated
                // content area first, then place the UI in that editable copy.
                var activePath = (originalScene.path ?? string.Empty).Replace('\\', '/');
                if (activePath.StartsWith("Assets/AIEngineer/", StringComparison.OrdinalIgnoreCase))
                {
                    var sceneName = Path.GetFileNameWithoutExtension(activePath);
                    if (string.IsNullOrWhiteSpace(sceneName)) sceneName = "GeneratedGame";
                    targetScenePath = "Assets/AIEngineerGenerated/Games/" + sceneName + "/" + sceneName + ".unity";
                    transaction.Snapshot(targetScenePath);
                    EnsureAssetFolder(Path.GetDirectoryName(targetScenePath)?.Replace('\\', '/') ?? "Assets");
                    if (!EditorSceneManager.SaveScene(originalScene, targetScenePath, true))
                        throw new InvalidOperationException("Protected sample scene could not be copied to: " + targetScenePath);
                    EditorSceneManager.OpenScene(targetScenePath, OpenSceneMode.Single);
                    saveInGeneratedCopy = true;
                    Debug.Log("[AI Autonomous] Protected sample scene copied to editable game output: " + targetScenePath);
                }
                else transaction.SnapshotActiveScene();
            }
            var sourceImage = string.IsNullOrWhiteSpace(operation.sourceImagePath) ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(operation.sourceImagePath);
            if (!saveAsScene && string.Equals(operation.referenceMode, "exact_image", StringComparison.OrdinalIgnoreCase) && sourceImage != null)
            {
                CreateExactReferenceScreen(operation, transaction, sourceImage, saveAsPrefab);
                return;
            }
            var name = string.IsNullOrWhiteSpace(operation.name) ? "Game Entrance UI" : operation.name;
            var title = string.IsNullOrWhiteSpace(operation.title) ? name : operation.title;
            var subtitle = string.IsNullOrWhiteSpace(operation.subtitle)
                ? "Oyunun amacını keşfet ve maceraya başla."
                : operation.subtitle;
            var buttonLabel = string.IsNullOrWhiteSpace(operation.buttonLabel) ? "OYNA" : operation.buttonLabel;
            var theme = string.IsNullOrWhiteSpace(operation.theme) ? "MOBİL MACERA" : operation.theme;
            var highlights = operation.highlights == null || operation.highlights.Length == 0
                ? new[] { "TEMAYI KEŞFET", "HEDEFİ TAMAMLA", "ÖDÜLLERİ KAZAN" }
                : operation.highlights.Take(3).Where(item => !string.IsNullOrWhiteSpace(item)).ToArray();
            var accent = TryColor(operation.color, out var requestedColor) ? requestedColor : new Color(0.22f, 0.82f, 0.78f, 1f);
            var referenceLayout = (operation.referenceLayout ?? string.Empty).Trim().ToLowerInvariant();
            var imageFit = string.Equals(operation.imageFit, "cover", StringComparison.OrdinalIgnoreCase) ? "cover" : "contain";
            var useReferenceBackground = sourceImage != null && string.Equals(referenceLayout, "background", StringComparison.OrdinalIgnoreCase);
            var useReferenceHero = sourceImage != null && !useReferenceBackground && !string.Equals(referenceLayout, "rebuild", StringComparison.OrdinalIgnoreCase);

            if (operation.replaceExisting)
            {
                var existingRoot = GameObject.Find(name);
                if (existingRoot != null) Undo.DestroyObjectImmediate(existingRoot);
            }

            var root = new GameObject(name, typeof(RectTransform), typeof(Canvas));
            var canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = TryAddComponent(root, "UnityEngine.UI.CanvasScaler");
            SetEnumMember(scaler, "uiScaleMode", "ScaleWithScreenSize");
            var landscape = string.Equals(operation.orientation, "landscape", StringComparison.OrdinalIgnoreCase);
            SetMember(scaler, "referenceResolution", landscape ? new Vector2(1920f, 1080f) : new Vector2(1080f, 1920f));
            SetMember(scaler, "matchWidthOrHeight", 0.5f);
            TryAddComponent(root, "UnityEngine.UI.GraphicRaycaster");
            Stretch(root.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            var backdrop = CreateUiNode("Backdrop", root.transform);
            Stretch(backdrop.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            if (useReferenceBackground) ApplyReferenceImage(backdrop, sourceImage, imageFit);
            else SetGraphicColor(TryAddComponent(backdrop, "UnityEngine.UI.Image"), new Color(0.025f, 0.06f, 0.13f, 0.98f));

            var safeArea = CreateUiNode("Safe Area", root.transform);
            Stretch(safeArea.GetComponent<RectTransform>(), new Vector2(0.06f, 0.06f), new Vector2(0.94f, 0.94f), Vector2.zero, Vector2.zero);
            var card = CreateUiNode("Game Brief Card", safeArea.transform);
            if (useReferenceBackground)
                Stretch(card.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            else
                Stretch(card.GetComponent<RectTransform>(), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), landscape ? new Vector2(1460f, 820f) : new Vector2(960f, 1420f), Vector2.zero);
            SetGraphicColor(TryAddComponent(card, "UnityEngine.UI.Image"), useReferenceBackground ? new Color(0.02f, 0.06f, 0.13f, 0.25f) : new Color(0.06f, 0.14f, 0.26f, 0.96f));

            var hero = CreateUiNode("Hero Artwork", card.transform);
            Stretch(hero.GetComponent<RectTransform>(), new Vector2(0.07f, 0.68f), new Vector2(0.93f, 0.92f), Vector2.zero, Vector2.zero);
            if (useReferenceHero) ApplyReferenceImage(hero, sourceImage, imageFit);
            else if (useReferenceBackground) hero.SetActive(false);
            else SetGraphicColor(TryAddComponent(hero, "UnityEngine.UI.Image"), new Color(accent.r * 0.35f, accent.g * 0.35f, accent.b * 0.5f, 0.9f));

            var eyebrow = CreateTextNode("Game Theme", card.transform, theme.ToUpperInvariant(), 28, new Color(0.65f, 0.82f, 0.95f, 1f));
            Stretch(eyebrow.GetComponent<RectTransform>(), new Vector2(0.1f, 0.61f), new Vector2(0.9f, 0.67f), Vector2.zero, Vector2.zero);
            var titleNode = CreateTextNode("Title", card.transform, title, 66, Color.white);
            Stretch(titleNode.GetComponent<RectTransform>(), new Vector2(0.1f, 0.46f), new Vector2(0.9f, 0.61f), Vector2.zero, Vector2.zero);
            var description = CreateTextNode("Game Objective", card.transform, subtitle, 31, new Color(0.82f, 0.89f, 0.97f, 1f));
            Stretch(description.GetComponent<RectTransform>(), new Vector2(0.1f, 0.31f), new Vector2(0.9f, 0.46f), Vector2.zero, Vector2.zero);

            var featureHeader = CreateTextNode("Highlights Header", card.transform, "OYUNDA SENİ NELER BEKLİYOR?", 20, new Color(0.55f, 0.74f, 0.9f, 1f));
            Stretch(featureHeader.GetComponent<RectTransform>(), new Vector2(0.1f, 0.255f), new Vector2(0.9f, 0.30f), Vector2.zero, Vector2.zero);
            for (var index = 0; index < highlights.Length; index++)
            {
                var highlight = CreateTextNode("Highlight " + (index + 1), card.transform, highlights[index], 19, new Color(0.93f, 0.98f, 1f, 1f));
                var width = 0.8f / Mathf.Max(1, highlights.Length);
                var min = new Vector2(0.1f + index * width, 0.18f);
                Stretch(highlight.GetComponent<RectTransform>(), min, new Vector2(min.x + width, 0.245f), Vector2.zero, Vector2.zero);
            }

            var action = CreateUiNode("Primary Action - " + buttonLabel, card.transform);
            GetCtaAnchors(operation.ctaAnchor, out var actionMin, out var actionMax);
            Stretch(action.GetComponent<RectTransform>(), actionMin, actionMax, Vector2.zero, Vector2.zero);
            SetGraphicColor(TryAddComponent(action, "UnityEngine.UI.Image"), accent);
            TryAddComponent(action, "UnityEngine.UI.Button");
            var startAction = action.AddComponent<StartGameButtonAction>();
            startAction.entranceRoot = root;
            startAction.gameplayRoot = FindGameObject(operation.gameplayTarget);
            startAction.gameplayScenePath = operation.gameplayScenePath;
            var actionText = CreateTextNode("Label", action.transform, buttonLabel, 36, new Color(0.02f, 0.07f, 0.12f, 1f));
            Stretch(actionText.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            if (operation.pulseAccent)
            {
                var glow = CreateUiNode("Pulse Accent", card.transform);
                Stretch(glow.GetComponent<RectTransform>(), new Vector2(0.38f, 0.145f), new Vector2(0.62f, 0.18f), Vector2.zero, Vector2.zero);
                SetGraphicColor(TryAddComponent(glow, "UnityEngine.UI.Image"), new Color(accent.r, accent.g, accent.b, 0.7f));
                glow.AddComponent<CanvasGroup>();
                glow.AddComponent<UiPulse>();
            }

            if (saveAsPrefab)
            {
                var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
                transaction.Snapshot(path);
                EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
                PrefabUtility.SaveAsPrefabAsset(root, path, out var success);
                Object.DestroyImmediate(root);
                if (!success) throw new InvalidOperationException("UI prefab could not be saved: " + path);
            }
            else if (saveAsScene || saveInGeneratedCopy)
            {
                EnsureUiEventSystem();
                if (!EditorSceneManager.SaveScene(root.scene, targetScenePath))
                    throw new InvalidOperationException("UI scene could not be saved: " + targetScenePath);
                if (saveAsScene) EditorSceneManager.SetActiveScene(originalScene);
                Selection.activeGameObject = root;
            }
            else
            {
                EnsureUiEventSystem();
                Undo.RegisterCreatedObjectUndo(root, "AI Engineer create game entrance UI");
                EditorSceneManager.MarkSceneDirty(root.scene);
                Selection.activeGameObject = root;
            }
        }

        private static void CreateExactReferenceScreen(AutonomousChangeOperation operation, ChangeSetTransaction transaction, Texture2D sourceImage, bool saveAsPrefab)
        {
            var name = string.IsNullOrWhiteSpace(operation.name) ? "Reference UI" : operation.name;
            var root = new GameObject(name, typeof(RectTransform), typeof(Canvas));
            root.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = TryAddComponent(root, "UnityEngine.UI.CanvasScaler");
            SetEnumMember(scaler, "uiScaleMode", "ScaleWithScreenSize");
            SetMember(scaler, "referenceResolution", new Vector2(sourceImage.width, sourceImage.height));
            TryAddComponent(root, "UnityEngine.UI.GraphicRaycaster");
            var artwork = CreateUiNode("Exact Reference Artwork", root.transform);
            Stretch(artwork.GetComponent<RectTransform>(), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            var rawImage = TryAddComponent(artwork, "UnityEngine.UI.RawImage");
            if (rawImage == null) throw new InvalidOperationException("Unity RawImage component is unavailable.");
            SetMember(rawImage, "texture", sourceImage);
            SetGraphicColor(rawImage, Color.white);
            var fitter = TryAddComponent(artwork, "UnityEngine.UI.AspectRatioFitter");
            SetEnumMember(fitter, "aspectMode", "FitInParent");
            SetMember(fitter, "aspectRatio", sourceImage.width / (float)Mathf.Max(1, sourceImage.height));
            if (saveAsPrefab)
            {
                var path = ChangeSetTransaction.NormalizeAssetPath(operation.assetPath);
                transaction.Snapshot(path);
                EnsureAssetFolder(Path.GetDirectoryName(path)?.Replace('\\', '/') ?? "Assets");
                PrefabUtility.SaveAsPrefabAsset(root, path, out var success);
                Object.DestroyImmediate(root);
                if (!success) throw new InvalidOperationException("Reference UI prefab could not be saved: " + path);
            }
            else
            {
                EnsureUiEventSystem();
                Undo.RegisterCreatedObjectUndo(root, "AI Engineer create reference UI");
                EditorSceneManager.MarkSceneDirty(root.scene);
                Selection.activeGameObject = root;
            }
        }

        private static GameObject CreateUiNode(string name, Transform parent)
        {
            var node = new GameObject(name, typeof(RectTransform));
            node.transform.SetParent(parent, false);
            return node;
        }

        // Layout is chosen by the local model's change set, not by a fixed UI
        // template.  This helper only turns that reviewed decision into UGUI.
        private static void ApplyReferenceImage(GameObject target, Texture2D sourceImage, string imageFit)
        {
            var rawImage = TryAddComponent(target, "UnityEngine.UI.RawImage");
            SetMember(rawImage, "texture", sourceImage);
            SetGraphicColor(rawImage, Color.white);
            var fitter = TryAddComponent(target, "UnityEngine.UI.AspectRatioFitter");
            SetEnumMember(fitter, "aspectMode", string.Equals(imageFit, "cover", StringComparison.OrdinalIgnoreCase) ? "EnvelopeParent" : "FitInParent");
            SetMember(fitter, "aspectRatio", sourceImage.width / (float)Mathf.Max(1, sourceImage.height));
        }

        private static void GetCtaAnchors(string anchor, out Vector2 min, out Vector2 max)
        {
            switch ((anchor ?? string.Empty).Trim().ToLowerInvariant())
            {
                case "top_left": min = new Vector2(0.06f, 0.84f); max = new Vector2(0.34f, 0.93f); break;
                case "top_center": min = new Vector2(0.36f, 0.84f); max = new Vector2(0.64f, 0.93f); break;
                case "top_right": min = new Vector2(0.66f, 0.84f); max = new Vector2(0.94f, 0.93f); break;
                case "center_left": min = new Vector2(0.06f, 0.46f); max = new Vector2(0.34f, 0.55f); break;
                case "center": min = new Vector2(0.36f, 0.46f); max = new Vector2(0.64f, 0.55f); break;
                case "center_right": min = new Vector2(0.66f, 0.46f); max = new Vector2(0.94f, 0.55f); break;
                case "bottom_left": min = new Vector2(0.06f, 0.07f); max = new Vector2(0.34f, 0.16f); break;
                case "bottom_right": min = new Vector2(0.66f, 0.07f); max = new Vector2(0.94f, 0.16f); break;
                default: min = new Vector2(0.30f, 0.07f); max = new Vector2(0.70f, 0.16f); break;
            }
        }

        private static GameObject CreateTextNode(string name, Transform parent, string text, int size, Color color)
        {
            var node = CreateUiNode(name, parent);
            var component = TryAddComponent(node, "TMPro.TextMeshProUGUI") ?? TryAddComponent(node, "UnityEngine.UI.Text");
            if (component == null) throw new InvalidOperationException("No Unity UI text component is available. Install TextMeshPro or UGUI.");
            SetMember(component, "text", text);
            SetMember(component, "fontSize", (float)size);
            SetEnumMember(component, "alignment", "Center", "MiddleCenter");
            SetGraphicColor(component, color);
            return node;
        }

        private static Component TryAddComponent(GameObject target, string typeName)
        {
            try { return AddComponent(target, typeName); }
            catch (InvalidOperationException) { return null; }
        }

        private static void Stretch(RectTransform transform, Vector2 min, Vector2 max, Vector2 size, Vector2 position)
        {
            transform.anchorMin = min;
            transform.anchorMax = max;
            transform.sizeDelta = size;
            transform.anchoredPosition = position;
        }

        private static void SetGraphicColor(Component component, Color color)
        {
            if (component != null) SetMember(component, "color", color);
        }

        private static void SetMember(Component component, string name, object value)
        {
            if (component == null) return;
            var flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            var property = component.GetType().GetProperty(name, flags);
            if (property?.CanWrite == true) { property.SetValue(component, value); return; }
            var field = component.GetType().GetField(name, flags);
            if (field != null) field.SetValue(component, value);
        }

        private static void SetEnumMember(Component component, string name, params string[] candidates)
        {
            if (component == null) return;
            var flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            var property = component.GetType().GetProperty(name, flags);
            if (property?.CanWrite != true || !property.PropertyType.IsEnum) return;
            foreach (var candidate in candidates)
            {
                if (!Enum.TryParse(property.PropertyType, candidate, true, out var parsed)) continue;
                property.SetValue(component, parsed);
                return;
            }
        }

        private static void EnsureUiEventSystem()
        {
            var eventSystemType = TypeCache.GetTypesDerivedFrom<Component>().FirstOrDefault(type => type.FullName == "UnityEngine.EventSystems.EventSystem");
            if (eventSystemType == null || Resources.FindObjectsOfTypeAll(eventSystemType).Length > 0) return;
            var eventSystem = new GameObject("EventSystem");
            AddComponent(eventSystem, eventSystemType.FullName);
            if (TryAddComponent(eventSystem, "UnityEngine.EventSystems.StandaloneInputModule") == null)
                TryAddComponent(eventSystem, "UnityEngine.InputSystem.UI.InputSystemUIInputModule");
        }

        private static void BuildCharacter(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var safeName = new string((operation.name ?? "GeneratedCharacter").Where(character => char.IsLetterOrDigit(character) || character == '_').ToArray());
            if (string.IsNullOrWhiteSpace(safeName)) safeName = "GeneratedCharacter";
            var root = "Assets/AIEngineerGenerated/Characters/" + safeName;
            transaction.Snapshot(root + "/" + safeName + ".prefab");
            transaction.Snapshot(root + "/" + safeName + ".controller");
            transaction.Snapshot(root + "/" + safeName + "ConceptArt.mat");
            if (!string.IsNullOrWhiteSpace(operation.sourceImagePath) && !operation.sourceImagePath.Replace('\\', '/').StartsWith("Assets/", StringComparison.Ordinal))
            {
                var extension = Path.GetExtension(operation.sourceImagePath);
                if (string.IsNullOrWhiteSpace(extension)) extension = ".png";
                transaction.Snapshot(root + "/" + safeName + "Source" + extension.ToLowerInvariant());
            }
            CharacterPrefabBuilder.BuildFromExternalImage(safeName, operation.dimension, operation.sourceImagePath, root);
        }

        internal static void ApplyComponents(GameObject target, AutonomousComponentSpec[] components)
        {
            if (components == null) return;
            foreach (var spec in components)
            {
                if (spec == null || string.IsNullOrWhiteSpace(spec.type)) continue;
                var component = AddComponent(target, spec.type);
                ApplyProperties(component, spec.properties);
            }
        }

        private static Component AddComponent(GameObject target, string typeName)
        {
            var type = ResolveComponentType(typeName);
            if (type == typeof(Transform)) return target.transform;
            var existing = target.GetComponent(type);
            return existing ?? Undo.AddComponent(target, type);
        }

        private static Type ResolveComponentType(string typeName)
        {
            var type = TypeCache.GetTypesDerivedFrom<Component>().FirstOrDefault(candidate =>
                string.Equals(candidate.FullName, typeName, StringComparison.Ordinal) ||
                string.Equals(candidate.Name, typeName, StringComparison.Ordinal));
            return type ?? throw new InvalidOperationException("Unity component type was not found after compilation: " + typeName);
        }

        private static void ApplyProperties(Component component, AutonomousPropertySpec[] properties)
        {
            if (properties == null) return;
            foreach (var property in properties) ApplyProperty(component, property);
        }

        private static void ApplyProperty(Component component, AutonomousPropertySpec spec)
        {
            if (component == null || spec == null || string.IsNullOrWhiteSpace(spec.name)) return;
            var serialized = new SerializedObject(component);
            var property = serialized.FindProperty(spec.name);
            if (property != null)
            {
                SetSerializedValue(property, spec);
                serialized.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(component);
                return;
            }
            var flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            var field = component.GetType().GetField(spec.name, flags);
            if (field != null) { field.SetValue(component, ConvertValue(field.FieldType, spec)); EditorUtility.SetDirty(component); return; }
            var reflected = component.GetType().GetProperty(spec.name, flags);
            if (reflected?.CanWrite == true) { reflected.SetValue(component, ConvertValue(reflected.PropertyType, spec)); EditorUtility.SetDirty(component); return; }
            throw new InvalidOperationException($"Property '{spec.name}' was not found on {component.GetType().Name}.");
        }

        private static void SetSerializedValue(SerializedProperty property, AutonomousPropertySpec spec)
        {
            switch (property.propertyType)
            {
                case SerializedPropertyType.String: property.stringValue = spec.value ?? string.Empty; break;
                case SerializedPropertyType.Boolean: property.boolValue = bool.Parse(spec.value); break;
                case SerializedPropertyType.Integer: property.intValue = int.Parse(spec.value, CultureInfo.InvariantCulture); break;
                case SerializedPropertyType.Float: property.floatValue = float.Parse(spec.value, CultureInfo.InvariantCulture); break;
                case SerializedPropertyType.Color: if (TryColor(spec.value, out var color)) property.colorValue = color; else throw new FormatException("Invalid color: " + spec.value); break;
                case SerializedPropertyType.Vector2: property.vector2Value = ParseVector2(spec.value); break;
                case SerializedPropertyType.Vector3: property.vector3Value = ParseVector3(spec.value); break;
                case SerializedPropertyType.ObjectReference: property.objectReferenceValue = ResolveObject(spec); break;
                case SerializedPropertyType.Enum: property.enumValueIndex = int.TryParse(spec.value, out var index) ? index : Array.IndexOf(property.enumDisplayNames, spec.value); break;
                default: throw new InvalidOperationException("Unsupported serialized property type: " + property.propertyType);
            }
        }

        private static object ConvertValue(Type type, AutonomousPropertySpec spec)
        {
            if (type == typeof(string)) return spec.value ?? string.Empty;
            if (type == typeof(bool)) return bool.Parse(spec.value);
            if (type == typeof(int)) return int.Parse(spec.value, CultureInfo.InvariantCulture);
            if (type == typeof(float)) return float.Parse(spec.value, CultureInfo.InvariantCulture);
            if (type == typeof(Vector2)) return ParseVector2(spec.value);
            if (type == typeof(Vector3)) return ParseVector3(spec.value);
            if (type == typeof(Color) && TryColor(spec.value, out var color)) return color;
            if (typeof(Object).IsAssignableFrom(type)) return ResolveObject(spec);
            if (type.IsEnum) return Enum.Parse(type, spec.value, true);
            return Convert.ChangeType(spec.value, type, CultureInfo.InvariantCulture);
        }

        private static Object ResolveObject(AutonomousPropertySpec spec)
        {
            var reference = !string.IsNullOrWhiteSpace(spec.objectPath) ? spec.objectPath : spec.value;
            if (reference.StartsWith("Assets/", StringComparison.Ordinal)) return AssetDatabase.LoadAssetAtPath<Object>(reference);
            return FindGameObject(reference);
        }

        private static GameObject CreatePrimitive(string primitive, string name)
        {
            var created = Enum.TryParse(primitive, true, out PrimitiveType type) ? GameObject.CreatePrimitive(type) : new GameObject();
            created.name = string.IsNullOrWhiteSpace(name) ? "AI Generated Object" : name;
            return created;
        }

        private static GameObject FindGameObject(string path)
        {
            if (string.IsNullOrWhiteSpace(path)) return null;
            foreach (var root in EditorSceneManager.GetActiveScene().GetRootGameObjects())
            {
                if (root.name == path) return root;
                if (path.StartsWith(root.name + "/", StringComparison.Ordinal))
                {
                    var child = root.transform.Find(path.Substring(root.name.Length + 1));
                    if (child != null) return child.gameObject;
                }
            }
            return Resources.FindObjectsOfTypeAll<GameObject>().FirstOrDefault(item => item.scene.IsValid() && item.name == path);
        }

        private static void ApplyTransform(Transform transform, AutonomousChangeOperation operation)
        {
            if (operation.position?.Length >= 3) transform.position = new Vector3(operation.position[0], operation.position[1], operation.position[2]);
            if (operation.rotation?.Length >= 3) transform.eulerAngles = new Vector3(operation.rotation[0], operation.rotation[1], operation.rotation[2]);
            if (operation.scale?.Length >= 3) transform.localScale = new Vector3(operation.scale[0], operation.scale[1], operation.scale[2]);
        }

        internal static void EnsureAssetFolder(string path)
        {
            path = (path ?? "Assets").Replace('\\', '/').TrimEnd('/');
            if (path == "Assets") return;
            ChangeSetTransaction.NormalizeAssetPath(path);
            var parts = path.Split('/');
            var current = "Assets";
            for (var index = 1; index < parts.Length; index++)
            {
                var next = current + "/" + parts[index];
                if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, parts[index]);
                current = next;
            }
        }

        private static bool TryColor(string text, out Color color)
        {
            if (ColorUtility.TryParseHtmlString(string.IsNullOrWhiteSpace(text) ? "#FFFFFF" : text, out color)) return true;
            return ColorUtility.TryParseHtmlString("#" + text, out color);
        }

        private static Vector2 ParseVector2(string text)
        {
            var values = (text ?? string.Empty).Split(',').Select(value => float.Parse(value.Trim(), CultureInfo.InvariantCulture)).ToArray();
            if (values.Length < 2) throw new FormatException("Vector2 requires x,y.");
            return new Vector2(values[0], values[1]);
        }

        private static Vector3 ParseVector3(string text)
        {
            var values = (text ?? string.Empty).Split(',').Select(value => float.Parse(value.Trim(), CultureInfo.InvariantCulture)).ToArray();
            if (values.Length < 3) throw new FormatException("Vector3 requires x,y,z.");
            return new Vector3(values[0], values[1], values[2]);
        }

        private static ParticleSystemShapeType ParseShape(string shape)
        {
            return Enum.TryParse(shape, true, out ParticleSystemShapeType parsed) ? parsed : ParticleSystemShapeType.Cone;
        }
    }
}

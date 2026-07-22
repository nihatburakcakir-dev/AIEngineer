using System;
using System.IO;
using AIEngineer.Games;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace AIEngineer.Editor.Games
{
    /// <summary>Builds a playable known-game prototype from a reviewed JSON request and verifies it in a separate automated run. Phase 11 reference-image trigger.</summary>
    public static class GameProjectScaffolder
    {
        // Generated games are project content, never part of the protected AI Engineer package.
        private const string OutputRoot = "Assets/AIEngineerGenerated/Games";
        private const string PendingRequestPath = OutputRoot + "/GameBuildRequest.json";

        [Serializable]
        private sealed class GameBuildRequest
        {
            public string gameKey;
            public string gameName;
            public string scenePath;
            public string[] systems;
            public string[] acceptanceSignals;
            public bool autoPlayValidation;
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

        [MenuItem("AI Engineer/Games/Create Zuma Prototype")]
        public static void CreateZumaPrototype()
        {
            Build(new GameBuildRequest
            {
                gameKey = "zuma_match",
                gameName = "ZumaPrototype",
                scenePath = OutputRoot + "/ZumaPrototype/ZumaPrototype.unity",
                autoPlayValidation = true,
            });
        }

        public static void BuildPendingRequest()
        {
            var request = JsonUtility.FromJson<GameBuildRequest>(File.ReadAllText(PendingRequestPath));
            if (request == null || request.gameKey != "zuma_match")
            {
                Debug.LogError("AI Engineer game request is invalid or not yet supported.");
                return;
            }

            Build(request);
            AssetDatabase.DeleteAsset(PendingRequestPath);
        }

        private static void Build(GameBuildRequest request)
        {
            var gameName = string.IsNullOrWhiteSpace(request.gameName) ? "ZumaPrototype" : request.gameName;
            var scenePath = string.IsNullOrWhiteSpace(request.scenePath)
                ? OutputRoot + "/" + gameName + "/" + gameName + ".unity"
                : request.scenePath;
            EnsureFolder(OutputRoot);
            EnsureFolder(OutputRoot + "/" + gameName);
            EnsureFolder(OutputRoot + "/" + gameName + "/Scripts");
            EnsureFolder(OutputRoot + "/" + gameName + "/Prefabs");
            EnsureFolder(OutputRoot + "/" + gameName + "/Materials");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            CreateCamera();
            CreateLight();
            var manager = new GameObject("ZumaGameManager").AddComponent<ZumaGameManager>();
            var hud = CreateMobileHud();
            manager.Configure(hud.score, hud.hint);
            var shooter = CreateShooter(manager);
            hud.fire.onClick.AddListener(shooter.FireForward);
            CreateTurkishMythologyEnvironment();
            CreateWindingMarblePath();
            CreateMarbleChain(manager);
            CreateBackground();
            EditorSceneManager.SaveScene(scene, scenePath);
            AssetDatabase.SaveAssets();
            Debug.Log("AI Engineer ZumaPrototype created: " + scenePath);

            if (request.autoPlayValidation)
                ZumaPlayModeValidator.Validate(scenePath);
        }

        private static void CreateCamera()
        {
            var camera = new GameObject("Main Camera").AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.orthographicSize = 5.35f;
            camera.transform.position = new Vector3(0f, 0f, -10f);
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.015f, 0.035f, 0.09f);
        }

        private static void CreateLight()
        {
            var light = new GameObject("Key Light").AddComponent<Light>();
            light.type = LightType.Directional;
            light.transform.rotation = Quaternion.Euler(45f, -30f, 0f);
        }

        private static void CreateBackground()
        {
            var background = GameObject.CreatePrimitive(PrimitiveType.Quad);
            background.name = "Tengri Night Sky";
            background.transform.position = new Vector3(0f, 0f, 3f);
            background.transform.localScale = new Vector3(11f, 18f, 1f);
            SetEditorColor(background, new Color(0.018f, 0.06f, 0.16f));

            var moon = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            moon.name = "Tengri Moon";
            moon.transform.position = new Vector3(3.7f, 3.65f, 1.8f);
            moon.transform.localScale = Vector3.one * 0.62f;
            SetEditorColor(moon, new Color(0.55f, 0.85f, 1f));
        }

        private sealed class MobileHud
        {
            public Text score;
            public Text hint;
            public Button fire;
        }

        private static MobileHud CreateMobileHud()
        {
            if (UnityEngine.Object.FindFirstObjectByType<EventSystem>() == null)
            {
                var events = new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
                events.name = "Mobile Event System";
            }

            var canvasObject = new GameObject("Mobile HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasObject.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 10;
            var scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080f, 1920f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            var hud = new MobileHud();
            var titlePanel = CreatePanel(canvas.transform, "Top Ornament", new Color(0.025f, 0.08f, 0.17f, 0.92f), new Vector2(0f, 0.9f), new Vector2(1f, 1f), new Vector2(32f, -18f), new Vector2(-32f, -150f));
            CreateText(titlePanel.transform, "GOKBORU: ATES YOLU", 42, TextAnchor.UpperCenter, new Color(1f, 0.72f, 0.2f), new Vector2(0f, 0.46f), new Vector2(1f, 1f), new Vector2(0f, 0f), new Vector2(0f, 0f));
            CreateText(titlePanel.transform, "TENGRI'NIN KORUDUGU KUTSAL YOL", 20, TextAnchor.UpperCenter, new Color(0.5f, 0.85f, 1f), new Vector2(0f, 0.1f), new Vector2(1f, 0.5f), Vector2.zero, Vector2.zero);

            var scorePanel = CreatePanel(canvas.transform, "Score Frame", new Color(0.07f, 0.12f, 0.17f, 0.94f), new Vector2(0.04f, 0.77f), new Vector2(0.35f, 0.9f), Vector2.zero, Vector2.zero);
            hud.score = CreateText(scorePanel.transform, "PUAN\n0000", 30, TextAnchor.MiddleCenter, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            var pause = CreatePanel(canvas.transform, "Pause Frame", new Color(0.07f, 0.12f, 0.17f, 0.94f), new Vector2(0.82f, 0.79f), new Vector2(0.96f, 0.9f), Vector2.zero, Vector2.zero);
            CreateText(pause.transform, "II", 38, TextAnchor.MiddleCenter, new Color(1f, 0.76f, 0.25f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            hud.hint = CreateText(canvas.transform, "NISAN AL • ATES ET • UC AYNI RENGI BIRLESTIR", 19, TextAnchor.MiddleCenter, new Color(0.8f, 0.93f, 1f), new Vector2(0.08f, 0.165f), new Vector2(0.92f, 0.215f), Vector2.zero, Vector2.zero);
            var fireObject = CreatePanel(canvas.transform, "Fire Button", new Color(0.78f, 0.17f, 0.06f, 0.98f), new Vector2(0.34f, 0.035f), new Vector2(0.66f, 0.14f), Vector2.zero, Vector2.zero);
            hud.fire = fireObject.gameObject.AddComponent<Button>();
            hud.fire.targetGraphic = fireObject.GetComponent<Image>();
            var state = hud.fire.colors;
            state.highlightedColor = new Color(1f, 0.55f, 0.12f, 1f);
            state.pressedColor = new Color(0.38f, 0.07f, 0.02f, 1f);
            hud.fire.colors = state;
            CreateText(fireObject.transform, "ATES ET", 34, TextAnchor.MiddleCenter, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            return hud;
        }

        private static ZumaShooter CreateShooter(ZumaGameManager manager)
        {
            var shooter = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            shooter.name = "Bozkurt Fire Totem";
            shooter.transform.position = new Vector3(0f, -3.75f, 0f);
            shooter.transform.localScale = Vector3.one * 0.74f;
            SetEditorColor(shooter, new Color(0.16f, 0.82f, 0.8f));
            var controller = shooter.AddComponent<ZumaShooter>();
            controller.Configure(manager);
            return controller;
        }

        private static void CreateMarbleChain(ZumaGameManager manager)
        {
            var colors = new[] { new Color(0.9f, 0.17f, 0.11f), new Color(0.9f, 0.17f, 0.11f), new Color(0.9f, 0.17f, 0.11f), new Color(1f, 0.69f, 0.08f), new Color(1f, 0.69f, 0.08f), new Color(1f, 0.69f, 0.08f), new Color(0.08f, 0.72f, 0.9f), new Color(0.08f, 0.72f, 0.9f), new Color(0.08f, 0.72f, 0.9f), new Color(0.62f, 0.2f, 0.9f), new Color(0.62f, 0.2f, 0.9f), new Color(0.62f, 0.2f, 0.9f) };
            for (var index = 0; index < colors.Length; index++)
            {
                var marble = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                marble.name = "Marble_" + index;
                var point = TrackPoint(0.17f + index * 0.055f);
                marble.transform.position = new Vector3(point.x, point.y, 0f);
                marble.transform.localScale = Vector3.one * 0.54f;
                SetEditorColor(marble, colors[index]);
                marble.AddComponent<ZumaMarble>().Configure(manager, colors[index]);
            }
        }

        private static void CreateWindingMarblePath()
        {
            for (var index = 0; index <= 46; index++)
            {
                var point = TrackPoint(index / 46f);
                var tile = GameObject.CreatePrimitive(PrimitiveType.Quad);
                tile.name = "Sacred Path Tile " + index;
                tile.transform.position = new Vector3(point.x, point.y, 1.35f);
                tile.transform.localScale = new Vector3(0.72f, 0.42f, 1f);
                SetEditorColor(tile, index % 2 == 0 ? new Color(0.3f, 0.19f, 0.09f) : new Color(0.42f, 0.28f, 0.11f));
            }
        }

        private static Vector2 TrackPoint(float t)
        {
            var y = Mathf.Lerp(-3.25f, 3.3f, t);
            var x = Mathf.Sin(t * Mathf.PI * 4.35f) * 2.3f;
            return new Vector2(x, y);
        }

        private static void CreateTurkishMythologyEnvironment()
        {
            CreateTotem("Bozkurt Gate Left", new Vector3(-4.25f, 2.5f, 1.45f), new Color(0.13f, 0.28f, 0.36f));
            CreateTotem("Bozkurt Gate Right", new Vector3(4.25f, 2.5f, 1.45f), new Color(0.13f, 0.28f, 0.36f));
            CreateTotem("Ergenekon Forge", new Vector3(3.7f, -2.6f, 1.45f), new Color(0.66f, 0.17f, 0.04f));
            CreateTotem("Simurg Shrine", new Vector3(-3.7f, -1.8f, 1.45f), new Color(0.12f, 0.42f, 0.7f));
            CreateWorldLabel("TENGRI RUNES", new Vector3(0f, 3.85f, 1.2f), new Color(0.52f, 0.88f, 1f));
        }

        private static void CreateTotem(string name, Vector3 position, Color color)
        {
            var pillar = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pillar.name = name;
            pillar.transform.position = position;
            pillar.transform.localScale = new Vector3(0.48f, 1.12f, 1f);
            SetEditorColor(pillar, color);
            var rune = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            rune.name = name + " Rune";
            rune.transform.position = position + new Vector3(0f, 0.68f, -0.15f);
            rune.transform.localScale = Vector3.one * 0.3f;
            SetEditorColor(rune, new Color(1f, 0.64f, 0.13f));
        }

        private static void CreateWorldLabel(string message, Vector3 position, Color color)
        {
            var label = new GameObject("Rune Label").AddComponent<TextMesh>();
            label.text = message;
            label.transform.position = position;
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.characterSize = 0.17f;
            label.fontSize = 42;
            label.color = color;
        }

        private static Image CreatePanel(Transform parent, string name, Color color, Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
        {
            var panel = new GameObject(name, typeof(RectTransform), typeof(Image));
            panel.transform.SetParent(parent, false);
            var image = panel.GetComponent<Image>();
            image.color = color;
            var rect = panel.GetComponent<RectTransform>();
            rect.anchorMin = anchorMin;
            rect.anchorMax = anchorMax;
            rect.offsetMin = offsetMin;
            rect.offsetMax = offsetMax;
            return image;
        }

        private static Text CreateText(Transform parent, string message, int fontSize, TextAnchor anchor, Color color, Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
        {
            var textObject = new GameObject("HUD Text", typeof(RectTransform), typeof(Text));
            textObject.transform.SetParent(parent, false);
            var text = textObject.GetComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.text = message;
            text.fontSize = fontSize;
            text.alignment = anchor;
            text.color = color;
            var rect = text.GetComponent<RectTransform>();
            rect.anchorMin = anchorMin;
            rect.anchorMax = anchorMax;
            rect.offsetMin = offsetMin;
            rect.offsetMax = offsetMax;
            return text;
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path))
                return;
            var parent = Path.GetDirectoryName(path)?.Replace("\\", "/");
            var folder = Path.GetFileName(path);
            if (!string.IsNullOrEmpty(parent) && !string.IsNullOrEmpty(folder))
                AssetDatabase.CreateFolder(parent, folder);
        }

        private static void SetEditorColor(GameObject target, Color color)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            target.GetComponent<Renderer>().sharedMaterial = new Material(shader) { color = color };
        }
    }

    [InitializeOnLoad]
    public static class ZumaPlayModeValidator
    {
        private const string PendingSceneKey = "AIEngineer.ZumaPlayModeValidator.Scene";
        private static double startedAt;
        private static bool probeRequested;

        static ZumaPlayModeValidator()
        {
            EditorApplication.playModeStateChanged += OnPlayModeChanged;
            if (EditorApplication.isPlaying && !string.IsNullOrEmpty(EditorPrefs.GetString(PendingSceneKey)))
                BeginVerification();
        }

        public static void Validate(string scenePath)
        {
            EditorPrefs.SetString(PendingSceneKey, scenePath);
            EditorApplication.delayCall += () => EditorApplication.isPlaying = true;
        }

        private static void OnPlayModeChanged(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredPlayMode && !string.IsNullOrEmpty(EditorPrefs.GetString(PendingSceneKey)))
                BeginVerification();
        }

        private static void BeginVerification()
        {
            startedAt = EditorApplication.timeSinceStartup;
            EditorApplication.update -= VerifyRuntime;
            EditorApplication.update += VerifyRuntime;
        }

        private static void VerifyRuntime()
        {
            if (ZumaGameManager.RuntimeReady && !probeRequested)
            {
                UnityEngine.Object.FindFirstObjectByType<ZumaGameManager>()?.RunAcceptanceProbe();
                probeRequested = true;
            }
            if ((!ZumaGameManager.RuntimeReady || !ZumaGameManager.MechanicsVerified) && EditorApplication.timeSinceStartup - startedAt < 8d)
                return;
            EditorApplication.update -= VerifyRuntime;
            if (ZumaGameManager.RuntimeReady && ZumaGameManager.MechanicsVerified)
                Debug.Log("AI Engineer Zuma play mode acceptance passed: runtime entered and core mechanics scored.");
            else
                Debug.LogError("AI Engineer Zuma play mode acceptance failed: runtime or mechanics did not initialize.");
            EditorPrefs.DeleteKey(PendingSceneKey);
            probeRequested = false;
            EditorApplication.isPlaying = false;
        }
    }
}

using System;
using System.IO;
using AIEngineer.Games;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace AIEngineer.Editor.Autonomy
{
    internal static class AutonomousPrototypeBuilder
    {
        public static void Build(AutonomousChangeOperation operation, ChangeSetTransaction transaction)
        {
            var safeName = SafeName(operation.name);
            var scenePath = string.IsNullOrWhiteSpace(operation.scenePath)
                ? $"Assets/AIEngineerGenerated/Games/{safeName}/{safeName}.unity"
                : ChangeSetTransaction.NormalizeAssetPath(operation.scenePath);
            transaction.Snapshot(scenePath);
            AutonomousChangeSetExecutor.EnsureAssetFolder(Path.GetDirectoryName(scenePath)?.Replace('\\', '/') ?? "Assets");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var is3D = IsThreeDimensional(operation.gameKey);
            CreateCamera(is3D);
            CreateLighting();
            CreateGround(is3D);
            var manager = new GameObject("AI Prototype - " + safeName);
            manager.AddComponent<AutonomousPrototypeRuntime>().Configure(operation.gameKey, operation.name, operation.systems, is3D);
            if (!EditorSceneManager.SaveScene(scene, scenePath))
                throw new InvalidOperationException("Generated prototype scene could not be saved: " + scenePath);
            Debug.Log("[AI Autonomous] Playable prototype generated: " + scenePath);
        }

        private static void CreateCamera(bool is3D)
        {
            var cameraObject = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            cameraObject.tag = "MainCamera";
            var camera = cameraObject.GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.025f, 0.055f, 0.1f);
            camera.orthographic = !is3D;
            camera.orthographicSize = 6.5f;
            if (is3D)
            {
                cameraObject.transform.position = new Vector3(0f, 10f, -13f);
                cameraObject.transform.rotation = Quaternion.Euler(28f, 0f, 0f);
            }
            else cameraObject.transform.position = new Vector3(0f, 0f, -10f);
        }

        private static void CreateLighting()
        {
            var lightObject = new GameObject("Key Light", typeof(Light));
            var light = lightObject.GetComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.25f;
            light.color = new Color(0.82f, 0.9f, 1f);
            lightObject.transform.rotation = Quaternion.Euler(42f, -28f, 0f);
        }

        private static void CreateGround(bool is3D)
        {
            if (!is3D) return;
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Prototype Ground";
            ground.transform.localScale = new Vector3(2.2f, 1f, 2.2f);
            var renderer = ground.GetComponent<Renderer>();
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            renderer.material = new Material(shader) { color = new Color(0.08f, 0.13f, 0.18f) };
        }

        private static bool IsThreeDimensional(string gameKey)
        {
            var key = (gameKey ?? string.Empty).ToLowerInvariant();
            return key.Contains("fps") || key.Contains("first_person") || key.Contains("third_person") || key.Contains("rpg") ||
                   key.Contains("racing") || key.Contains("flight") || key.Contains("horror") || key.Contains("moba") || key.Contains("shooter");
        }

        private static string SafeName(string value)
        {
            var characters = (value ?? "GeneratedPrototype").ToCharArray();
            var output = string.Empty;
            foreach (var character in characters)
                if (char.IsLetterOrDigit(character) || character == '_') output += character;
            return string.IsNullOrWhiteSpace(output) ? "GeneratedPrototype" : output;
        }
    }
}

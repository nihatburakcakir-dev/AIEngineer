using System;
using System.Collections.Generic;
using UnityEngine;

namespace AIEngineer.Games
{
    /// <summary>Playable base runtime shared by model-generated prototype scenes.</summary>
    public sealed class AutonomousPrototypeRuntime : MonoBehaviour
    {
        [SerializeField] private string gameKey = "prototype";
        [SerializeField] private string gameName = "AI Prototype";
        [SerializeField] private string[] systems = Array.Empty<string>();
        [SerializeField] private bool threeDimensional;
        [SerializeField] private float moveSpeed = 6f;
        [SerializeField] private GameObject player;

        private readonly List<GameObject> pickups = new();
        private int score;
        private float elapsed;
        private string eventMessage = "Prototype ready";

        public void Configure(string key, string title, string[] requestedSystems, bool is3D)
        {
            gameKey = string.IsNullOrWhiteSpace(key) ? "prototype" : key;
            gameName = string.IsNullOrWhiteSpace(title) ? "AI Prototype" : title;
            systems = requestedSystems ?? Array.Empty<string>();
            threeDimensional = is3D;
        }

        private void Awake()
        {
            CreatePlayer();
            CreatePlayableTargets();
        }

        private void Update()
        {
            if (player == null) return;
            elapsed += Time.deltaTime;
            var horizontal = KeyAxis(KeyCode.A, KeyCode.D, KeyCode.LeftArrow, KeyCode.RightArrow);
            var vertical = KeyAxis(KeyCode.S, KeyCode.W, KeyCode.DownArrow, KeyCode.UpArrow);
            if (gameKey.Contains("runner")) horizontal += 0.65f;
            var direction = threeDimensional ? new Vector3(horizontal, 0f, vertical) : new Vector3(horizontal, vertical, 0f);
            if (direction.sqrMagnitude > 1f) direction.Normalize();
            player.transform.position += direction * moveSpeed * Time.deltaTime;
            if (Input.GetKeyDown(KeyCode.Space) || Input.GetMouseButtonDown(0)) TriggerPrimaryAction();
            CollectNearby();
        }

        private static float KeyAxis(KeyCode negative, KeyCode positive, KeyCode negativeAlt, KeyCode positiveAlt)
        {
            var value = 0f;
            if (Input.GetKey(negative) || Input.GetKey(negativeAlt)) value -= 1f;
            if (Input.GetKey(positive) || Input.GetKey(positiveAlt)) value += 1f;
            return value;
        }

        private void CreatePlayer()
        {
            if (player != null) return;
            player = GameObject.CreatePrimitive(threeDimensional ? PrimitiveType.Capsule : PrimitiveType.Sphere);
            player.name = "Generated Player";
            player.transform.position = threeDimensional ? new Vector3(0f, 1f, -4f) : new Vector3(0f, -3f, 0f);
            player.transform.localScale = threeDimensional ? Vector3.one : new Vector3(0.8f, 0.8f, 0.25f);
            Tint(player, new Color(0.16f, 0.72f, 1f));
        }

        private void CreatePlayableTargets()
        {
            for (var index = 0; index < 8; index++)
            {
                var target = GameObject.CreatePrimitive(index % 2 == 0 ? PrimitiveType.Sphere : PrimitiveType.Cube);
                target.name = "Prototype Target " + (index + 1);
                var angle = index / 8f * Mathf.PI * 2f;
                target.transform.position = threeDimensional
                    ? new Vector3(Mathf.Cos(angle) * 6f, 0.7f, Mathf.Sin(angle) * 6f)
                    : new Vector3(Mathf.Cos(angle) * 6f, Mathf.Sin(angle) * 3.4f, 0f);
                target.transform.localScale = Vector3.one * (index % 3 == 0 ? 1.25f : 0.75f);
                Tint(target, Color.HSVToRGB(index / 8f, 0.72f, 1f));
                pickups.Add(target);
            }
        }

        private void CollectNearby()
        {
            for (var index = pickups.Count - 1; index >= 0; index--)
            {
                var target = pickups[index];
                if (target == null) { pickups.RemoveAt(index); continue; }
                if (Vector3.Distance(player.transform.position, target.transform.position) > 1.15f) continue;
                Destroy(target);
                pickups.RemoveAt(index);
                score += 100;
                eventMessage = "Collected: score +100";
            }
            if (pickups.Count == 0) eventMessage = "Prototype objective completed";
        }

        private void TriggerPrimaryAction()
        {
            var projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            projectile.name = "Prototype Projectile";
            projectile.transform.position = player.transform.position + (threeDimensional ? Vector3.forward : Vector3.up) * 1.1f;
            projectile.transform.localScale = Vector3.one * 0.32f;
            Tint(projectile, new Color(1f, 0.72f, 0.12f));
            var body = projectile.AddComponent<Rigidbody>();
            body.useGravity = false;
            body.linearVelocity = (threeDimensional ? Vector3.forward : Vector3.up) * 12f;
            Destroy(projectile, 2.5f);
            eventMessage = "Primary action triggered";
        }

        private void OnGUI()
        {
            var scale = Mathf.Max(1f, Screen.height / 720f);
            var title = new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt(24 * scale), fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            var text = new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt(15 * scale), normal = { textColor = new Color(0.76f, 0.91f, 1f) } };
            GUI.Box(new Rect(18 * scale, 18 * scale, 410 * scale, 126 * scale), string.Empty);
            GUI.Label(new Rect(34 * scale, 26 * scale, 370 * scale, 38 * scale), gameName, title);
            GUI.Label(new Rect(34 * scale, 64 * scale, 370 * scale, 24 * scale), $"{gameKey}  |  Score {score}  |  {elapsed:0.0}s", text);
            GUI.Label(new Rect(34 * scale, 88 * scale, 370 * scale, 24 * scale), eventMessage, text);
            GUI.Label(new Rect(34 * scale, 111 * scale, 370 * scale, 24 * scale), "WASD / arrows: move   Space / tap: action", text);
        }

        private static void Tint(GameObject target, Color color)
        {
            var renderer = target.GetComponent<Renderer>();
            if (renderer == null) return;
            var shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard") ?? Shader.Find("Unlit/Color");
            renderer.material = new Material(shader) { color = color };
        }
    }
}

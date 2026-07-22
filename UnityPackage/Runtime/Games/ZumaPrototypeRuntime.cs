using System.Collections.Generic;
using UnityEngine;

namespace AIEngineer.Games
{
    internal sealed class ZumaGameManagerLegacy : MonoBehaviour
    {
        private readonly List<ZumaMarbleLegacy> marbles = new();
        private TextMesh scoreLabel;

        public static bool RuntimeReady { get; private set; }
        public int Score { get; private set; }

        private void Start()
        {
            RuntimeReady = true;
            UpdateScoreLabel();
            Debug.Log("AI Engineer Zuma prototype runtime ready.");
        }

        public void Configure(TextMesh label) => scoreLabel = label;

        public void Register(ZumaMarbleLegacy marble)
        {
            if (!marbles.Contains(marble))
                marbles.Add(marble);
        }

        public void ResolveHit(ZumaMarbleLegacy hit, Color projectileColor)
        {
            if (hit == null || !SameColor(hit.Color, projectileColor))
                return;

            var index = marbles.IndexOf(hit);
            var matching = new List<ZumaMarbleLegacy> { hit };
            CollectMatching(index - 1, -1, hit.Color, matching);
            CollectMatching(index + 1, 1, hit.Color, matching);
            if (matching.Count < 3)
                return;

            foreach (var marble in matching)
            {
                marbles.Remove(marble);
                Destroy(marble.gameObject);
            }

            Score += matching.Count * 10;
            UpdateScoreLabel();
            Debug.Log($"Zuma match resolved: {matching.Count} marbles, score {Score}.");
        }

        private void CollectMatching(int index, int direction, Color color, List<ZumaMarbleLegacy> matching)
        {
            while (index >= 0 && index < marbles.Count && SameColor(marbles[index].Color, color))
            {
                matching.Add(marbles[index]);
                index += direction;
            }
        }

        private void UpdateScoreLabel()
        {
            if (scoreLabel != null)
                scoreLabel.text = $"Score: {Score}\nClick or Space to fire";
        }

        private static bool SameColor(Color left, Color right) => Vector4.Distance(left, right) < 0.1f;
    }

    [RequireComponent(typeof(SphereCollider))]
    internal sealed class ZumaMarbleLegacy : MonoBehaviour
    {
        public Color Color { get; private set; }

        public void Configure(ZumaGameManagerLegacy gameManager, Color color)
        {
            Color = color;
            GetComponent<Renderer>().material.color = color;
            gameManager.Register(this);
        }
    }

    [RequireComponent(typeof(Rigidbody), typeof(SphereCollider))]
    internal sealed class ZumaProjectileLegacy : MonoBehaviour
    {
        private ZumaGameManagerLegacy gameManager;
        private Color color;

        public void Launch(ZumaGameManagerLegacy manager, Vector2 direction, Color projectileColor)
        {
            gameManager = manager;
            color = projectileColor;
            GetComponent<Renderer>().material.color = color;
            GetComponent<Rigidbody>().linearVelocity = direction.normalized * 11f;
            Destroy(gameObject, 4f);
        }

        private void OnCollisionEnter(Collision collision)
        {
            var marble = collision.gameObject.GetComponent<ZumaMarbleLegacy>();
            if (marble != null)
                gameManager.ResolveHit(marble, color);
            Destroy(gameObject);
        }
    }

    internal sealed class ZumaShooterLegacy : MonoBehaviour
    {
        [SerializeField] private ZumaGameManagerLegacy gameManager;
        private readonly Color[] colors = { Color.red, Color.yellow, Color.cyan, Color.magenta };
        private int nextColor;

        public void Configure(ZumaGameManagerLegacy manager) => gameManager = manager;

        private void Update()
        {
            var mouse = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            var direction = ((Vector2)mouse - (Vector2)transform.position).normalized;
            if (direction.sqrMagnitude > 0.01f)
                transform.up = direction;
            if (Input.GetMouseButtonDown(0) || Input.GetKeyDown(KeyCode.Space))
                Fire(direction);
        }

        public void Fire(Vector2 direction)
        {
            var projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            projectile.name = "ZumaProjectile";
            projectile.transform.position = transform.position + (Vector3)(direction * 0.75f);
            projectile.transform.localScale = Vector3.one * 0.38f;
            var body = projectile.AddComponent<Rigidbody>();
            body.useGravity = false;
            body.collisionDetectionMode = CollisionDetectionMode.Continuous;
            var shot = projectile.AddComponent<ZumaProjectileLegacy>();
            shot.Launch(gameManager, direction, colors[nextColor++ % colors.Length]);
        }
    }
}

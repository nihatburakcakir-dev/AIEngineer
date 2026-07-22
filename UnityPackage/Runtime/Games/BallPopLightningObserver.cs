using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace AIEngineer.Games
{
    /// <summary>
    /// Detects newly spawned colour-hit particle roots and adds a top-to-bottom
    /// lightning strike. This integrates with existing ball-chain projects
    /// without requiring a direct dependency on their Assembly-CSharp scripts.
    /// </summary>
    public sealed class BallPopLightningObserver : MonoBehaviour
    {
        [SerializeField] private GameObject lightningPrefab;
        [SerializeField] private float spawnHeight = 5.5f;
        [SerializeField] private float fallDuration = 0.18f;
        [SerializeField] private float effectLifetime = 2f;
        [SerializeField] private float pollInterval = 0.08f;

        private readonly HashSet<int> observedRoots = new();
        private float nextPoll;

        public void Configure(GameObject prefab)
        {
            lightningPrefab = prefab;
        }

        private void Awake()
        {
            RememberExistingHitEffects();
        }

        private void Update()
        {
            if (Time.unscaledTime < nextPoll) return;
            nextPoll = Time.unscaledTime + pollInterval;
            DetectNewHitEffects();
        }

        private void RememberExistingHitEffects()
        {
            foreach (var particle in FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
            {
                var root = particle.transform.root.gameObject;
                if (IsBallHitEffect(root.name)) observedRoots.Add(root.GetInstanceID());
            }
        }

        private void DetectNewHitEffects()
        {
            if (lightningPrefab == null) return;
            foreach (var particle in FindObjectsByType<ParticleSystem>(FindObjectsSortMode.None))
            {
                var root = particle.transform.root.gameObject;
                if (!IsBallHitEffect(root.name) || !observedRoots.Add(root.GetInstanceID())) continue;
                StartCoroutine(Strike(root.transform.position));
            }
        }

        private static bool IsBallHitEffect(string objectName)
        {
            var normalized = (objectName ?? string.Empty).ToLowerInvariant();
            return normalized.Contains("hit") && !normalized.Contains("lightning");
        }

        private IEnumerator Strike(Vector3 target)
        {
            var start = target + Vector3.up * spawnHeight;
            var effect = Instantiate(lightningPrefab, start, Quaternion.identity);
            effect.name = "AI Ball Pop Lightning";
            var elapsed = 0f;
            while (effect != null && elapsed < fallDuration)
            {
                elapsed += Time.deltaTime;
                effect.transform.position = Vector3.Lerp(start, target, Mathf.Clamp01(elapsed / fallDuration));
                yield return null;
            }
            if (effect != null)
            {
                effect.transform.position = target;
                Destroy(effect, effectLifetime);
            }
        }
    }
}

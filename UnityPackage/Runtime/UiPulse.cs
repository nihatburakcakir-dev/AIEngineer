using UnityEngine;

namespace AIEngineer.Runtime
{
    /// <summary>Small allocation-free alpha pulse for generated UI accents.</summary>
    [RequireComponent(typeof(CanvasGroup))]
    public sealed class UiPulse : MonoBehaviour
    {
        [Range(0f, 1f)] public float minAlpha = 0.45f;
        [Range(0f, 1f)] public float maxAlpha = 1f;
        [Min(0.01f)] public float frequency = 1.2f;
        private CanvasGroup canvasGroup;

        private void Awake() => canvasGroup = GetComponent<CanvasGroup>();

        private void Update()
        {
            var wave = (Mathf.Sin(Time.unscaledTime * frequency * Mathf.PI * 2f) + 1f) * 0.5f;
            canvasGroup.alpha = Mathf.Lerp(minAlpha, maxAlpha, wave);
        }
    }
}

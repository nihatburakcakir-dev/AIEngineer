using UnityEngine;

namespace AIEngineer.Games
{
    [RequireComponent(typeof(SphereCollider))]
    public sealed class ZumaMarble : MonoBehaviour
    {
        [SerializeField] private Color marbleColor;
        public Color Color => marbleColor;
        private void Awake() => FindFirstObjectByType<ZumaGameManager>()?.Register(this);
        public void Configure(ZumaGameManager gameManager, Color color) { marbleColor = color; gameManager.Register(this); }
    }
}

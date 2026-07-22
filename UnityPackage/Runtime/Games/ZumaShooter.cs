using UnityEngine;
using UnityEngine.EventSystems;

namespace AIEngineer.Games
{
    public sealed class ZumaShooter : MonoBehaviour
    {
        [SerializeField] private ZumaGameManager gameManager;
        private readonly Color[] colors = { Color.red, Color.yellow, Color.cyan, Color.magenta };
        private int nextColor;
        private Camera gameCamera;
        public void Configure(ZumaGameManager manager) => gameManager = manager;
        private void Start() => gameCamera = Camera.main;
        private void Update()
        {
            var pointer = (Vector2)Input.mousePosition;
            var fire = Input.GetMouseButtonDown(0) || Input.GetKeyDown(KeyCode.Space);
            if (Input.touchCount > 0)
            {
                var touch = Input.GetTouch(0);
                pointer = touch.position;
                fire = touch.phase == TouchPhase.Ended;
            }

            var world = (Vector2)(gameCamera ?? Camera.main).ScreenToWorldPoint(pointer);
            var direction = (world - (Vector2)transform.position).normalized;
            if (direction.sqrMagnitude > 0.01f) transform.up = direction;
            var overUi = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
            if (fire && !overUi && direction.y > -0.2f) Fire(direction);
        }

        /// <summary>Called by the large mobile HUD button when one-handed play is preferred.</summary>
        public void FireForward() => Fire(transform.up);
        public void Fire(Vector2 direction)
        {
            var projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            projectile.name = "ZumaProjectile";
            projectile.transform.position = transform.position + (Vector3)(direction * 0.75f);
            projectile.transform.localScale = Vector3.one * 0.38f;
            var body = projectile.AddComponent<Rigidbody>();
            body.useGravity = false;
            body.collisionDetectionMode = CollisionDetectionMode.Continuous;
            projectile.AddComponent<ZumaProjectile>().Launch(gameManager, direction, colors[nextColor++ % colors.Length]);
        }
    }
}

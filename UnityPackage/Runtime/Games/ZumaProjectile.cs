using UnityEngine;

namespace AIEngineer.Games
{
    [RequireComponent(typeof(Rigidbody), typeof(SphereCollider))]
    public sealed class ZumaProjectile : MonoBehaviour
    {
        private ZumaGameManager gameManager;
        private Color color;
        public void Launch(ZumaGameManager manager, Vector2 direction, Color projectileColor)
        {
            gameManager = manager; color = projectileColor;
            GetComponent<Renderer>().material.color = color;
            GetComponent<Rigidbody>().linearVelocity = direction.normalized * 11f;
            Destroy(gameObject, 4f);
        }
        private void OnCollisionEnter(Collision collision)
        {
            var marble = collision.gameObject.GetComponent<ZumaMarble>();
            if (marble != null) gameManager.ResolveHit(marble, color);
            Destroy(gameObject);
        }
    }
}

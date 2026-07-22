using UnityEngine;

namespace AIEngineer.Characters
{
    [RequireComponent(typeof(Rigidbody2D))]
    public sealed class GeneratedCharacterController2D : MonoBehaviour
    {
        [SerializeField] private float speed = 5f;
        private Rigidbody2D body;
        private Vector2 input;

        private void Awake()
        {
            body = GetComponent<Rigidbody2D>();
        }

        private void Update()
        {
            input = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical")).normalized;
        }

        private void FixedUpdate()
        {
            body.linearVelocity = input * speed;
        }
    }
}

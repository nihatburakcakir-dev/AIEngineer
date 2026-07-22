using UnityEngine;

namespace AIEngineer.Characters
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class GeneratedCharacterController3D : MonoBehaviour
    {
        [SerializeField] private float speed = 5f;
        private Rigidbody body;
        private Vector3 input;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
        }

        private void Update()
        {
            input = new Vector3(Input.GetAxisRaw("Horizontal"), 0f, Input.GetAxisRaw("Vertical")).normalized;
        }

        private void FixedUpdate()
        {
            body.MovePosition(body.position + input * speed * Time.fixedDeltaTime);
        }
    }
}

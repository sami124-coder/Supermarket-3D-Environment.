using UnityEngine;

namespace Sipo
{
    /// <summary>Slow local animation for the suspended solar-system sculptures.</summary>
    [DisallowMultipleComponent]
    public sealed class SipoAmbientMotion : MonoBehaviour
    {
        public Vector3 rotationAxis = Vector3.up;
        public float rotationDegreesPerSecond = 4;
        [Min(0)] public float bobHeight = 0.06f;
        [Min(0)] public float bobSpeed = 0.7f;
        private Vector3 restPosition;
        private Quaternion restRotation;
        private float startTime;
        private float phase;

        private void OnEnable()
        {
            restPosition = transform.localPosition;
            restRotation = transform.localRotation;
            startTime = Time.time;
            phase = Mathf.Abs(transform.GetSiblingIndex() * 1.618f) % (Mathf.PI * 2);
        }

        private void Update()
        {
            float elapsed = Time.time - startTime;
            transform.localPosition = restPosition + Vector3.up * (Mathf.Sin(elapsed * bobSpeed + phase) - Mathf.Sin(phase)) * bobHeight;
            if (rotationAxis.sqrMagnitude > 0.001f)
                transform.localRotation = restRotation * Quaternion.AngleAxis(elapsed * rotationDegreesPerSecond, rotationAxis.normalized);
        }

        private void OnDisable()
        {
            transform.localPosition = restPosition;
            transform.localRotation = restRotation;
        }
    }
}

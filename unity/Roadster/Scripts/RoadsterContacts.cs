#nullable enable
using UnityEngine;

namespace Roadster
{
    // Logs what the Roadster's body runs into: the other collider, the impact speed and where on the car it touched,
    // so a stop that "feels like a wall" can be read from Player.log. RoadsterDrive adds it to the driven Roadster's
    // rigidbody object. At most one line every half second, and only for impacts above 0.5 m/s.
    internal sealed class RoadsterContacts : MonoBehaviour
    {
        private const float MinImpact = 0.5f; // m/s
        private const float Interval = 0.5f; // s
        private float nextLog;

        private void OnCollisionEnter(Collision collision) => Report("hit", collision);

        private void OnCollisionStay(Collision collision)
        {
            // A body resting on the road stays in contact without a new enter; log it too, slower.
            if (collision.collider != null && collision.contactCount > 0) Report("touching", collision);
        }

        private void Report(string kind, Collision collision)
        {
            if (Time.time < nextLog) return;
            var impact = collision.relativeVelocity.magnitude;
            if (kind == "hit" && impact < MinImpact) return;
            nextLog = Time.time + (kind == "hit" ? Interval : 5f);
            var point = collision.contactCount > 0 ? transform.InverseTransformPoint(collision.GetContact(0).point) : Vector3.zero;
            // Which of the car's own colliders touched: the body hull, or a wheel's collider (NWH adds its own).
            var ours = collision.contactCount > 0 ? collision.GetContact(0).thisCollider : null;
            var other = collision.collider;
            var body = GetComponent<Rigidbody>();
            var speed = body == null ? 0f : body.velocity.magnitude * 2.23694f;
            Log.Info($"Contact ({kind}) with the car's {(ours != null ? ours.name : "?")}: {Path(other != null ? other.transform : null)} (layer {(other != null ? LayerMask.LayerToName(other.gameObject.layer) : "?")}), " +
                     $"impact {impact:F1} m/s at {speed:F0} mph, on the car at x {point.x:F2}, y {point.y:F2}, z {point.z:F2} m.");
        }

        private static string Path(Transform? t)
        {
            if (t == null) return "?";
            var path = t.name;
            for (var p = t.parent; p != null && path.Length < 120; p = p.parent) path = p.name + "/" + path;
            return path;
        }
    }
}

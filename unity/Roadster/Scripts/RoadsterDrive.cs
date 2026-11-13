#nullable enable
using System;
using System.Linq;
using Helpers;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Roadster
{
    internal sealed class RoadsterDrive : MonoBehaviour
    {
        private const float SixtyMph = 26.8224f;
        private const float MotorSeconds = 1.6f;
        private const float NitrogenSeconds = 0.6f;
        private const Key ModeKey = Key.N;
        private bool nitrogen;
        private float LaunchSeconds => nitrogen ? NitrogenSeconds : MotorSeconds;
        private float LaunchAcceleration => SixtyMph / LaunchSeconds;
        private const float LaunchGain = 4f;
        // The launch is for a straight run. A launch started at full steering lock pushed the car on while it turned,
        // and the catch-up term pushed harder still as it scrubbed speed (Player.log, 17 October 2026). It now starts
        // only with the wheels near straight, ends when the steering goes past LaunchSteerLimit, and its push never
        // exceeds LaunchMaxPush times the line's acceleration.
        private const float LaunchStartSteer = 0.3f;
        private const float LaunchSteerLimit = 0.6f;
        private const float LaunchMaxPush = 1.3f;
        private const float LaunchStartSpeed = 0.5f; // m/s; a launch starts from a standstill only
        private const float LaunchMaxSeconds = 1.5f;
        // The game's keyboard throttle settles at 0.77 to 0.85 in NWH's input (Player.log, 17 October 2026), so a
        // launch starts above StartThrottle and only ends when the throttle is mostly released.
        private const float StartThrottle = 0.7f;
        private const float HoldThrottle = 0.4f;

        private const float FanDownforce = 2f;
        private const float FanRamp = 0.3f;

        // Barrel roll (Backslash), as the reveal rolled over the Tesla lineup, in one motion (Peter, 17 October 2026): the
        // down thrusters lift the car over ThrustTime while it already starts to roll, it rolls once about its own
        // length on the way up and over the top, then the thrusters hold it level and brake the fall to 3 m/s over the
        // last 6 m. The roll goes the way the steering points (right when straight). Its rate starts at its fastest and
        // eases to nothing at RollEnd (rate ~ 1 - x squared), so it leaves the ground already turning and settles level.
        // Keep J free for HART. Self Driving; ignore stopped/creeping starts (issue #2).
        private const Key RollKey = Key.Backslash;
        private const float RollMinSpeed = 2f;
        private const float JumpHeight = 6f;
        private const float ThrustTime = 0.35f;
        private const float JumpCooldown = 2f;
        private const float RollEnd = 1.4f;
        private const float AttitudeGain = 60f;
        private const float AttitudeDamping = 15f;
        // Braking the fall from 6 m to 3 m/s kept the car 3.5 s in the air ("the fall back to the road is a bit too
        // slow", Peter, 17 October 2026): the thrusters now only catch it over the last 2.5 m, down to 5 m/s.
        private const float LandingSpeed = 5f;
        private const float LandingBrakeHeight = 2.5f;
        private const float MaxThrust = 40f;
        private const float LevelGain = 12f;
        private const float LevelDamping = 4f;
        private const float MinAirTime = 0.3f;

        private CarController? car;
        private Rigidbody? body;

        private bool launching;
        private float launchStart;
        private float lastSpeed;
        private float lastPush;

        private bool jumpRequested;
        private float jumpSteer;
        private bool airborne;
        private float jumpStart;
        private float nextJump;
        private float jumpBase;
        private float jumpPeak;
        private Quaternion rollBase;
        private float rollSign;
        private float rolled;
        private float lastLanding = -10f;

        private const float TelemetrySpeed = 4.5f;
        private const float TelemetrySteer = 0.2f;
        private float nextTelemetry;
        private Vector3 lastVelocity;
        private CarController? described;

        private const float PlumeLength = 1.6f;
        private CarController? plumesOf;
        private MeshRenderer[] rearPlumes = Array.Empty<MeshRenderer>();
        private MeshRenderer[] downPlumes = Array.Empty<MeshRenderer>();
        private float rearThrust;
        private float downThrust;

        private bool lookupFailed;
        private readonly RaycastHit[] hits = new RaycastHit[8];

        private void Update()
        {
            car = CurrentRoadster();
            body = car == null ? null : car.vehicleController.vehicleRigidbody;
            if (car == null || body == null || body.isKinematic)
            {
                launching = airborne = jumpRequested = false;
                Drive(rearPlumes, 0f);
                Drive(downPlumes, 0f);
                return;
            }
            if (body.GetComponent<RoadsterContacts>() == null) body.gameObject.AddComponent<RoadsterContacts>();
            ShowPlumes();
            if (GameManager.ShouldBlockKeyboardShortcuts() || CityMap.IsOpen) return;
            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard[ModeKey].wasPressedThisFrame) SwitchLaunchMode();
            if (keyboard != null && keyboard[RollKey].wasPressedThisFrame && !airborne && Time.time >= nextJump
                && body.velocity.magnitude > RollMinSpeed && GroundedWheels() >= 2)
            {
                jumpRequested = true;
                jumpSteer = car.vehicleController.input.Steering;
            }
        }

        private void FixedUpdate()
        {
            if (car == null || body == null || body.isKinematic) return;
            rearThrust = downThrust = 0f;
            Launch();
            BarrelRoll();
            Fans();
            Telemetry();
        }

        private void Launch()
        {
            var vehicle = car!.vehicleController;
            var speed = vehicle.SpeedSigned;
            var throttle = vehicle.input.Throttle;
            var now = Time.fixedTime;
            var dt = Time.fixedDeltaTime;

            if (!launching)
            {
                if (throttle < StartThrottle || Mathf.Abs(speed) > LaunchStartSpeed || airborne || GroundedWheels() < 4
                    || Mathf.Abs(vehicle.input.Steering) > LaunchStartSteer) return;
                launching = true;
                launchStart = now;
                lastSpeed = speed;
                lastPush = 0f;
                Log.Info($"Launch started ({(nitrogen ? "nitrogen" : "motors")}, target 0-60 mph in {LaunchSeconds:F1} s).");
            }

            var t = now - launchStart;
            if (speed >= SixtyMph)
            {
                var measured = (speed - lastSpeed) / dt;
                var crossed = measured > 0f ? t - (speed - SixtyMph) / measured : t;
                Log.Info($"Launch ({(nitrogen ? "nitrogen" : "motors")}): 0-60 mph in {crossed:F2} s (target {LaunchSeconds:F2} s).");
                launching = false;
                return;
            }
            var steering = vehicle.input.Steering;
            if (throttle < HoldThrottle || GroundedWheels() < 2 || t > LaunchMaxSeconds || Mathf.Abs(steering) > LaunchSteerLimit)
            {
                Log.Info($"Launch ended at {speed * 2.23694f:F0} mph after {t:F2} s (throttle {throttle:F2}, steering {steering:F2}, wheels down {GroundedWheels()}).");
                launching = false;
                return;
            }

            var wheels = t > 0f ? Mathf.Max(0f, (speed - lastSpeed) / dt - lastPush) : 0f;
            var target = LaunchAcceleration * t;
            var push = Mathf.Clamp(LaunchAcceleration - wheels + LaunchGain * (target - speed), 0f, LaunchMaxPush * LaunchAcceleration);
            var forward = Vector3.ProjectOnPlane(body!.transform.forward, Vector3.up).normalized;
            body.AddForce(forward * push, ForceMode.Acceleration);
            if (nitrogen) rearThrust = Mathf.Clamp01(push / SixtyMph * NitrogenSeconds);
            lastSpeed = speed;
            lastPush = push;
        }

        private void Fans()
        {
            if (airborne || GroundedWheels() < 3) return;
            var ramp = Mathf.Clamp01((Time.fixedTime - lastLanding) / FanRamp);
            body!.AddForce(-body.transform.up * (FanDownforce * -Physics.gravity.y * ramp), ForceMode.Acceleration);
        }

        private void BarrelRoll()
        {
            var b = body!;
            var now = Time.fixedTime;
            var gravity = -Physics.gravity.y;

            if (jumpRequested)
            {
                jumpRequested = false;
                launching = false;
                airborne = true;
                jumpStart = now;
                jumpBase = jumpPeak = b.position.y;
                nextJump = Time.time + JumpCooldown;
                var heading = Vector3.ProjectOnPlane(b.transform.forward, Vector3.up);
                rollBase = Quaternion.LookRotation(heading.sqrMagnitude > 1e-4f ? heading.normalized : Vector3.forward, Vector3.up);
                rollSign = jumpSteer < -0.2f ? 1f : -1f;
                rolled = 0f;
                b.maxAngularVelocity = Mathf.Max(b.maxAngularVelocity, 20f);
                Log.Info($"Barrel roll to the {(rollSign < 0f ? "right" : "left")} at {b.velocity.magnitude * 2.23694f:F0} mph.");
                return;
            }
            if (!airborne) return;

            jumpPeak = Mathf.Max(jumpPeak, b.position.y);
            var vy = b.velocity.y;
            var t = now - jumpStart;
            if (t > MinAirTime && GroundedWheels() >= 3)
            {
                airborne = false;
                lastLanding = now;
                var tilt = Vector3.Angle(b.transform.up, Vector3.up);
                Log.Info($"Barrel roll landed: peak {jumpPeak - jumpBase:F1} m, rolled {rolled:F0} degrees, touchdown {-vy:F1} m/s, " +
                         $"{tilt:F0} degrees off level, {t:F2} s in the air.");
                return;
            }

            if (t < ThrustTime)
            {
                var climb = gravity * (Mathf.Sqrt(ThrustTime * ThrustTime / 4f + 2f * JumpHeight / gravity) - ThrustTime / 2f);
                var lift = Mathf.Max(0f, (climb - vy) / Mathf.Max(ThrustTime - t, Time.fixedDeltaTime)) + gravity;
                b.AddForce(Vector3.up * Mathf.Min(lift, 3f * MaxThrust), ForceMode.Acceleration);
                downThrust = 1f;
            }

            if (t <= RollEnd)
            {
                var x = Mathf.Clamp01(t / RollEnd);
                var angle = 360f * (1.5f * x - 0.5f * x * x * x) * rollSign;
                rolled = Mathf.Max(rolled, Mathf.Abs(angle));
                var rate = 360f * 1.5f * (1f - x * x) / RollEnd * rollSign * Mathf.Deg2Rad;
                var target = rollBase * Quaternion.AngleAxis(angle, Vector3.forward);
                var error = target * Quaternion.Inverse(b.rotation);
                error.ToAngleAxis(out var errorAngle, out var errorAxis);
                if (errorAngle > 180f) errorAngle -= 360f;
                if (float.IsNaN(errorAxis.x)) errorAxis = Vector3.zero;
                var targetRate = (rollBase * Vector3.forward) * rate;
                b.AddTorque(errorAxis * (errorAngle * Mathf.Deg2Rad * AttitudeGain) + (targetRate - b.angularVelocity) * AttitudeDamping,
                    ForceMode.Acceleration);
            }
            else
            {
                var tilt = Vector3.Cross(b.transform.up, Vector3.up);
                var tumble = Vector3.ProjectOnPlane(b.angularVelocity, Vector3.up);
                b.AddTorque(tilt * LevelGain - tumble * LevelDamping, ForceMode.Acceleration);
            }

            if (vy < -LandingSpeed && GroundDistance(b) < LandingBrakeHeight)
            {
                var thrust = Mathf.Clamp((-LandingSpeed - vy) / Time.fixedDeltaTime + gravity, 0f, MaxThrust);
                b.AddForce(Vector3.up * thrust, ForceMode.Acceleration);
                downThrust = Mathf.Max(downThrust, thrust / MaxThrust);
            }
        }

        private void SwitchLaunchMode()
        {
            nitrogen = !nitrogen;
            Log.Info($"Launch mode: {(nitrogen ? "nitrogen" : "motors")}.");
            try
            {
                UI.Notification.Notifications.Show(UI.Notification.NotificationType.Info,
                    nitrogen ? "roadster:notification_nitrogen_open" : "roadster:notification_nitrogen_closed",
                    null, 4f, "roadster-launch-mode", null, notificationSound: true, trackOnSaveGame: false);
            }
            catch (Exception ex) { Log.Error("Launch mode notice: " + ex); }
        }

        private void ShowPlumes()
        {
            if (plumesOf != car)
            {
                plumesOf = car;
                var all = car!.GetComponentsInChildren<MeshRenderer>(true);
                rearPlumes = all.Where(r => r.name.StartsWith("Plume_Rear", StringComparison.Ordinal)).ToArray();
                downPlumes = all.Where(r => r.name.StartsWith("Plume_Down", StringComparison.Ordinal)).ToArray();
                Log.Info($"Plumes found: {rearPlumes.Length} rear, {downPlumes.Length} down.");
            }
            Drive(rearPlumes, rearThrust);
            Drive(downPlumes, downThrust);
        }

        private static void Drive(MeshRenderer[] plumes, float thrust)
        {
            foreach (var plume in plumes)
            {
                if (plume == null) continue;
                var on = thrust > 0.03f;
                if (plume.enabled != on) plume.enabled = on;
                if (!on) continue;
                var flicker = UnityEngine.Random.Range(0.85f, 1.15f);
                var width = Mathf.Lerp(0.2f, 0.4f, thrust) * flicker;
                plume.transform.localScale = new Vector3(width, width, PlumeLength * Mathf.Lerp(0.35f, 1f, thrust) * flicker);
            }
        }

        private void Telemetry()
        {
            var b = body!;
            var vehicle = car!.vehicleController;
            var lateral = Vector3.Dot((b.velocity - lastVelocity) / Time.fixedDeltaTime, b.transform.right) / 9.81f;
            lastVelocity = b.velocity;
            if (described != car)
            {
                described = car;
                var setup = string.Join("; ", vehicle.powertrain.wheels.Select(w =>
                    $"{w.name}: radius {w.wheelUAPI.Radius:F3}, spring {w.wheelUAPI.SpringMaxForce:F0} N over {w.wheelUAPI.SpringMaxLength:F2} m, " +
                    $"dampers {w.wheelUAPI.DamperBumpRate:F0}/{w.wheelUAPI.DamperReboundRate:F0}, max load {w.wheelUAPI.MaxLoad:F0} N, " +
                    $"grip {w.wheelUAPI.LongitudinalFrictionGrip:F2}/{w.wheelUAPI.LateralFrictionGrip:F2}"));
                Log.Info($"Setup: mass {b.mass:F0} kg, centre of mass {b.centerOfMass}, {setup}.");
            }
            var speed = vehicle.Speed;
            var steer = vehicle.input.Steering;
            if (speed < TelemetrySpeed || Mathf.Abs(steer) < TelemetrySteer || Time.time < nextTelemetry) return;
            nextTelemetry = Time.time + 0.5f;
            var wheels = string.Join("; ", vehicle.powertrain.wheels.Select(w =>
            {
                var u = w.wheelUAPI;
                var hit = u.IsGrounded && u.HitCollider != null ? u.HitCollider.name : "-";
                return $"{w.name.Replace("Wheel", "").Replace("_WheelController", "")} {(u.IsGrounded ? "down" : "UP")} load {u.Load:F0} N " +
                       $"compressed {u.SpringCompression * 100f:F0}% slip {u.NormalizedLongitudinalSlip:F2}/{u.NormalizedLateralSlip:F2} on {hit}";
            }));
            Log.Info($"Corner: {speed * 2.23694f:F0} mph, steer {steer:F2}, lateral {lateral:F2} g, throttle {vehicle.input.Throttle:F2}, brakes {vehicle.input.Brakes:F2}; {wheels}.");
        }

        private float GroundDistance(Rigidbody b)
        {
            var count = Physics.RaycastNonAlloc(b.worldCenterOfMass, Vector3.down, hits, 50f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            var nearest = float.PositiveInfinity;
            for (var i = 0; i < count; i++)
            {
                if (hits[i].rigidbody == b) continue;
                nearest = Mathf.Min(nearest, hits[i].distance);
            }
            return nearest;
        }

        private int GroundedWheels()
        {
            var count = 0;
            foreach (var wheel in car!.vehicleController.powertrain.wheels)
                if (wheel.wheelUAPI != null && wheel.wheelUAPI.IsGrounded) count++;
            return count;
        }

        private CarController? CurrentRoadster()
        {
            try
            {
                if (SaveGameManager.Current == null) return null;
                var current = VehicleHelper.GetCurrentVehicleBase() as CarController;
                if (current == null || !current.controlledByPlayer || current.vehicleType == null) return null;
                return current.vehicleType.vehicleTypeName == RoadsterMod.TypeName ? current : null;
            }
            catch (Exception ex)
            {
                if (!lookupFailed) Log.Error("Looking up the current vehicle failed: " + ex);
                lookupFailed = true;
                return null;
            }
        }
    }
}

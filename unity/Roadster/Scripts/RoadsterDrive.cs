#nullable enable
using System;
using System.Linq;
using Helpers;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Roadster
{
    // The Roadster's fans and thrusters while the player drives one: the launch to 60 mph, the fans' suction, and the
    // barrel roll on J. One instance for the whole game; it does nothing in any other vehicle.
    internal sealed class RoadsterDrive : MonoBehaviour
    {
        // Launch: Tesla's 0-60 mph in 0.81 s from the 15 October 2026 reveal, about 3.4 g. Tyres grip about 1 g, so
        // the thrusters supply the rest, as Tesla says they do on the real car. The push follows a straight speed
        // line from the moment the throttle goes down, minus whatever the wheels already add.
        private const float SixtyMph = 26.8224f; // m/s
        private const float LaunchSeconds = 0.81f;
        private const float LaunchAcceleration = SixtyMph / LaunchSeconds; // 33.1 m/s²
        private const float LaunchGain = 8f; // 1/s, pulls the speed back onto the line
        private const float LaunchStartSpeed = 0.5f; // m/s; a launch starts from a standstill only
        private const float LaunchMaxSeconds = 1.5f;
        // The game's keyboard throttle settles at 0.77 to 0.85 in NWH's input (Player.log, 17 October 2026), so a
        // launch starts above StartThrottle and only ends when the throttle is mostly released.
        private const float StartThrottle = 0.7f;
        private const float HoldThrottle = 0.4f;

        // Fans: the reveal claims up to 2 g of downforce at a standstill. While three or more wheels are on the road the
        // fans pull the car down with an extra 1 g along its own down axis, so it grips in corners at any speed; the
        // springs are sized for it (RoadsterModel). Off in the air, and faded back in over FanRamp after a landing.
        private const float FanDownforce = 1f; // in g
        private const float FanRamp = 0.3f; // s

        // Barrel roll (J), as the reveal rolled over the Tesla lineup: thrusters fire the car 6 m up, roll it once
        // about its own length while it climbs and falls, then hold it level and brake the fall to 3 m/s over the
        // last 6 m. The roll goes the way the steering points (right when straight). An attitude controller follows a
        // smooth 0 to 360 degree roll over RollStart to RollEnd after take-off, while the car is still well clear.
        private const Key RollKey = Key.J;
        private const float JumpHeight = 6f; // m
        private const float JumpCooldown = 2f; // s
        private const float RollStart = 0.12f; // s after take-off
        private const float RollEnd = 1.35f; // s; about 5.8 m up on the way down
        private const float AttitudeGain = 60f; // 1/s²
        private const float AttitudeDamping = 15f; // 1/s, near critical for the gain
        private const float LandingSpeed = 3f; // m/s
        private const float LandingBrakeHeight = 6f; // m
        private const float MaxThrust = 40f; // m/s², about 4 g
        private const float LevelGain = 12f; // 1/s²
        private const float LevelDamping = 4f; // 1/s
        private const float MinAirTime = 0.3f; // s before a touchdown counts

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
        private float rolled; // degrees reached, for the log
        private float lastLanding = -10f;

        // Cornering telemetry: one line every half second while turning at speed, for tuning from Player.log.
        private const float TelemetrySpeed = 4.5f; // m/s, about 10 mph
        private const float TelemetrySteer = 0.2f;
        private float nextTelemetry;
        private Vector3 lastVelocity;
        private CarController? described;

        private bool lookupFailed;
        private readonly RaycastHit[] hits = new RaycastHit[8];

        private void Update()
        {
            car = CurrentRoadster();
            body = car == null ? null : car.vehicleController.vehicleRigidbody;
            if (car == null || body == null || body.isKinematic)
            {
                launching = airborne = jumpRequested = false;
                return;
            }
            if (body.GetComponent<RoadsterContacts>() == null) body.gameObject.AddComponent<RoadsterContacts>();
            if (GameManager.ShouldBlockKeyboardShortcuts() || CityMap.IsOpen) return;
            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard[RollKey].wasPressedThisFrame && !airborne && Time.time >= nextJump && GroundedWheels() >= 2)
            {
                jumpRequested = true;
                jumpSteer = car.vehicleController.input.Steering;
            }
        }

        private void FixedUpdate()
        {
            if (car == null || body == null || body.isKinematic) return;
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
                if (throttle < StartThrottle || Mathf.Abs(speed) > LaunchStartSpeed || airborne || GroundedWheels() < 4) return;
                launching = true;
                launchStart = now;
                lastSpeed = speed;
                lastPush = 0f;
                Log.Info("Launch started.");
            }

            var t = now - launchStart;
            if (speed >= SixtyMph)
            {
                // The crossing falls between two physics steps; interpolate back from this one.
                var measured = (speed - lastSpeed) / dt;
                var crossed = measured > 0f ? t - (speed - SixtyMph) / measured : t;
                Log.Info($"Launch: 0-60 mph in {crossed:F2} s (target {LaunchSeconds:F2} s).");
                launching = false;
                return;
            }
            if (throttle < HoldThrottle || GroundedWheels() < 2 || t > LaunchMaxSeconds)
            {
                Log.Info($"Launch ended at {speed * 2.23694f:F0} mph after {t:F2} s (throttle {throttle:F2}, wheels down {GroundedWheels()}).");
                launching = false;
                return;
            }

            // What the wheels added over the last step, without our own push.
            var wheels = t > 0f ? Mathf.Max(0f, (speed - lastSpeed) / dt - lastPush) : 0f;
            var target = LaunchAcceleration * t;
            var push = Mathf.Clamp(LaunchAcceleration - wheels + LaunchGain * (target - speed), 0f, 2f * LaunchAcceleration);
            var forward = Vector3.ProjectOnPlane(body!.transform.forward, Vector3.up).normalized;
            body.AddForce(forward * push, ForceMode.Acceleration);
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
                var up = Mathf.Sqrt(2f * gravity * JumpHeight);
                b.AddForce(Vector3.up * Mathf.Max(0f, up - b.velocity.y), ForceMode.VelocityChange);
                airborne = true;
                jumpStart = now;
                jumpBase = jumpPeak = b.position.y;
                nextJump = Time.time + JumpCooldown;
                var heading = Vector3.ProjectOnPlane(b.transform.forward, Vector3.up);
                rollBase = Quaternion.LookRotation(heading.sqrMagnitude > 1e-4f ? heading.normalized : Vector3.forward, Vector3.up);
                // Positive roll about the car's forward axis lifts its right side in Unity's left-handed frame, so a roll
                // to the right is the negative direction.
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

            if (t <= RollEnd)
            {
                // Follow the roll: target orientation and rate from a smooth 0 to 360 degree profile.
                var s = Mathf.Clamp01((t - RollStart) / (RollEnd - RollStart));
                var eased = s * s * (3f - 2f * s);
                var angle = 360f * eased * rollSign;
                rolled = Mathf.Max(rolled, Mathf.Abs(angle));
                var rate = 360f * 6f * s * (1f - s) / (RollEnd - RollStart) * rollSign * Mathf.Deg2Rad;
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
                // Level: turn the car's up towards the world's up, and damp the tumble but not the yaw.
                var tilt = Vector3.Cross(b.transform.up, Vector3.up);
                var tumble = Vector3.ProjectOnPlane(b.angularVelocity, Vector3.up);
                b.AddTorque(tilt * LevelGain - tumble * LevelDamping, ForceMode.Acceleration);
            }

            // Landing: hold the fall at LandingSpeed near the ground.
            if (vy < -LandingSpeed && GroundDistance(b) < LandingBrakeHeight)
            {
                var thrust = Mathf.Clamp((-LandingSpeed - vy) / Time.fixedDeltaTime + gravity, 0f, MaxThrust);
                b.AddForce(Vector3.up * thrust, ForceMode.Acceleration);
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

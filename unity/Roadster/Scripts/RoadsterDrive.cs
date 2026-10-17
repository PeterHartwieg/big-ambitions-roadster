#nullable enable
using System;
using Helpers;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Roadster
{
    // The Roadster's thrusters while the player drives one: the launch to 60 mph and the hop. One instance for the
    // whole game; it does nothing in any other vehicle.
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

        // Hop: straight up 5 m, enough to clear a box truck, as the reveal hopped the Tesla lineup. In the air the
        // thrusters hold the car level and brake the fall to 3 m/s over the last 6 m.
        private const Key HopKey = Key.J;
        private const float HopHeight = 5f; // m
        private const float HopCooldown = 1.5f; // s
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

        private bool hopRequested;
        private bool airborne;
        private float hopStart;
        private float nextHop;
        private float hopBase;
        private float hopPeak;

        private bool lookupFailed;
        private readonly RaycastHit[] hits = new RaycastHit[8];

        private void Update()
        {
            car = CurrentRoadster();
            body = car == null ? null : car.vehicleController.vehicleRigidbody;
            if (car == null || body == null || body.isKinematic)
            {
                launching = airborne = hopRequested = false;
                return;
            }
            if (GameManager.ShouldBlockKeyboardShortcuts() || CityMap.IsOpen) return;
            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard[HopKey].wasPressedThisFrame && !airborne && Time.time >= nextHop && GroundedWheels() >= 2)
                hopRequested = true;
        }

        private void FixedUpdate()
        {
            if (car == null || body == null || body.isKinematic) return;
            Launch();
            Hop();
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

        private void Hop()
        {
            var b = body!;
            var now = Time.fixedTime;
            var gravity = -Physics.gravity.y;

            if (hopRequested)
            {
                hopRequested = false;
                launching = false;
                var up = Mathf.Sqrt(2f * gravity * HopHeight);
                b.AddForce(Vector3.up * Mathf.Max(0f, up - b.velocity.y), ForceMode.VelocityChange);
                airborne = true;
                hopStart = now;
                hopBase = hopPeak = b.position.y;
                nextHop = Time.time + HopCooldown;
                Log.Info($"Hop at {b.velocity.magnitude * 2.23694f:F0} mph.");
                return;
            }
            if (!airborne) return;

            hopPeak = Mathf.Max(hopPeak, b.position.y);
            var vy = b.velocity.y;
            if (now - hopStart > MinAirTime && GroundedWheels() >= 3)
            {
                airborne = false;
                Log.Info($"Hop landed: peak {hopPeak - hopBase:F1} m, touchdown {-vy:F1} m/s, {now - hopStart:F2} s in the air.");
                return;
            }

            // Level: turn the car's up towards the world's up, and damp the tumble but not the yaw.
            var tilt = Vector3.Cross(b.transform.up, Vector3.up);
            var tumble = Vector3.ProjectOnPlane(b.angularVelocity, Vector3.up);
            b.AddTorque(tilt * LevelGain - tumble * LevelDamping, ForceMode.Acceleration);

            // Landing: hold the fall at LandingSpeed near the ground.
            if (vy < -LandingSpeed && GroundDistance(b) < LandingBrakeHeight)
            {
                var thrust = Mathf.Clamp((-LandingSpeed - vy) / Time.fixedDeltaTime + gravity, 0f, MaxThrust);
                b.AddForce(Vector3.up * thrust, ForceMode.Acceleration);
            }
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

# Roadster mod plan

A drivable Roadster for Big Ambitions, after Tesla's 15 October 2026 reveal: the 0-60 mph launch in 0.81 s, thruster hops and flips on a button. Planned 16 October 2026.

## What the reveal showed

Sources: [The Drive](https://www.thedrive.com/news/tesla-roadster-reveal-updates), [Carscoops](https://www.carscoops.com/2288442/2028-tesla-roadster-reveal/).

- Shown live: a 0-60 mph run on Tesla's timer, 0.81 s. Not independently timed.
- Shown: the car climbs a ramp until it is upside down, held on by fan suction. Then it drives off the ramp, flips with thrusters and lands under control. It also barrel-rolls over the Tesla lineup and lands.
- Claimed: ten cold-gas thrusters in the rear diffuser, fed by two 600 L tanks of compressed air that refill while driving. The thrusters also add forward acceleration. The fans give up to 2 g of downforce at a standstill.
- Not shown: sustained flight. The car hops, flips and rolls. "Flying" in the mod means thruster hops and glides, not a plane.
- Not published: weight, power, top speed, range, price. Production is planned for 2028.

## How it maps onto the game

- **Vehicle type.** Data-driven `VehicleType` registered through `ModdingAPI.RegisterModVehicleType`. The prefab is found by file name (`Roadster.prefab` for `roadster:vehicletype_roadster`).
- **Physics.** NWH Vehicle Physics 2 on an ordinary Rigidbody (`CarController.vehicleController.vehicleRigidbody`). `AddForce` and `AddTorque` work. `VehicleType.maxSpeed` and `enginePower` are showroom numbers only; the prefab's engine, gearing and brakes drive the car.
- **Launch.** 0.81 s is 33.1 m/s², about 3.4 g. Tyres give about 1 g, so the extra push comes from the thrusters, as Tesla says it does on the real car. `RoadsterDrive.Launch` follows a straight speed line and logs the measured time.
- **Flip-over module.** NWH's `FlipOverModule` only rights a car that is nearly stopped (below 0.6 m/s) and tilted past 70°. It never acts mid-air, so it stays on as the safety net for a roof landing.
- **Input.** `Keyboard.current`, guarded by `GameManager.ShouldBlockKeyboardShortcuts()` and `CityMap.IsOpen`, as the other HART mods do.
- **Dealer.** A Harmony postfix on `VehicleContractSettings.SetListOfVehiclesForSale`, the Food Trucks mod's method.
- **Name.** The game uses parody names for real cars (Anselmo AF90, Mersaidi, Vord, Petrolls Fanton). A public release should follow that pattern. Tesla's name and its likeness are trademarks.

## Risks

- **Rescue barriers.** `RescueBarrier` tows a driven vehicle to the repair shop when it touches a barrier trigger. High hops and long glides near the map edge will trip them.
- **Saving in the air.** The save stores the car's position. A save mid-hop reloads the car in the air, and the game's load code waits for it to settle.
- **Crash damage.** Hard landings deform the body (`VehicleDeformationController`) and add damage. At damage 1 the engine stops.
- **Camera.** The drive camera is Cinemachine. Flips and 3.4 g launches may make it swing or lag. It may need its own camera mode during stunts.
- **Traffic.** AI cars and the NavMesh obstacle toggler aren't checked with a car in the air.
- **Removal.** Saves holding a mod vehicle lose it when the mod is removed. The Food Trucks mod needed an uninstall-and-refund step.
- **Every launch is a launch.** In phase 0, full throttle from a standstill always fires the 3.4 g launch, at every traffic light. Phase 1 adds a launch mode.

## Phases

| Phase | Work | Effort |
|---|---|---|
| 0 Spike | Repo, build, placeholder car on the SDK example body, dealer entry, launch push, J hop with levelling and a braked landing. | 1 session |
| 1 Drive | Launch mode (hold brake and throttle, release brake), tuned grip and steering at speed, top speed, brakes, the right dealer and price. | 1-2 days |
| 2 Model | Roadster body from the reveal photos in Blender (no official model exists): body, wheels, collision mesh, paint mask, lights, spoiler. Peter's look check. | 2-4 days |
| 3 Thrusters | Air tank that refills while driving, hop, glide, backflip, front flip and barrel roll on keys, an attitude controller that lands wheels down, thruster jets and sound, camera handling. | 3-5 days |
| 4 Edge cases | Rescue barriers, saving in the air, traffic, damage on landing, uninstall, both platforms. Review loop. | 2-3 days |

Total: about 10 to 15 working days. Ramp driving upside down with fan suction is a stretch goal after phase 4.

## Status

Phase 0 is written and builds. Nothing in this repo has been checked in game yet.

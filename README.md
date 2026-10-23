# Roadster

A Big Ambitions mod: a Roadster with a thruster launch (0-60 mph in 0.81 s), fan downforce and a thruster barrel roll.

Version 0.0.3 preview: lights follow the vehicle's normal light state, and dealer colours apply to the body and wing. Keeps 0.0.2's faster landings and straight-run launch assistance. In-game verification is still pending; see `CHECKS.md`.

## Controls

- **Launch:** full throttle from a standstill. N switches between the motors (0-60 mph in 1.6 s) and the nitrogen thrusters (0.6 s, with the rear plumes).
- **Fans:** always on while the wheels are on the road: an extra 2 g of downforce for grip in corners.
- **Barrel roll:** J. The car lifts 6 m on its thrusters while already rolling, rolls once (towards the side you steer, right when straight) and lands level.

## Install

Copy the `Roadster` folder into `ModsLocal` with the game closed. The mod changes every save it loads; removing it later loses any Roadster in those saves.

## Build and offline checks

Use the pinned Unity SDK and local game DLLs described in `tools/build-mod.sh`.
Run `bash tools/check-all.sh` for the complete offline suite and fresh Windows/Mac
SDK build on the Mac. It uses an empty Unity editor scene to test the actual game
colour/light methods, without starting Big Ambitions or using a test rig.
Then run `python3 tools/package-release.py` to create the checksum-verified preview
ZIP under `build/releases` (existing archives are never overwritten).

Implementation and verification limits: `docs/appearance-0.0.3.md`.

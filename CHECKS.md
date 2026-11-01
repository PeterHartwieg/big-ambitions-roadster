# Checks: the model build

Use a throwaway save. The mod changes every save it loads.

## Look and feel (about 10 minutes)

1. General US Trucks, 1 7th Avenue: the Roadster is listed and can be bought. It is the white Roadster model, wheels on the ground, nothing floating or sunk, wing folded on the rear deck.
2. Walk around it in daylight and at night: body, glass, lights, rear diffuser and nozzles look right; nothing missing, black or see-through. The lamps should stop emitting when the vehicle lights are off; the coloured lenses remain visible in daylight. Follow the 0.0.3 checks below.
3. From a standstill, floor it with the motors, then press N and floor it again with nitrogen. Two different launches? Do the four rear plumes show during the nitrogen one and look like cold gas? Does the camera cope?
4. Press Backslash (`\`) while driving above 2 m/s (about 4.5 mph), first straight and then steering left. Does the car leave the ground already rolling, in one fluid motion, with the two down plumes firing, roll once the right way round, and land level and gently? Does the camera cope? After cooldown, press Backslash stopped and creeping at or below 2 m/s: neither must lift, fire down plumes, or log a `Barrel roll to ...` start. Holding the rejected key while accelerating must not queue a roll; release and press again above the threshold. With HART. Self Driving on its default bindings and a pinned destination, press J in a stopped Roadster: self-driving must start without a roll. Press J while moving: no roll. N must still switch launch mode.
5. Drive fast through the city. Anything that feels broken: grip, steering, brakes, bumps at speed?
6. Does the game stutter with the Roadster on screen? The model is about 142,000 triangles, roughly 20 times a game car.
7. Corners at speed: does the fan suction make the car grip without feeling like it bottoms out?

## Log lines (read by the agent from Player.log)

- `Version 0.0.3 loading.`, `Vehicle registered: roadster:vehicletype_roadster`, `Active: VehicleContractSettings.SetListOfVehiclesForSale.`
- `Launch (motors): 0-60 mph in X s`: X within 1.25 to 1.35; `Launch (nitrogen)`: within 0.57 to 0.63. Measured 1 Nov 2026 in the PC rig with the same method: 0.0.2 median 1.31 s, 0.0.3 median 1.29 s; launch code unchanged since 0.0.2, logged target stays 1.60 s.
- `Plumes found: 4 rear, 2 down.`
- `Barrel roll to the right/left at X mph.`: accepted moving starts above 2 m/s (about 4.5 mph); no start line for stopped/creeping Backslash or J presses. Capture speed and key input alongside the log for rejected starts.
- `Barrel roll landed: peak X m, rolled Y degrees, touchdown Z m/s, W degrees off level`: peak about 6 m, rolled 360, touchdown at most 5 m/s, under 10 degrees off level, about 2.5 s in the air.
- `Corner:` lines: no wheel `UP`, loads under 14,000 N, compression under about 70%.
- No `ERROR` lines from `[Mod:Roadster]`.

## 0.0.3 manual acceptance — all pending

PC rig preflight on 30 October 2026 was [blocked before launch](docs/rig-test-0.0.3.md). No in-game box below was checked; before/red and after/green proof remains missing.

The recorded `8448179` preview in `docs/release-0.0.3.json` is **stale**, superseded by the issue #2 source fix commit on top of `3579e2c` (`Fix barrel-roll key clash and require movement (Refs #2)`). It has the old J binding and no speed guard. A fresh build from the superseding source commit must be identified and tested by the scheduled Codex Sol/high PC rig session after 6 November, with before/red and after/green proof on PR #1 before merge/upload. This fix run does not rebuild or use the rig.

Issue #2 key selection (31 October, **source review only; in-game compatibility pending**): Backslash is absent from the Mod Pack key matrix in `hart-group/docs/research/modpack-review-2026-10-07/world.md` at `01a6146`. That matrix covers Hyperreal, Camera Tools, HART Free Camera and Campaign Objectives. Also checked the current pack member list (`big-ambitions-modpack/modpack.json` at `2152955`), Self Driving's J/K/L defaults and destination key choices (`hart-self-driving` at `8b9547a`), RLO's bindings/game defaults (`RLO/Assets/Mods/RealLifeOverhaul/Scripts/Core/Keys.cs` at `850e278`), and HART tool sources for Backslash bindings. RDSTR has no configuration support: the new Backslash binding remains a constant, and N remains launch mode.

Use a disposable save and compare against a vanilla car under the same conditions.

1. At General US Trucks choose two clearly different colours, purchase two Roadsters,
   and confirm the body and folded wing match each choice. Changing one must not
   repaint the other; glass, carbon, wheels, plates and lamps retain their colours.
2. In clear daylight enter and drive: headlights, tail lights and amber markers
   must not emit continuously. Brake while moving: the rear lights brighten and
   return to unlit when released. Lens reflections are not emission.
3. Drive through dusk/night and dawn, and test daytime rain: front lights, amber
   markers and tail lights follow the vanilla automatic state. Brake at night:
   rear lights get brighter and return to tail brightness on release.
4. Exit at night: lamps and projected headlight beam switch off like vanilla.
   Re-enter and repeat; park two differently coloured cars together and check
   their lights and paint remain independent. Amber markers are not turn signals;
   the current mesh has a single material for both sides.
5. Save/reload the two colours in daylight and at night. Also load a disposable
   copy of a save with an existing 0.0.2 Roadster: its saved colour should apply
   without repurchasing it. Check the dealer's currently selected colour is used
   on purchase, not a colour from an earlier selection.
6. Check both sides of the car, hover outline, body and wing at near/far camera
   distances and after leaving/re-entering the area. Check no pink/missing shaders,
   giant glow, daylight emission, unexpected dirt texture or decal projection.
7. Run the existing launch, nitrogen plume and barrel-roll checklist above. Check
   startup says 0.0.3 and the dealer patch is Active; no new mod/asset/shader errors.

Offline evidence is documented separately in `docs/appearance-0.0.3.md`. These
manual boxes stay pending until Peter observes them in game on the target platform.

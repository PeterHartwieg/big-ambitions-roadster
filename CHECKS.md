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

## 0.0.3 manual acceptance

Results for each item below are in `docs/rig-test-0.0.3.md`. Still open there: stunt camera, subjective feel, night re-entry repeat and two-car lamp independence.

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

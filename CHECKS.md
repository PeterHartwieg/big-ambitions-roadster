# Checks: the model build

Use a throwaway save. The mod changes every save it loads.

## Look and feel (about 10 minutes)

1. General US Trucks, 1 7th Avenue: the Roadster is listed and can be bought. It is the white Roadster model, wheels on the ground, nothing floating or sunk, wing folded on the rear deck.
2. Walk around it in daylight and at night: body, glass, lights, rear diffuser and nozzles look right; nothing missing, black or see-through. The lights glow all the time for now and the dealer colour doesn't repaint it (both known).
3. From a standstill, floor it. Does the launch feel like a launch, and does the camera cope?
4. Press J while driving and while standing. Does the car go up, stay level and come down gently?
5. Drive fast through the city. Anything that feels broken: grip, steering, brakes, bumps at speed?

## Log lines (read by the agent from Player.log)

- `Version 0.0.1 loading.`, `Vehicle registered: roadster:vehicletype_roadster`, `Active: VehicleContractSettings.SetListOfVehiclesForSale.`
- `Launch: 0-60 mph in X s`: X within 0.78 to 0.84.
- `Hop landed: peak X m, touchdown Y m/s`: peak about 5 m, touchdown at most 3 m/s.
- No `ERROR` lines from `[Mod:Roadster]`.
- Frame rate with the Roadster on screen against another car (the model is about 142,000 triangles, roughly 20 times a game car).

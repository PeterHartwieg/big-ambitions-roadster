# Phase 0 checks

Use a throwaway save. The mod changes every save it loads.

## Look and feel (about 10 minutes)

1. General US Trucks, 1 7th Avenue: the Roadster is listed and can be bought. It looks like the SDK's example car for now.
2. From a standstill, floor it. Does the launch feel like a launch, and does the camera cope?
3. Press J while driving and while standing. Does the car go up, stay level and come down gently?
4. Drive fast through the city. Anything that feels broken: grip, steering, brakes, bumps at speed?

## Log lines (read by the agent from Player.log)

- `Version 0.0.1 loading.`, `Vehicle registered: roadster:vehicletype_roadster`, `Active: VehicleContractSettings.SetListOfVehiclesForSale.`
- `Launch: 0-60 mph in X s`: X within 0.78 to 0.84.
- `Hop landed: peak X m, touchdown Y m/s`: peak about 5 m, touchdown at most 3 m/s.
- No `ERROR` lines from `[Mod:Roadster]`.

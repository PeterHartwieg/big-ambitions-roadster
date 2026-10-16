# Roadster mod for Big Ambitions

A mod that adds a Roadster with a thruster launch, hops and flips. Read `docs/plan.md` first. `CLAUDE.local.md`, if present, has the machine setup and is never committed.

## Layout

- `unity/Roadster/`: the mod folder for the official SDK (`Assets/Mods/Roadster` once linked). Runtime and Harmony patches.
- `unity/BuildEditor/`: editor code that generates the vehicle assets and runs the SDK packager in batch mode.
- `tools/build-mod.sh`: the build. `--generate` re-creates the generated assets first.
- `CHECKS.md`: the in-game checklist for the current phase.

## Rules

- Never commit game DLLs, decompiled game code, Harmony binaries or save files.
- Each Harmony patch logs one `Active` or `Not active` line at startup.
- Every stunt logs its measured numbers (0-60 time, hop height, touchdown speed) so checks read the log, not a stopwatch.
- Mark evidence as checked (seen in game), pending or unverified. Code reading is not a check.
- Neutral names in shipped files: no references to any YouTube series or personal saves.

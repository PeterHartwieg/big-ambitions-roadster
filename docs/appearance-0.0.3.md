# RDSTR 0.0.3 appearance fixes

Status: implementation and offline verification complete. Release candidate only. All in-game checks
remain pending; no test rig, game profile or save is used for this work.

## Diagnosis from local references

The supplied `build/game-dlls/BigAmbitions.dll` and `ExternalPlugins.dll` were
inspected with the locally installed `ilspycmd`. Decompiled references remain
private under ignored `build/references`; no game code or DLLs are committed.
The shader source is from the official SDK pinned by `tools/build-mod.sh` at
`1e03ddd5071b77a32cfd8bba89f0c130ba6c7d73`.

- `CarFeatures.SetColor(VehicleColor)` stores the selected colour and writes tint,
  fresnel colour and fresnel power into each `bodyMeshes` renderer property block.
  `VehicleController` reapplies the saved colour during initialization. The
  Roadster body and wing were already registered, but HDRP/Lit ignores these
  vehicle-shader property names. `VehicleContractSettings.SelectColor` calls
  `ContractVehicleForSale.SetColor`; purchase copies that selection into
  `VehicleInstance.vehicleColorName`, and `SetVehicleInstance` reapplies it.
- `CarController` sets the low-beam and tail groups from `ShouldLightsBeOn` when
  entering, on outdoor-light changes while controlled, and when the effects LOD
  becomes active. The condition includes rain and outdoor-light/time-of-day state.
  Exiting calls `TurnOffAllLights`.
- NWH `LightSource` of type `ShaderProperty` preserves renderer property blocks
  and writes `_FrontLightStrength`, `_BackLightStrength` or
  `_ReverseLightStrength`. The inherited prefab addresses the whole body
  (`rendererMaterialIndex = -1`). Its strengths are front 50,000, tail 20,000,
  brake 40,000. Brake release restores the tail state.
- The model's HDRP/Lit lamps ignored those writes and instead had permanently
  nonzero `_EmissiveColor`. This explains the reported always-on glow.

## Change

`RoadsterMaterials` generates Paint, HeadLight, TailLight and Indicator materials
using the SDK's existing `SH_Vehicle` shader. Diffuse alpha enables paint tint
only on Paint, including the wing. Lamp masks select front (red channel) or
rear/brake (green channel). All light strengths start at zero. Explicit flat
textures prevent the SDK example car's UV textures from appearing on this mesh.
Lamp coefficients retain the old model's lit emission, with twice the rear
brightness while braking. Small coefficients use float textures to avoid being
quantized to black.

The amber material covers both sides, so it follows the front lamps as marker
lighting. No new turn-signal or reverse-light geometry is claimed. Glass, trim,
wheels and plates retain HDRP/Lit. The export also uses Paint on wheel details;
those four slots receive a separate WheelPaint material with their original
finish, so native body tint does not recolour them. Thruster plume materials/controller and driving
physics are unchanged. No new runtime Harmony patch, polling loop, cloned material
per car, save format or custom clock/rain logic is needed.

## Offline checks

`bash tools/check-all.sh` runs the Python packager regression suite, runs `AppearanceChecks` in an empty Unity editor play-mode scene, and
builds both platforms with the official SDK, then repeats the native checks against
the actual Mac asset bundle. Add `--generate` to regenerate the assets first. The native checks use real
`CarFeatures.SetColor` and NWH `VehicleLight`/`LightSource` methods on lightweight
renderer fixtures with the generated prefab's material/light configuration.
They check two-car isolation, repaint/light interleaving, default-off state,
head/tail/brake transitions, paint masks, material bindings and neutral textures.
This is not a launch of Big Ambitions or an in-game/rendered acceptance test.

The partial SDK's empty play-mode scene emits bootstrap errors from missing game
content (ArcadeMachines, Addressables/Seasons and game managers). Before testing,
the runner captures a fresh empty-scene baseline. Source and bundle tests require
an exact match to those startup error messages, then fail on any error during the
appearance fixtures themselves. The bootstrap messages remain in the local logs;
they are not presented as a clean game launch. No game content is copied in to
work around them.

The strict release packager verifies exact file inventory, build checksums,
ZIP CRC, round-trip bytes and a ZIP checksum sidecar. Regression tests cover
missing/extra/changed files, symlinks, invalid locales and existing ZIP protection.

Reference SHA-256 values:

| Local reference | SHA-256 |
| --- | --- |
| BigAmbitions.dll | `9427561b81aaab2ada09c22a3c98dd9a4017a65225b389513885bf336852e911` |
| ExternalPlugins.dll | `7d43e9d42d2f464674cff045bcb048c48e0f87aec0a987baa34122ac6e3415d1` |
| SDK SH_Vehicle.shadergraph | `708d03b57d19617132b22b2ab5a6422f7972c641603a8031514b40703a9cc792` |

## Verification results — 23 October 2026

- Full Python suite: **8 passed**.
- Native Unity source-asset checks: **227 passed**.
- Native checks against the freshly built Mac bundle: **228 passed**.
- Both fixture runs match the **8** empty-SDK bootstrap diagnostics and report
  **zero errors during the appearance checks**. No new C# compiler warnings;
  the SDK packager's existing duplicate-type warnings remain.
- Negative controls: separately restoring the original 0.0.2 Paint and HeadLight
  materials makes the suite reject each for the expected shader mismatch. Both
  materials were restored and the full suite/build passed again afterward.
- The Mac-hosted official SDK build produced both Windows and Mac bundles.
- Generated prefab comparison preserved all 113 compared objects/components
  except the four intended wheel-material references. Original object IDs were
  retained; physics, plumes and driving configuration remain unchanged.
- Package inventory, checksums and ZIP round trip passed. Exact artifact and
  build-source commit are recorded in `release-0.0.3.json`; the ZIP is ignored.

All in-game acceptance remains pending on both platforms, including dealer
purchase, existing saved cars, save/reload, night/rain transitions, lamp appearance,
hover outline, LOD and driving/stunt regressions. Peter's checklist is in
`CHECKS.md`. No test rig, live installation or Workshop upload was used.

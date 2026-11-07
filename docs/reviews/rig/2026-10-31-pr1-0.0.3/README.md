# PC rig proof (agent1): 0.0.3

**Verdict: FAIL. Do not merge on this evidence.** The required motor-launch timing was outside the acceptance range. Default J reached Self Driving, but its departures cancelled; a sustained departure remains incomplete. The rig is restored and the lease released.

Tested PR #1 head `0e6d82332cc122235fca10c1ede90745939114b7`, branch `codex/rdstr-0.0.3`, on Windows game build **3682**, using the existing isolated `C:\BigAmbitions-AgentTests` runtime. The PR head was independently rechecked and remains that SHA. Requested role/model: rig_test, Codex Sol/high; no provider-returned model identifier is available to assert. No production code/tests, source branches, PR body, Steam files/settings, normal profile, Windows settings or game graphics settings were changed. No merge or Workshop upload.

| Check / expected AFTER | BEFORE 0.0.2 (red/control) | AFTER 0.0.3 | Evidence |
| --- | --- | --- | --- |
| 1. Two dealer colours repaint body + folded wing independently; save/reload retains colours | **Red reproduced:** Red and Blue purchases both rendered silver/white | **PASS:** two fresh dealer purchases used Red and Blue, body/wing matched each and stayed independent. Day and night save/reload retained both. Existing 0.0.2 cars also repainted from their saved colours without repurchase. Sampled glass, carbon, plates and lenses retained their colours; no pink shader, giant glow, unintended dirt/decal projection in sampled views. | S1 PNGs; observations.json: after-new-two-paint, after-day-reload-observed, final-night-reload-confirmed-colours |
| 2. Day off, brake brightens/returns, night automatic lamps/beam and exit off; vanilla parity | **Red reproduced:** constant HDRP lamp emission, including daylight. Native runtime emissive colours: head (29.6,36.4,40), tail (10.4,.096,.192), amber (24,4.56,.192) | **PASS for day/night, braking, dawn/dusk and exit.** Day rear 0 -> 40000 -> 0; night rear 20000 -> 40000 -> 20000, including moving S-key samples. Night front/tail 50000/20000 and exit 0/0 match vanilla Mersaidi Dash, with beams off after exit. Rain entry also matches vanilla; see live-toggle limitation below. | S2 PNGs; observations.json native-brake-night/native-brake-day-long and vanilla snapshots |
| 3. Wheel/rim finish independent of body colour | Same silver finish on both white-body controls | **PASS:** silver/dark wheel finish remains the same with red versus blue paint; wheel close-ups show readable rim portions. Native bindings use separate WheelPaint on all four wheel meshes. | S3 PNGs; source native wheel observations retained locally |
| 4. Moving Backslash right/left rolls; stopped/creeping/held reject; J compatibility; N works | **Red reproduced:** J at about 0 m/s started a roll at 0 mph | **INCOMPLETE overall.** Right roll, low-speed rejection, held-key rejection, moving-J no-roll and N switch passed. Boulevard logs: right 31 mph, peak 6.3 m, 360°, touchdown 2.7 m/s, 1°; left 25 mph, peak 6.3 m, 360°, touchdown 3.1 m/s, 2°, but a tree contact occurred before the left landing, so a clean left-roll pass remains pending. Stopped J entered native Self Driving (no roll), then cancelled during unparking/route setup; no sustained self-driven departure was observed. | before-log.txt, after-log.txt; input-trials.json and key-presses.csv (all recorded presses, including setup trials) |
| 5. Versions/registration/dealer/plumes; no new errors; measured launches in range | **PASS for startup:** 0.0.2, registered, dealer Active, 4 rear/2 down; no Roadster ERROR. Motor launch not measured in BEFORE | **FAIL:** startup 0.0.3, registration, dealer Active, 4 rear/2 down and error checks passed. Nitrogen **0.60 s**, within 0.57–0.63. Motors **1.31 s**, outside **1.55–1.65**; later runs also ended around 57–58 mph at 1.52 s. No timing fix or production change was made. | after-log.txt, log-audit.json; raw trial/final log SHA-256s recorded |

## Native excerpts

```text
[Mod:Roadster] Version 0.0.2 loading.
[Mod:Roadster] Barrel roll to the right at 0 mph.
[Mod:Roadster] Barrel roll landed: peak 6.3 m, rolled 360 degrees, touchdown 3.6 m/s, 1 degrees off level, 2.66 s in the air.

[Mod:Roadster] Version 0.0.3 loading.
[Mod:Roadster] Vehicle registered: roadster:vehicletype_roadster (price 250000).
[Mod:Roadster] Active: VehicleContractSettings.SetListOfVehiclesForSale.
[Mod:Roadster] Plumes found: 4 rear, 2 down.
[Mod:Roadster] Barrel roll to the right at 31 mph.
[Mod:Roadster] Barrel roll landed: peak 6.3 m, rolled 360 degrees, touchdown 2.7 m/s, 1 degrees off level, 2.62 s in the air.
[Mod:Roadster] Barrel roll to the left at 25 mph.
[Mod:Roadster] Barrel roll landed: peak 6.3 m, rolled 360 degrees, touchdown 3.1 m/s, 2 degrees off level, 2.62 s in the air.
[Mod:Roadster] Launch (motors): 0-60 mph in 1.31 s (target 1.60 s).
[Mod:Roadster] Launch mode: nitrogen.
[Mod:Roadster] Launch (nitrogen): 0-60 mph in 0.60 s (target 0.60 s).
[Mod:DrivenRides] Own car: driving itself (roadster:vehicletype_roadster, wheelbase 2.79 m).
[Mod:DrivenRides] Own car: the keys are the player's again (cancelled: unparking: not enough clear straight road to pull out).
```

Input System events and measured body speed accompany each recorded J/Backslash/N press in `key-presses.csv`; `input-trials.json` also records peak height and whether down plumes were enabled. Native 0 mph included body-speed jitter below 0.4 m/s. Rejected Backslash trials showed no lift/start/down plumes, and the held-key run reached 26.54 m/s without queuing a roll. The final separate crawl requested Backslash at 0.820 m/s (first actual key sample 0.424 m/s), with no start or down plume. Early setup trials hit props/parked cars; those are retained and are not presented as clean roll acceptance. The later boulevard right landing had no contact. The left trial hit a tree at 13.0 m/s before its otherwise in-range landing; those numbers are reported, not promoted to a clean left-roll pass. See roll-log-spans.json for all four start/landing spans and contacts.

## Packages and identity

All three supplied archive SHA-256s matched **before use**; ZIP CRCs and member hashes also verified. Full member hashes are in `package-hashes.json`.

| Archive | SHA-256 |
| --- | --- |
| AFTER after-0e6d823-Roadster-0.0.3-preview.zip | `df2621160712a539821d7f80ff31262cfe6aa2f798d1bf26ebfd78ea62bddd04` |
| BEFORE before-master-2250540-Roadster-0.0.2-preview.zip | `d64d67074a1e4b62d2e52631b7375e5314d0d19f9601ad683d041cbc89154f7e` |
| REFERENCE uploaded-0.0.2-Roadster-0.0.2-preview.zip | `28877bf82f13dab6a63b998efae6d515fc75e0d13a258929193c894aac793057` |

BEFORE and the uploaded archive have byte-identical actual Windows/Mac asset bundles. Roadster.dll, the two bundle manifests and their checksum listing differ. The uploaded DLL was not run; no specific BEFORE-only behavioural discrepancy was established, and runtime equivalence is not asserted solely from matching source/assets.

HART. Self Driving **0.4.1** was copied from Workshop item 3819853552 into agent1 only, with copy/installed hashes verified. Its DLL SHA-256 was `062d63970052cb4a8f04751c697313c10cf021c7cfd4ca751ff6e49493481724`. J/K bindings were not changed. The source Workshop files were rehashed unchanged afterwards; details: `self-driving-hashes.json` and `lifecycle.json`. Test copies/helpers are outside the restored active profile; its pre-existing mod inventory, including its original Self Driving copy, is restored exactly.

The approved existing rig uses managed game hash `055700fd26a7a6430bbb6a9d79379781909fbc518af760453396947887db5063`; this is not a new stock-game validation. The evidence establishes failed timing acceptance on this rig, not that the PR introduced a timing regression. No ERROR line from Roadster or new shader/asset-load exception was found in the final native log. The usual native null-renderer/NavMesh warnings and initial fixture-only kinematic-velocity warnings are not counted as clean production errors or silently attributed to the candidate.

## Limits and open items

- **Motor launch acceptance failed.** A clean recheck/explanation is needed before treating CHECKS.md's motor range as met. BEFORE motors were not measured, so this session does not attribute the timing discrepancy to 0.0.3.
- **Clean left-roll acceptance remains incomplete.** Both left trials contacted scenery before landing (building, then tree). Their measured direction/rotation/landing numbers are retained; the contact-free right roll is a separate pass.
- **Stopped-J departure remains incomplete.** J reached Self Driving's native controller without a roll, but attempts either refused while the body jittered above its 0.3 m/s stop threshold, reported a lane/departure restriction, or initialized then cancelled. This is not a completed-trip claim.
- **Rain live-toggle timing is incomplete.** Entering either vehicle during noon rain gave the same native 50000/20000 state. While already controlled, a Roadster rain-on toggle initially left 0/0 despite ShouldLightsBeOn=true; vanilla rain-off similarly retained 50000/20000 despite false. Re-entry/time transitions refreshed lamps. No mod light state was assigned by the helper, and no instant-toggle pass is claimed.
- **SKIPPED-LOCKED — hover outline:** free hover/pointer input unavailable in the locked session.
- **SKIPPED-LOCKED — native near/far camera/LOD and stunt camera comfort:** no free camera drag/pointer route was used; observer-camera renders cannot establish native-camera behaviour. Game-view captures were black and excluded from proof images.
- **SKIPPED-LOCKED — subjective stutter/handling/camera feel:** no visible interactive play assessment was possible. Short scripted physical trials are not a city-driving or performance benchmark.

All images here are native PNG renders from the running game through the established bridge's **observer camera**, resized to 1000 px width to keep the evidence small. There are no AI-generated/repainted images. Native originals and their SHA-256s are retained; `screenshots-manifest.json` records originals, exact resize and published hashes. The wheel close-ups show readable portions of the rims; they are not full-wheel framing. Diagnostic-camera images do not substitute for the skipped native camera/hover checks.

## Restoration and release

- Lease owner `rdstr-pr1-0.0.3-rig` acquired the free agent1 lease at **2026-10-31T05:01:44.5635901Z**. No takeover or queue wait was needed. Every launch checked lease ownership, receipt hashes and absence of all Big Ambitions processes.
- Backed up the entire isolated profile, isolated preferences, installation receipt, run receipt and previous log before installation. Only disposable FT fixtures were loaded/created. Exactly one Roadster package was active at a time; unrelated rig mods were parked and subsequently restored.
- Restoration verified at **2026-10-31T05:46:53.6342990Z**: **4828 profile files** and **107 installation references** match the original inventory/SHA-256. Preferences match: `66fccbcc5f63bc492e36ba7f342d9d2480adb2b87404a650a8607094d207381d`.
- Restored installation receipt SHA-256: `9785d1de5c7360875b2a2a47f511815660dd98a38d6f64ab4ecff8c20627b949`. Original run receipt and Player-agent.log also match; hashes are in `lifecycle.json`.
- Lease released at **2026-10-31T05:48:02.6935979Z**: **unheld, zero pending operations, no Big Ambitions process**. The isolated game quit natively. No normal-game process was launched, stopped or controlled.

Full raw logs, native PNGs, original/exercised profile and helper provenance remain in the local rig evidence backup. No game DLL, decompiled game code, mod/game binary, save or credential is committed in this evidence folder.

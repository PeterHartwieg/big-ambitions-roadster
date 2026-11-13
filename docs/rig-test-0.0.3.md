# RDSTR 0.0.3 PC rig acceptance record

Updated 7 November 2026. A 30 October preflight was blocked before launch; the 31 October, 1 November and 7 November rig sessions below replace it.

## Shipped candidate

- PR [#1](https://github.com/PeterHartwieg/big-ambitions-roadster/pull/1), squash-merged as `7671f84d2e9d015c8a663824e078dde669f962d6` on 2026-11-01 (07:43 UTC).
- Source head `43765955ddd185676d72f0f0a075b35a9950f01c` on `codex/rdstr-0.0.3`, the same tree as the merge. It is `0e6d823` (barrel roll on Backslash above 2 m/s, Refs #2) plus a CHECKS.md-only motor range change to 1.25–1.35 s.
- Package `Roadster-0.0.3-preview.zip`, 17,918,517 bytes, SHA-256 `05a27e4271cccc408914367a7aadd4059c9c00bb6709bc33c88c8ca5b5439ccd`. Recomputed on 7 November from `C:\Users\Peter\HART-Builds\rdstr-0.0.3-release\`; member hashes are in `docs/release-0.0.3.json`.
- **Build source commit: unverified.** The build did not record it. Its RELEASE-NOTES.txt and en.json match `7671f84`, not the later `6e97ff2`. Those bytes are equally consistent with `0e6d823`, because CHECKS.md is not packaged.
- The rig ran package `df2621160712a539821d7f80ff31262cfe6aa2f798d1bf26ebfd78ea62bddd04`, built from `0e6d823`. It has the same asset bundles, Harmony, INSTALL, RELEASE-NOTES and en.json bytes as the shipped zip. Roadster.dll and the bundle manifests differ because rebuilds are not deterministic.
- **The shipped `05a27e42` zip was run in the rig on 7 November.** Its SHA-256, member hashes and ZIP CRC were checked before install; no rebuild ([package verification](reviews/rig/2026-11-07-rdstr-0.0.3-native/package-verification.json)).

The `8448179` preview (`e7d67a30…`, 23 October) is **historical**. It still bound the roll to J and had no speed guard. Its record is kept under `superseded_preview` in `docs/release-0.0.3.json`.

## Evidence

| Session | Package | Evidence |
| --- | --- | --- |
| 31 Oct 2026, agent1, game build 3682 | `df262116…` (0e6d823) vs 0.0.2 `d64d6707…` | [2026-10-31-pr1-0.0.3](reviews/rig/2026-10-31-pr1-0.0.3/README.md) |
| 1 Nov 2026, agent1, motor timing and left roll | same | [2026-11-01-pr1-0.0.3-timing](reviews/rig/2026-11-01-pr1-0.0.3-timing/README.md) |
| 7 Nov 2026, agent1, remaining native checks | shipped `05a27e42…`, Self Driving 0.4.2 | [2026-11-07-rdstr-0.0.3-native](reviews/rig/2026-11-07-rdstr-0.0.3-native/README.md) |

The first two folders are unchanged copies from `rig-evidence/rdstr-pr1-0.0.3` (`252ddbf`) and `rig-evidence/rdstr-pr1-0.0.3-rig2` (`865bd45`). Images come from the rig's observer camera in a locked session. They are not native-camera views. The 7 November folder is an unchanged copy of that session's artifacts. Its `native-*` PNGs are native-camera captures; the other images there are observer-camera views.

The 31 October verdict was FAIL because motors logged 1.31 s against the old 1.55–1.65 s range. On 1 November, 0.0.2 and 0.0.3 measured the same way gave medians of 1.31 s and 1.29 s. CHECKS.md now uses 1.25–1.35 s, and the timing item passes.

## Per-check status (`CHECKS.md` 0.0.3 manual acceptance)

| Item | Status | Result | Evidence |
| --- | --- | --- | --- |
| 1. Two dealer colours, independent body/wing paint | **PASS** | Red and Blue purchases paint the body and wing independently. 0.0.2 red control: both silver/white. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S1 PNGs |
| 2. Daylight lamps and braking | **PASS** | Day rear 0 → 40000 → 0 when braking. 0.0.2 red control: constant emission. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S2 PNGs |
| 3. Dusk/night/dawn and daytime rain | **PASS / KNOWN ISSUE** | PASS: night, dawn/dusk, night braking 20000 → 40000 → 20000, rain on entry matches vanilla. KNOWN ISSUE matching vanilla: see [Rain live toggle](#known-issue-rain-live-toggle-matches-vanilla). | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), [7 Nov rain matrix](reviews/rig/2026-11-07-rdstr-0.0.3-native/rain-results.json) |
| 4. Exit/re-enter, beams, two-car independence | **PASS / UNVERIFIED** | PASS: exit 0/0 with beams off, matching vanilla Mersaidi Dash; the two cars' paint stays independent. UNVERIFIED: the evidence does not separately record a night re-entry repeat or per-car lamp independence. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), `S2-after-road-night-exit-front.png` |
| 5. Save/reload and existing 0.0.2 car migration | **PASS** | Day and night reload keep both colours. Existing 0.0.2 cars repaint from their saved colour. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S1-after-reload PNGs |
| 6. Both sides, hover, LOD, shader/decal appearance | **PASS** | PASS in sampled observer views: no pink shader, giant glow, daylight emission, dirt or decal. Wheel finish is independent of paint (S3). 7 Nov: hover outline and `CLICK TO DRIVE` tooltip PASS; native wheel-zoom near/far visuals PASS within the sampled range (camera height 11.70 → 24.98 m). No numerical LOD index is claimed. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), [hover](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/native-hover-after.png), [near](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/native-zoom-near.png), [far](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/native-zoom-far.png), [camera-evidence.json](reviews/rig/2026-11-07-rdstr-0.0.3-native/camera-evidence.json) |
| 7. Launch, plumes, barrel roll, startup and errors | **PASS / OPEN** | PASS: startup 0.0.3, registration, dealer Active, 4 rear/2 down, no Roadster ERROR. Motors median 1.29 s; nitrogen 0.60–0.63 s. Right roll at 31 mph: 6.3 m peak, 360°, 2.7 m/s, 1°. Clean left roll at 23 mph with no contact: 6.3 m, 360°, 2.6 m/s, 2°. Stopped, creeping and held Backslash rejected. J stopped and J moving start no roll. N switches mode. 7 Nov, shipped zip: clean left roll at 23 mph, 6.3 m, 360°, touchdown 2.6 m/s, 2°, no contacts. Stopped Roadster + J at 0.0 m/s: Self Driving engaged, `Departed (NWH)`, `Complete (arrived)`, no roll. SKIPPED: stunt camera (rig limit, see below). | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), [1 Nov](reviews/rig/2026-11-01-pr1-0.0.3-timing/README.md), [7 Nov left roll](reviews/rig/2026-11-07-rdstr-0.0.3-native/left-roll.json), [7 Nov J](reviews/rig/2026-11-07-rdstr-0.0.3-native/J-departure.json) |

From the earlier look-and-feel list, the subjective items (city driving feel, stutter, cornering feel) were SKIPPED-LOCKED in both sessions.

## Known issue: rain live toggle (matches vanilla)

On 7 November, rain was toggled on and off while the player stayed in the vehicle. The Roadster's lamp strengths stayed stale for at least 10 s unpaused after each toggle. The vanilla Mersaidi Dash behaved identically. `ShouldLightsBeOn` changed immediately. Re-entering refreshed both cars to 50000/20000 (front/tail) in rain, and to 0/0 in clear weather. This matches vanilla and is not a Roadster-specific regression. A refresh while driving would be an optional later improvement; 0.0.3 ships without one. Evidence: [rain-results.json](reviews/rig/2026-11-07-rdstr-0.0.3-native/rain-results.json), [Roadster rain-on 10 s](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/roadster-rain-on-10s.png), [vanilla rain-on 10 s](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/vanilla-retest-rain-on-10s.png), [full matrix](reviews/rig/2026-11-07-rdstr-0.0.3-native/README.md#rain-finding).

## Stunt camera: skipped

The rig cannot combine keyboard input with native captures. In background mode `Keyboard.current` is null, so no Backslash press reaches the game. In windowed mode keys work, but native frames are black ([example](reviews/rig/2026-11-07-rdstr-0.0.3-native/images/windowed-native-black.png)). Not retried. This is a rig limit, not a failed Roadster key handler. See [camera-evidence.json](reviews/rig/2026-11-07-rdstr-0.0.3-native/camera-evidence.json).

## Remaining native gaps

- [x] ~~Stopped-J Self Driving departure.~~ **PASS 7 Nov** (Self Driving 0.4.2): engaged, departed and completed the trip.
- [x] ~~Rain live-toggle lamp refresh.~~ Reclassified 7 Nov as a **known issue matching vanilla** (above). Not a release blocker.
- [x] ~~SKIPPED-LOCKED: hover outline.~~ **PASS 7 Nov.**
- [x] ~~SKIPPED-LOCKED: native near/far camera and LOD.~~ **PASS 7 Nov** within the sampled zoom range; no LOD index claimed.
- [x] ~~Shipped bytes not run.~~ **Run 7 Nov**: the `05a27e42` zip itself was installed after hash checks.
- [ ] **SKIPPED: stunt camera** (rig limit, above). Not retried.
- [ ] **Unverified: subjective** stutter, handling, cornering and camera comfort.
- [ ] **Unverified: night re-entry repeat and two-car lamp independence** (item 4). Only paint independence is recorded.
- [ ] **Build source commit of `05a27e42` unrecorded** (see above).

## Rig results (this run)

Recorded above from the [7 November native session](reviews/rig/2026-11-07-rdstr-0.0.3-native/README.md). Overall: PASS for the left roll, stopped-J, hover and near/far items; known issue (matches vanilla) for the rain live toggle; stunt camera SKIPPED.

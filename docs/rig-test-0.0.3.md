# RDSTR 0.0.3 PC rig acceptance record

Updated 7 November 2026. The 30 October preflight that used to fill this file is kept [below as history](#historical-30-october-preflight-superseded). It was blocked before launch and has been **superseded** by the 31 October and 1 November rig sessions.

## Shipped candidate

- PR [#1](https://github.com/PeterHartwieg/big-ambitions-roadster/pull/1), squash-merged as `7671f84d2e9d015c8a663824e078dde669f962d6` on 2026-11-01 (07:43 UTC).
- Source head `43765955ddd185676d72f0f0a075b35a9950f01c` on `codex/rdstr-0.0.3`, the same tree as the merge. It is `0e6d823` (barrel roll on Backslash above 2 m/s, Refs #2) plus a CHECKS.md-only motor range change to 1.25–1.35 s.
- Package `Roadster-0.0.3-preview.zip`, 17,918,517 bytes, SHA-256 `05a27e4271cccc408914367a7aadd4059c9c00bb6709bc33c88c8ca5b5439ccd`. Recomputed on 7 November from `C:\Users\Peter\HART-Builds\rdstr-0.0.3-release\`; member hashes are in `docs/release-0.0.3.json`.
- **Build source commit: unverified.** The build did not record it. Its RELEASE-NOTES.txt and en.json match `7671f84`, not the later `6e97ff2`. Those bytes are equally consistent with `0e6d823`, because CHECKS.md is not packaged.
- The rig ran package `df2621160712a539821d7f80ff31262cfe6aa2f798d1bf26ebfd78ea62bddd04`, built from `0e6d823`. It has the same asset bundles, Harmony, INSTALL, RELEASE-NOTES and en.json bytes as the shipped zip. Roadster.dll and the bundle manifests differ because rebuilds are not deterministic. **The shipped `05a27e42` zip has not itself been run in the rig.**

The `8448179` preview (`e7d67a30…`, 23 October) is **historical**. It still bound the roll to J and had no speed guard. Its record is kept under `superseded_preview` in `docs/release-0.0.3.json`.

## Evidence

| Session | Package | Evidence |
| --- | --- | --- |
| 31 Oct 2026, agent1, game build 3682 | `df262116…` (0e6d823) vs 0.0.2 `d64d6707…` | [2026-10-31-pr1-0.0.3](reviews/rig/2026-10-31-pr1-0.0.3/README.md) |
| 1 Nov 2026, agent1, motor timing and left roll | same | [2026-11-01-pr1-0.0.3-timing](reviews/rig/2026-11-01-pr1-0.0.3-timing/README.md) |

Both folders are unchanged copies from `rig-evidence/rdstr-pr1-0.0.3` (`252ddbf`) and `rig-evidence/rdstr-pr1-0.0.3-rig2` (`865bd45`). Images come from the rig's observer camera in a locked session. They are not native-camera views.

The 31 October verdict was FAIL because motors logged 1.31 s against the old 1.55–1.65 s range. On 1 November, 0.0.2 and 0.0.3 measured the same way gave medians of 1.31 s and 1.29 s. CHECKS.md now uses 1.25–1.35 s, and the timing item passes.

## Per-check status (`CHECKS.md` 0.0.3 manual acceptance)

| Item | Status | Result | Evidence |
| --- | --- | --- | --- |
| 1. Two dealer colours, independent body/wing paint | **PASS** | Red and Blue purchases paint the body and wing independently. 0.0.2 red control: both silver/white. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S1 PNGs |
| 2. Daylight lamps and braking | **PASS** | Day rear 0 → 40000 → 0 when braking. 0.0.2 red control: constant emission. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S2 PNGs |
| 3. Dusk/night/dawn and daytime rain | **PASS / OPEN** | PASS: night, dawn/dusk, night braking 20000 → 40000 → 20000, rain on entry matches vanilla. OPEN: rain live-toggle lamp refresh. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md) |
| 4. Exit/re-enter, beams, two-car independence | **PASS / UNVERIFIED** | PASS: exit 0/0 with beams off, matching vanilla Mersaidi Dash; the two cars' paint stays independent. UNVERIFIED: the evidence does not separately record a night re-entry repeat or per-car lamp independence. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), `S2-after-road-night-exit-front.png` |
| 5. Save/reload and existing 0.0.2 car migration | **PASS** | Day and night reload keep both colours. Existing 0.0.2 cars repaint from their saved colour. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), S1-after-reload PNGs |
| 6. Both sides, hover, LOD, shader/decal appearance | **PASS / OPEN** | PASS in sampled observer views: no pink shader, giant glow, daylight emission, dirt or decal. Wheel finish is independent of paint (S3). OPEN: SKIPPED-LOCKED hover outline and native near/far camera LOD. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md) |
| 7. Launch, plumes, barrel roll, startup and errors | **PASS / OPEN** | PASS: startup 0.0.3, registration, dealer Active, 4 rear/2 down, no Roadster ERROR. Motors median 1.29 s; nitrogen 0.60–0.63 s. Right roll at 31 mph: 6.3 m peak, 360°, 2.7 m/s, 1°. Clean left roll at 23 mph with no contact: 6.3 m, 360°, 2.6 m/s, 2°. Stopped, creeping and held Backslash rejected. J stopped and J moving start no roll. N switches mode. OPEN: stopped-J Self Driving departure; SKIPPED-LOCKED stunt camera. | [31 Oct](reviews/rig/2026-10-31-pr1-0.0.3/README.md), [1 Nov](reviews/rig/2026-11-01-pr1-0.0.3-timing/README.md) |

From the earlier look-and-feel list, the subjective items (city driving feel, stutter, cornering feel) were SKIPPED-LOCKED in both sessions.

## Remaining native gaps

- [ ] **Stopped-J Self Driving departure.** J in a stopped Roadster enters HART. Self Driving 0.4.1 without a roll. Every attempt then cancelled while unparking or setting up the route. No sustained self-driven departure has been seen.
- [ ] **Rain live-toggle lamp refresh.** Turning rain on while already in the Roadster left lamps at 0/0 until re-entry or a time transition. Vanilla showed a similar lag when rain turned off. No pass is claimed.
- [ ] **SKIPPED-LOCKED: hover outline.**
- [ ] **SKIPPED-LOCKED: native near/far camera and LOD.**
- [ ] **SKIPPED-LOCKED: stunt camera comfort**, plus subjective stutter, handling and cornering feel.
- [ ] **Unverified: night re-entry repeat and two-car lamp independence** (item 4). Only paint independence is recorded.
- [ ] **Shipped bytes not run.** The rig has not installed the `05a27e42` zip, only `df262116`.
- [ ] **Build source commit of `05a27e42` unrecorded** (see above).

## Rig results (this run)

Pending. The rig step of this run adds its results here.

---

## Historical: 30 October preflight (superseded)

This preflight was blocked before launch. Its "all checks pending" status no longer holds; see the table above.

### RDSTR 0.0.3 PC rig acceptance preflight — 30 October 2026

Status: **blocked before launch**. No 0.0.3 in-game acceptance check was run. No red/green comparison, game screenshot, or 0.0.3 `Player.log` evidence exists from this session. All seven manual checks in `CHECKS.md` remain **pending**.

Session requested: Codex `gpt-6-sol`, high reasoning. This worker interface did not expose a provider-returned model ID or session UUID, so neither is asserted as observed metadata. `rig_used` and `in_game_verified` remain false.

Finding `Astra-r2-1` remains unresolved. PR #1 was converted to draft, with the GitHub response confirming `draft=true`. Merge and release/Workshop uploads must remain blocked until the required in-game proof is posted and reviewed.

#### Candidate identity

**31 October source update:** the recorded `8448179` preview below is **stale**, superseded by the issue #2 fix commit on top of `3579e2c` (`Fix barrel-roll key clash and require movement (Refs #2)`). The new source uses Backslash and requires speed above 2 m/s; the recorded archive has neither change. No rebuild was made for this fix. The scheduled Codex Sol/high rig session after 6 November must identify a fresh build from the superseding source commit and post before/red and after/green proof to PR #1 before merge/upload. The observations below remain the historical preflight record.

- Reviewed branch: `codex/rdstr-0.0.3`, HEAD `cc8700b3e20b762b1d4ed4ebfeb0a2d886adfcb5`.
- `docs/release-0.0.3.json` names build source `844817915a3999457f8a47fc81d210d47ad85582` and preview ZIP SHA-256 `e7d67a30679d66b3be914eac11891727f68236f8a50c88c3f038ad5e7c36bb88`. The recorded Windows bundle SHA-256 is `09421297873ddc427718483b0f30b8b708db0d76918ee54f62c1a71f2dc0bcd3`; `Roadster.dll` is `55bfd45f4cc068a84ff95e67af7a6bfd7214965067a3c7500bbc4bb04f618415`.
- The preview ZIP is absent from this worktree, the main Roadster checkout, and the sibling Big Ambitions project directories searched on this PC. This worktree also has no `build/` directory. Thus the recorded archive and its member hashes could not be checked against actual bytes or installed.
- HEAD has further build/check/document changes after the recorded build source. A successful test of the recorded preview would identify the `8448179` build, not by itself prove a build from HEAD.

#### Rig state observed, read only

- The isolated player exists at `C:\BigAmbitions-AgentTests`, with a separate profile at `%USERPROFILE%\AppData\LocalLow\Hovgaard Games\Big Ambitions Agent Tests`. A save directory exists, but no save was opened, copied, created, or changed.
- `run.json` names PID 7852, but that PID does not exist and no Big Ambitions process was running. The `agent1` lease file had no active owner. `C:\Users\Peter\game-lock.txt` did not exist. No rig or normal-game process was started or stopped.
- The isolated profile's `ModsLocal/Roadster/RELEASE-NOTES.txt` identifies the installed package as **0.0.2**. Its `Roadster.dll` SHA-256 is `4038398a492b69739a8e8118ca42783062c8f1bf8fd6c3d744a8a7fe898e86a5`; its Windows bundle SHA-256 is `15b5d09295670be7dcffe2abcbd18710d867f09babdbfde65379e11254c5304a`. These differ from the recorded 0.0.3 candidate.
- `python scripts/agent lock status`, `status`, and `health` from the rig checkout each failed with `ssh: Could not resolve hostname homepc: No such host is known.` That client targets an SSH alias rather than this local Windows host; it cannot drive the PC rig as configured in this session.
- The build script requires Unity 2022.3.62f2 and defaults to a macOS Unity path. The expected Windows Unity editor path `C:\Program Files\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe` was absent. The source checkout has no game DLLs or generated build output. No candidate was rebuilt.

#### Manual acceptance disposition

| `CHECKS.md` item | Status | In-game evidence |
| --- | --- | --- |
| 1. Two dealer colours, independent body/wing paint | Pending | None |
| 2. Daylight lamps and braking | Pending | None |
| 3. Dusk/night/dawn and daytime rain | Pending | None |
| 4. Exit/re-enter, beams, two-car independence | Pending | None |
| 5. Save/reload and existing 0.0.2 car migration | Pending | None |
| 6. Both sides, hover, LOD, shader/decal appearance | Pending | None |
| 7. Launch, plumes, barrel roll, startup and errors | Pending | None |

The same applies to the earlier look, driving, stutter, cornering and log-line checks in `CHECKS.md`. The existing rig's 0.0.2 installation is neither a valid 0.0.3 green run nor an observed 0.0.3 red control.

#### Required to resume

Build a fresh candidate from the issue #2 fix source commit and record its source commit and SHA-256; the stale recorded preview can serve only as a before/red control. Make the rig client target this PC or use its supported local control path, then install into the isolated profile under its lease. Use a disposable `FT` save and record before/after package hashes, game log lines, screenshots, per-check observations (including the stopped/creeping/moving and Self Driving checks in `CHECKS.md`), and restoration of the prior rig package. The existing installation and saves were left untouched in this preflight.

#### Offline validation for this review attempt

The required foreground command `python -m pytest tests -q -p no:cacheprovider --deselect tests/test_package_release.py::PackageTests::test_symlink_refused_even_if_bytes_match` completed with **7 passed, 1 deselected**. This result supplies no in-game acceptance evidence. No background process was started by this attempt.

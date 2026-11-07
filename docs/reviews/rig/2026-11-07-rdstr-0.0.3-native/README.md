# RDSTR 0.0.3 remaining native checks — 7 November 2026

**Overall: FAIL for live rain-toggle refresh.** Clean left roll and stopped-J compatibility passed. Hover and native near/far visuals now passed; stunt camera remains **SKIPPED** because the installed rig cannot combine native captures with keyboard input. These are observed running-game results, not source-reading checks.

Task `rdstr-0.0.3-records-1107`, branch `harness/rdstr-0.0.3-records-1107`, HEAD `ba548cbc70d4f7ba6895b520e293b0a8fe13a3d7`. Configured harness role: **Codex gpt-6.1-sol / high / PC**; the provider-returned model identifier is not independently exposed. [Session/helper provenance](session.json).

## Results and direct proof

| Requested item | Result | Evidence |
| --- | --- | --- |
| 1. Moving Backslash, clean left barrel roll | **PASS, checked in game.** Key sample **10.275 m/s**, native start **23 mph left**, peak **6.3 m**, **360°**, touchdown **2.6 m/s**, **2°** off level, **2.62 s** airborne. No recorded contacts during this trial; damage **0.1728198 → 0.1728198**. | [Before/corridor](images/left-2-before.png), [mid-air](images/left-2-air.png), [landed](images/left-2-landed.png); Player-windowed.log **337, 340, 343**; [full input/contact record](left-roll.json), [samples](left-roll-samples.csv). |
| 2. Stopped Roadster + default J | **PASS, checked in game.** Input logged at **0.0 m/s**. Self Driving engaged, logged `Departed (NWH)`, sustained departure and driving, then `Complete (arrived)`. No barrel-roll start in the J span. | [Open road ahead](images/J-before.png), [at destination](images/J-after-25s.png); Player-windowed.log **348, 365–373, 514–515**; [measurements](J-departure.json), [samples](J-departure-samples.csv). |
| 3. Live rain on/off while remaining in the vehicle | **FAIL for refresh; PASS for vanilla parity.** Both vehicles retained stale lamp strengths through at least **10 s unpaused** after each toggle. Re-entry refreshed both. This is not evidence of a Roadster-specific regression. | [Rain matrix](rain-results.json), screenshots below; Player-windowed.log observation labels indexed in [player-log-index.json](player-log-index.json). |
| 4. Hover / native near-far / stunt camera | **PARTIAL.** Hover outline + tooltip **PASS**; native wheel zoom near/far visual/LOD check **PASS** within the sampled native zoom range. **Stunt camera SKIPPED**: background mode has no `Keyboard.current`, including during an active virtual mouse interaction; windowed mode has keyboard input but its native captures are black. | [Hover before](images/native-hover-before.png), [after](images/native-hover-after.png), [detail](images/native-hover-detail.png); [near](images/native-zoom-near.png), [far](images/native-zoom-far.png), [return](images/native-zoom-return.png); [capture/camera/input records](camera-evidence.json), Player-background.log observation labels in the line index. |

Native roll excerpt, Player-windowed.log 337/340:

```text
[Mod:Roadster] Barrel roll to the left at 23 mph.
[Mod:Roadster] Barrel roll landed: peak 6.3 m, rolled 360 degrees, touchdown 2.6 m/s, 2 degrees off level, 2.62 s in the air.
```

Native J excerpt, Player-windowed.log 365/370/514:

```text
[Mod:DrivenRides] Own car: driving itself (roadster:vehicletype_roadster, wheelbase 2.79 m).
[Mod:DrivenRides] Departed (NWH): 613 waypoints, 3138 m, top 320 km/h, light cycle 8 s.
[Mod:DrivenRides] Ride ending: Complete (arrived), 78.6 game minutes so far.
```

The J sampling interval was **26.32 real seconds / 67.42 simulation seconds**. Sampled travel was **788.57 m excluding** the native Self Driving bridge jump (**1418.92 m**). Self Driving uses trip time acceleration and a bridge skip; the plan's 3138 m is not claimed as continuously physically driven. A traffic truck approached from behind and produced low-speed contact samples at the stopped start; the road ahead was open, and those contacts are retained in J-departure.json. The accepted roll's contact-free requirement is a separate result.

### Rain finding

All rows were captured with the player still controlling the named vehicle. Values are native body-renderer **front/tail shader strengths**, read without assigning lamp state. `ShouldLightsBeOn` changed with native rain state immediately.

| State | ShouldLightsBeOn | Roadster front/tail | Mersaidi Dash front/tail |
| --- | --- | --- | --- |
| Clear baseline after entry | false | 0 / 0 | 0 / 0 |
| Rain on, immediate / 2 s / 10 s | true | 0 / 0 | 0 / 0 |
| Exit/re-enter in rain | true | 50000 / 20000 | 50000 / 20000 |
| Rain off, immediate / 2 s / 10 s | false | 50000 / 20000 | 50000 / 20000 |
| Exit/re-enter in clear weather | false | 0 / 0 | 0 / 0 |

Roadster: [clear baseline](images/roadster-baseline-clear.png), [rain-on stale](images/roadster-rain-on-10s.png), [rain re-entry refreshed](images/roadster-rain-reentry.png), [rain-off stale](images/roadster-rain-off-10s.png).

Mersaidi Dash: [clear baseline](images/vanilla-retest-baseline-clear.png), [rain-on stale](images/vanilla-retest-rain-on-10s.png), [rain re-entry refreshed](images/vanilla-retest-rain-reentry.png), [rain-off stale](images/vanilla-retest-rain-off-10s.png).

Weather was changed through the installed rig's native `weather set` operation and restored with `weather clear`. Its before/after native rain schedule and intensity are in rain-results.json. This bounded instant-toggle test does not establish natural-rain onset/cessation timing.

### Native camera limits

The installed `capture start/status` returned readable **combined native camera + HUD** PNGs in background mode using `render_texture` (`ops_view_capture_background`). The camera override stayed **inactive**: native wheel events moved camera height from **11.70 m to 24.98 m**, then back near. Body/wing/wheel silhouettes stayed rendered without a sampled missing/pink material or disappearance. No numerical LOD index or transition outside that native zoom range is asserted. The hover image shows the native outline and `Roadster / CLICK TO DRIVE` tooltip; no outline was assigned by the helper.

The attempted background stunt input had `Keyboard.current == null`, so no actual Backslash event/roll start was delivered. A second availability check during virtual mouse interaction also returned null and stopped before another roll attempt. These are rig limitations, not failed Roadster key handling. [Windowed native capture failure](images/windowed-native-black.png) is retained as a small black PNG. Subjective camera comfort and smoothness remain unverified; capture overhead is not a performance benchmark.

## Package, rig and method

Used the **shipped** `Roadster-0.0.3-preview.zip` at the path recorded in [docs/release-0.0.3.json](../../../release-0.0.3.json). Archive SHA-256 **`05a27e4271cccc408914367a7aadd4059c9c00bb6709bc33c88c8ca5b5439ccd`**, all recorded member hashes and ZIP CRC verified before installation. **No Roadster rebuild.** The archive's exact build-source commit remains unverified as already recorded; this test identifies the actual shipped bytes. [Package verification](package-verification.json).

Self Driving **0.4.2**, copied read-only from Workshop item **3819853552** into agent1, DLL SHA-256 **`4c52d5d14867f84beee3b36ed97a3688370c8a48f21709fc55945b441bdc2d67`**. J/K bindings were not changed. All **8 source package files** rehashed unchanged afterward. [Hashes](self-driving-hashes.json).

Used the existing isolated game build **3682**, runtime **7**, `C:/BigAmbitions-AgentTests`, port **18330**, disposable `FT RDSTR Rig…` saves. The helper used native placement/entry/pinned-destination fixture APIs, ordinary NWH throttle/steering setup and Input System KeyboardState events. It observed collision callbacks, positions and native material properties; it assigned neither roll state nor lamp state. Runtime/receipt identity and hashes passed after city load. [Loaded selfcheck](selfcheck-loaded.json), [background selfcheck](selfcheck-background.json). The first startup selfcheck saw pending coverage; the loaded checks passed and the final normal selfcheck resolved the alerts.

Invalid setup attempts remain in the raw logs: initial braking setup moved into traffic before the accepted rolls; existing damage was retained and did not increase in either accepted roll. The first roll's air screenshot request had an invalid frame count, so the contact-free roll was repeated with valid capture settings. An initial vanilla rain fixture overlapped the parked Roadster and was stopped/discarded; **only `vanilla-retest-*` observations**, with cars separated by 17 m, support the matrix. No production fix was made.

## Restoration and artifacts

Waited for owner `edit-po-prototype-review-rig-20261107`; acquired the free lease as `rdstr-0.0.3-records-1107` at **07:52:21 UTC**, with no takeover. [Wait/acquisition log](lease-wait.jsonl).

Restored and verified at **08:13:10 UTC**: **5094 profile files**, **110 receipt references**, original preferences, installation receipt, run record and previous Player-agent.log. Preference SHA-256 **`e0c444650dee7df90e3557409fd5d2666b54c2867c455268b5d2c57f8da333eb`**; original installation receipt **`9a25d9bb1759a3e63b734b6e924c668bb8d241a80a48ac2cdb8fc09ff26b20e9`**. The isolated player quit natively. Mouse/camera were released and simulation paused first. [Lifecycle](lifecycle.json), [restore receipt](restore-receipt.json).

The lease was released; the next queued owner `cp1-sync-native-1107b` acquired it at **08:13:54 UTC**. A subsequent read-only status confirms that handoff; no control was attempted afterward. Release succeeded before a receipt-encoding verification error, which was corrected by read-only verification. [Release/handoff receipt](release-receipt.json).

Raw [Player-windowed.log](logs/Player-windowed.log), [Player-background.log](logs/Player-background.log), [short native excerpts](logs/native-excerpts.txt), [line index](player-log-index.json), and [machine-readable verdicts](results.json) accompany the PNGs. Observer-camera images prove roll/lamp observations only; native-camera acceptance uses the distinct `native-*` PNGs. Images are real game captures, resized to at most **800 px** width (plus an unscaled hover crop); no AI imagery or repainting. [Original/published hashes and exact transforms](screenshots-manifest.json). Full originals, exercised profile, private helper and backups remain locally at `C:\Users\Peter\HART-Builds\rdstr-0.0.3-native-20261107`.

Only new evidence files were added here. No tracked file was modified, and no commit, push, merge or PR comment was made. Game/mod DLLs, saves, credentials and private game references are excluded.

# RDSTR 0.0.3 PC rig acceptance preflight — 30 October 2026

Status: **blocked before launch**. No 0.0.3 in-game acceptance check was run. No red/green comparison, game screenshot, or 0.0.3 `Player.log` evidence exists from this session. All seven manual checks in `CHECKS.md` remain **pending**.

Session requested: Codex `gpt-6-sol`, high reasoning. This worker interface did not expose a provider-returned model ID or session UUID, so neither is asserted as observed metadata. `rig_used` and `in_game_verified` remain false.

Finding `Astra-r2-1` remains unresolved. PR #1 was converted to draft, with the GitHub response confirming `draft=true`. Merge and release/Workshop uploads must remain blocked until the required in-game proof is posted and reviewed.

## Candidate identity

- Reviewed branch: `codex/rdstr-0.0.3`, HEAD `cc8700b3e20b762b1d4ed4ebfeb0a2d886adfcb5`.
- `docs/release-0.0.3.json` names build source `844817915a3999457f8a47fc81d210d47ad85582` and preview ZIP SHA-256 `e7d67a30679d66b3be914eac11891727f68236f8a50c88c3f038ad5e7c36bb88`. The recorded Windows bundle SHA-256 is `09421297873ddc427718483b0f30b8b708db0d76918ee54f62c1a71f2dc0bcd3`; `Roadster.dll` is `55bfd45f4cc068a84ff95e67af7a6bfd7214965067a3c7500bbc4bb04f618415`.
- The preview ZIP is absent from this worktree, the main Roadster checkout, and the sibling Big Ambitions project directories searched on this PC. This worktree also has no `build/` directory. Thus the recorded archive and its member hashes could not be checked against actual bytes or installed.
- HEAD has further build/check/document changes after the recorded build source. A successful test of the recorded preview would identify the `8448179` build, not by itself prove a build from HEAD.

## Rig state observed, read only

- The isolated player exists at `C:\BigAmbitions-AgentTests`, with a separate profile at `%USERPROFILE%\AppData\LocalLow\Hovgaard Games\Big Ambitions Agent Tests`. A save directory exists, but no save was opened, copied, created, or changed.
- `run.json` names PID 7852, but that PID does not exist and no Big Ambitions process was running. The `agent1` lease file had no active owner. `C:\Users\Peter\game-lock.txt` did not exist. No rig or normal-game process was started or stopped.
- The isolated profile's `ModsLocal/Roadster/RELEASE-NOTES.txt` identifies the installed package as **0.0.2**. Its `Roadster.dll` SHA-256 is `4038398a492b69739a8e8118ca42783062c8f1bf8fd6c3d744a8a7fe898e86a5`; its Windows bundle SHA-256 is `15b5d09295670be7dcffe2abcbd18710d867f09babdbfde65379e11254c5304a`. These differ from the recorded 0.0.3 candidate.
- `python scripts/agent lock status`, `status`, and `health` from the rig checkout each failed with `ssh: Could not resolve hostname homepc: No such host is known.` That client targets an SSH alias rather than this local Windows host; it cannot drive the PC rig as configured in this session.
- The build script requires Unity 2022.3.62f2 and defaults to a macOS Unity path. The expected Windows Unity editor path `C:\Program Files\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe` was absent. The source checkout has no game DLLs or generated build output. No candidate was rebuilt.

## Manual acceptance disposition

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

## Required to resume

Provide the recorded candidate archive bytes (or build a fresh candidate and record its source commit and SHA-256), make the rig client target this PC or use its supported local control path, then install into the isolated profile under its lease. Use a disposable `FT` save and record before/after package hashes, game log lines, screenshots, per-check observations, and restoration of the prior rig package. The existing installation and saves were left untouched in this preflight.

## Offline validation for this review attempt

The required foreground command `python -m pytest tests -q -p no:cacheprovider --deselect tests/test_package_release.py::PackageTests::test_symlink_refused_even_if_bytes_match` completed with **7 passed, 1 deselected**. This result supplies no in-game acceptance evidence. No background process was started by this attempt.

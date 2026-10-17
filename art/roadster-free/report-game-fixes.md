Fixed and saved [Roadster-game.blend](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/Roadster-game.blend), re-exported the [FBX](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/Roadster-game.fbx) and [metadata](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/game-export.json) with the same settings. `Roadster.blend` is untouched.

- Added a solid Black apron closing the splitter gap.
- Rebuilt the body-only collision hull: **230 triangles**, closed and convex. Lowest point: **≈0 → 0.150000 m**.
- Opened the arches and liners without moving or shrinking the wheels. All seven names and origins remain unchanged.

Maximum tested overlap counts:

| Wheel | Before | After |
|---|---:|---:|
| FL | 1,510 | **0** |
| FR | 1,507 | **0** |
| RL | 1,690 | **0** |
| RR | 1,692 | **0** |

All 32 required poses, 16 neutral-height checks and **720 dense poses** passed. Full per-pose counts are in the [report](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/fix-1-report.txt).

Renders: [front three-quarter](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/renders/game/fix-1-after-front-quarter.png), [nose top view](/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free/renders/game/fix-1-after-nose-top.png). Neutral arch gaps are necessarily larger. These fixes still need an in-game drive check.
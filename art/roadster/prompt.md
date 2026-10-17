# Task: model a two-seat electric hypercar for a Big Ambitions mod

You are driving a running Blender 5.2 instance through the `blender` MCP server (`execute_blender_code`, scene summaries, screenshots, viewport and thumbnail renders, API and manual search). Work on your own until the task is finished; nobody will answer questions during the run.

The asset is a drivable car in the PC game Big Ambitions (Unity 2022.3, HDRP, New York setting). It replaces the mesh of the game's example car inside the same vehicle prefab, so its size, wheel positions and pivots are fixed and must match the numbers below exactly. The game's cars are clean low-poly shapes with flat colours and simple painted details, not photoreal sculpts. Neutral art: no text, logos, badges, brand names, licence plate numbers or flags anywhere.

## Coordinates (read carefully)

Blender units are metres, Z up. **The car's front faces −Y. Its left (driver's) side is +X, its right side −X.** This is what the FBX settings below turn into Unity's forward (+Z) and right (+X); it was measured in Unity. Do not build it facing +Y.

The origin (0, 0, 0) is on the ground, halfway between the front and rear axles, on the centre line.

## The car

A low, wide, two-seat electric hypercar coupe, inspired by the next-generation electric roadster revealed on 15 October 2026. No reference images are available, so design from this description:

- **Shape.** Sharp and angular, not rounded: a long, low nose that rises in one straight wedge to a steeply raked windscreen; a short cabin set slightly forward of centre; a fastback roof that falls to a cut-off (Kamm) tail. Crisp creases along the sides, flat facets rather than bubbles. Think of a stealth-fighter version of a classic wedge supercar.
- **Cabin.** Fixed roof (coupe). Large wraparound glass: windscreen, side windows and a glass roof panel, all gold-tinted.
- **Doors.** One large door per side, hinged at the front pillar and opening upwards and forwards ("dihedral"). In the model they are closed and part of the body; show them only as clean panel lines.
- **Front.** Concealed headlights: a thin, sharp light strip across the front edge of the nose on each side, no round lamps. A wide, low intake below.
- **Rear.** One continuous red light bar across the full width of the tail. Two small reverse lights in the lower rear. A large rear diffuser with **ten small round cold-gas thruster nozzles**: six in a row across the diffuser and one low at each of the four corners of the car (two at the front bumper corners, two at the rear). The nozzles are dark metal rings with a black centre.
- **Spoiler.** A separate active rear wing (`Roadster_Spoiler`) lying flush in the rear deck when closed, hinged along its front edge so it tilts up at the back to deploy.
- **Underbody.** Two round fan grilles in the flat floor, between the axles, each about 0.45 m across. Visible only from below.
- **Wheels.** Large aero wheels: a flat, turbine-style disc with a few angular cut-outs, titanium-grey, with a low-profile dark tyre.
- **Colours.** Body paint pearl white ("Ano White"). Dark titanium accents on the sills, diffuser and wing supports. Gold-tinted dark glass. Black trim.

## Size and layout (Blender coordinates)

- **Overall**: 4.50 m long (Y from −2.25 at the nose to +2.25 at the tail), 2.00 m wide across the body (X from −1.00 to +1.00; mirrors or camera stalks may stick out to ±1.08), 1.15 m high at the roof. Ground clearance under the floor about 0.11 m.
- **Wheels**: four wheels, 0.70 m diameter, 0.28 m wide, axle along X. Hubs at:
  - front left (+0.85, −1.35, 0.35), front right (−0.85, −1.35, 0.35)
  - rear left (+0.85, +1.35, 0.35), rear right (−0.85, +1.35, 0.35)
- **Wheel arches**: the body must leave each wheel room to steer and bounce: no body geometry within 0.40 m of the hub along Y, below z = 0.76, between |x| = 0.705 and 0.995 on either side.
- **Spoiler**: about 1.40 m wide, 0.30 m deep, 0.04 m thick; closed it sits in a recess in the rear deck. Its hinge line runs along X at y = +2.05, z = 1.00, the spoiler's front edge. Rotating it about that line lifts its rear edge (+Y side) upwards. The rear deck must have surface at the hinge point (0, 2.05, 1.00).
- **Lights**: headlight strips (front), the tail light bar (rear), reverse lights (rear), and amber blinkers at the four corners (they can be short sections at the ends of the front strips and the tail bar). Each light is its own faces with its own UV island so the emission masks below can light it. The ten thruster nozzle centres also get their own UV islands.
- **Charge port**: a small flush flap on the left (+X) rear quarter near (+1.00, +1.75, 0.80).

## Spec

- At most 9,500 triangles for all visible objects together: `Roadster_Body` at most 7,200, each wheel at most 500, the spoiler at most 300. The collision mesh doesn't count. Spend triangles on the silhouette, not hidden faces.
- Real size in metres. Rotation 0 and scale 1 applied on every object.
- Objects, with these exact names and origins:
  - `Roadster_Body`: everything except the wheels and the spoiler. Origin at (0, 0, 0).
  - `Roadster_Wheel_FL`, `Roadster_Wheel_FR`, `Roadster_Wheel_RL`, `Roadster_Wheel_RR`: one object per wheel, origin exactly at its hub (positions above). L is the +X side.
  - `Roadster_Spoiler`: origin on its hinge line at (0, 2.05, 1.00).
  - `Roadster_Collision`: a convex collision hull of the whole car (body and wheels, without mirrors), at most 150 triangles. Build it with `bmesh.ops.convex_hull` so it is strictly convex. Hide it from renders.
- **One material** shared by all visible objects, with **two UV maps** on every visible object: the first (`UVMap`) for all textures below, the second (`UV2`) a non-overlapping layout inside 0–1 used by the game for dirt (it may be a copy of the first). Both without overlaps, inside 0–1, and packed so that at least 40% of the texture is covered (check with the scorer).
- **Textures**, all 2048 × 2048 PNG in the output folder, all in the first UV map. They are made for the game's vehicle shader, which takes the same set as the game's example car:
  - `T_Roadster_D.png`: base colour in RGB; alpha 1 on the painted body panels and 0 elsewhere (the game repaints alpha-1 areas in the colour the player picks).
  - `T_Roadster_MaskMap.png`: R metallic (1 on titanium and nozzle metal, 0 elsewhere), G ambient occlusion (1 by default, darker in recesses if you want), B 0, A smoothness (about 0.7 paint, 0.9 glass, 0.5 titanium, 0.2 rubber).
  - `T_Roadster_N.png`: a flat normal map, RGB (128, 128, 255).
  - `T_Roadster_E.png`: emission colour: cool white on headlights and reverse lights, red on the tail bar, amber on blinkers, pale blue on the ten nozzle centres, black elsewhere.
  - `T_Roadster_EM_1.png`: emission masks, R = headlights, G = tail/brake light bar, B = reverse lights; 1 on the light, 0 elsewhere.
  - `T_Roadster_EM_2.png`: R = right (−X) blinkers, G = left (+X) blinkers, B = the ten thruster nozzle centres.
  In the Blender material, connect only the base colour (and, if you like, emission for the renders); the other maps are for the game.
- Clean geometry: no loose vertices or edges, no flipped normals, no n-gons, closed parts where the shape allows.
- Export `Roadster.fbx` with exactly these settings (checked in Unity 2022.3; with them Blender −Y becomes Unity +Z, scale 1 and rotation 0):

  ```python
  bpy.ops.export_scene.fbx(filepath=OUT + "/Roadster.fbx", use_selection=True, object_types={"MESH"},
      global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
      axis_forward="-Z", axis_up="Y", bake_space_transform=True, use_space_transform=True,
      mesh_smooth_type="OFF", use_triangles=True, use_tspace=True, bake_anim=False,
      add_leaf_bones=False, path_mode="RELATIVE", embed_textures=False)
  ```

  with only the seven objects selected.
- Save the scene as `Roadster.blend` in the output folder. Keep it under 20 MB (don't pack the images).

## Starting point

Blender has `start.blend` open: metric units and a wireframe box `HumanRef_1.8m` (a 1.8 m person for scale; leave it alone, it isn't rendered or exported). Don't open other files, and don't write outside the output folder.

## Checking your work

A scorer measures the result against this spec. Run it after exporting, read every failure, fix it, export again and rerun until it prints `SCORE PASS`. Start it from the running Blender with `execute_blender_code`, as a separate background Blender process, because a `blender -b` started from your shell sandbox crashes while probing the GPU:

```python
import subprocess
p = subprocess.run(["/Applications/Blender.app/Contents/MacOS/Blender", "-b", OUT + "/Roadster.blend",
    "--python", "{REPO}/art/tools/score.py",
    "--", OUT + "/spec.json"], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
result = {"exit": p.returncode, "log": p.stdout[-4000:]}
```

It writes `score.json` in the output folder. Do not edit the scorer or `spec.json`.

Passing the scorer is the floor, not the goal. The car has to read at a glance as a sharp, low, wedge-shaped hypercar from the game's usual camera: behind and above the car, and from the street at eye height. Render it from those angles and from front three-quarter, side and rear, and fix anything that looks blobby, boxy or toy-like.

## Output folder

`{OUT}`

Put everything there. After each major step (blockout, detail, UVs and textures, final), save a viewport screenshot or render to `{OUT}/renders/` named `01-blockout.png`, `02-detail.png` and so on, and look at it before moving on. End with `renders/review-sheet.png`: one image with front three-quarter, rear three-quarter, side, top and the high chase-camera view. Save the build code you used as `{OUT}/build_roadster.py` so the model can be regenerated.

## Finish

End with a short report: what you built, triangles per object, the final scorer result, and anything in the spec you could not meet and why.

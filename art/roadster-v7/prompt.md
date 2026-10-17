# Task: front-crown correction pass on a high-fidelity model of a two-seat electric hypercar, as close to the reveal photos as you can make it

You are driving a running Blender 5.2 instance through the `blender` MCP server (`execute_blender_code`, scene summaries, screenshots, viewport and thumbnail renders, API and manual search). Work on your own until the task is finished; nobody will answer questions during the run. Take as long as the quality needs: a two-hour run that looks like the car beats a fast one that doesn't.

The asset is the player's hero car in the PC game Big Ambitions (Unity 2022.3, HDRP, New York setting). It replaces the mesh of the game's example car inside the same vehicle prefab, so its wheel positions and pivots are fixed and must match the numbers below exactly. Unlike the game's own low-poly cars, this one is meant to be as close to the real car as possible: true surfaces, crisp creases, real panel gaps, modelled lights, nozzles, fans and wheels. Neutral art: no text, logos, badges, brand names, licence plate lettering or flags anywhere (leave the plate recess blank).

Pass 6 fixed the rear half of the side view. One large error is left: the front fender crowns stand far too high. Fixing it is this pass's whole job. Keep everything else as it is. The review below is the job.

## Coordinates (read carefully)

Blender units are metres, Z up. **The car's front faces −Y. Its left (driver's) side is +X, its right side −X.** This is what the FBX settings below turn into Unity's forward (+Z) and right (+X); it was measured in Unity. Do not build it facing +Y.

The origin (0, 0, 0) is on the ground, halfway between the front and rear axles, on the centre line.

## Reference

Eight reveal photos are attached and are also in `{REPO}/art/reference/` (private reference only; never copy their plate or any lettering):

- `01-front.jpg`: straight front, studio.
- `02-rear.jpg`: straight rear, studio, from slightly above.
- `03-rear-wing.jpg`: rear three-quarter on stage, wing raised.
- `04-doors.jpg`: rear three-quarter, both doors open.
- `05-hero.jpg`: near side view, driving, with a vapour trail from the rear.
- `06-carscoops-a.jpg`: front, airborne on thrusters.
- `07-carscoops-b.jpg`: small, in flight over trucks.
- `08-jets.jpg`: two rear views, one inverted (underside and diffuser) and one with downward jets.

You may load them into Blender as reference images (empties or camera backgrounds) while you work; keep them out of the export and delete them before saving the final file, or keep them in a collection that is excluded from the view layer.

What the photos show, as a checklist to match:

- **Side profile** (`05`): one long straight wedge from a sharp, low nose up a raked windscreen into a long, low dark-glass canopy that runs back over the cabin, then a short rear deck and a high cut-off tail. A crisp horizontal crease along the flank. A black lower sill band, thin at the front wheel, that rises steeply behind the door towards the rear wheel, so the rear quarter is black below and white above. A small vertical air outlet behind the front wheel. Short overhangs.
- **Front** (`01`, `06`): a flat central hood panel framed by two raised, sharply faceted front fender peaks. Small triangular headlight slits where each fender peak meets the hood, with LED segments inside. A thin light line across the full front edge of the hood. Below it a wide, dark, rectangular lower intake and a thin dark splitter. The windscreen and roof glass are one continuous brown-gold tinted canopy, outlined by a thin bright edge.
- **Rear** (`02`, `03`, `04`, `08`): a high tail with one full-width red light bar along its top edge, slightly inset under an overhanging lip. Below it a smooth white tail panel with a blank plate recess and two small reverse lights. Under that a large black diffuser box: four round bronze thruster nozzles in a row across its top, and below them four square bays, each holding a round fan with a turbine hub. Vertical diffuser strakes at the outer edges.
- **Thrusters**: ten in all. The four bronze ones in the diffuser, two short nozzles pointing straight down just inside the rear wheels (`08`), two pointing down inside the front wheels, and two small ones low at the front bumper corners (`06`). Bronze rings with a dark throat; give each throat its own faces.
- **Wing** (`03`, `08`): a wide, thin, bronze-gold wing blade with angular downturned end plates, on two slim swan-neck supports that attach to the top of the blade. In the model it is the closed position: blade folded flat into a recess in the rear deck, supports folded under it. The hinge spec below raises it.
- **Doors** (`04`): dihedral doors with angular frameless glass. Closed and part of the body; show them with real panel gaps (about 4 mm, modelled as small inset grooves).
- **Wheels** (`03`, `04`): large wheels with five sharp twin spokes forming a star, dark titanium with machined silver edges, red-painted inner barrels on some photos (use dark grey), low-profile tyres with a rounded sidewall, a brake disc and caliper visible behind the spokes.
- **Colours**: body pearl white. Lower sills, diffuser box, front intake and splitter black. Wing and nozzle rings bronze-gold metal. Glass very dark with a warm brown-gold tint.

## Review of pass 6 (what to fix)

Pass 6 is in `{REPO}/art/roadster-v6/` (`Roadster.blend`, `build_roadster.py`, `renders/overlay-side-final.png`, `report.txt`). In that side overlay (the `05-hero.jpg` frame, 1918 × 1080, about 0.39 m per 100 px), pass 6 still has a flat white crown over the front wheel whose top edge is at about y 415 from x 260 to 430. In the photo, the body top over the front wheel is at about y 470, falling to the nose top near (130, 530) and rising into the windscreen base near (300, 490). The crown is about 60 to 80 px (0.25 to 0.30 m) too high, and from behind it shows as two white ears beside the roof.

Pass 6's report says lowering it would enter the wheel-clearance volume. It would not: the clearance boxes stop at z = 0.80 m, and the photo's fender top over the wheel is at about z = 0.95 m. Lowering the crown top to about 0.95 m leaves 0.15 m above the clearance box for the arch and the fender skin.

1. Lower both front fender crowns so their top edge in the side overlay follows the photo: about y 470 over the wheel, down to (130, 530) at the nose, up into the windscreen base at (300, 490). In metres, the crown top should be about 0.95 m over the wheel centre and at most 1.00 m anywhere.
2. Keep the crowns' sharp faceted shape from the front: tapered blades whose top edges slope down and inwards to the headlight slits. They get lower, not rounder.
3. The front view will change. The front camera in pass 5 and 6 was matched with the crowns too high, so rematch it on the wheels, the track width and the windscreen base before judging the front overlay, and say in the report what changed.
4. From the rear camera, nothing may stand above the roof line beside the rear window. Check `overlay-rear` after the change.

## Method

Side camera first, as in pass 6: after every change render the 50% overlay as `renders/overlay-side-<n>.png` and write down the remaining gap at the crown, the nose top and the windscreen base, in pixels. At least four rounds, more while the gaps shrink. Then rematch and render the front overlay, and the rear and rear three-quarter overlays once each. In the report, give a table of the final gaps.

## Size and layout (Blender coordinates)

These were measured from the side and front photos and scaled to a 0.72 m tyre; keep them exact.

- **Overall**: 4.58 m long (Y from −2.35 at the nose to +2.23 at the tail), 2.00 m wide across the body (X from −1.00 to +1.00; mirrors or camera stalks may stick out to ±1.10), 1.15 m high at the roof. Ground clearance under the floor about 0.11 m.
- **Wheels**: four wheels, 0.72 m diameter, 0.30 m wide, axle along X. Hubs at:
  - front left (+0.84, −1.475, 0.36), front right (−0.84, −1.475, 0.36)
  - rear left (+0.84, +1.475, 0.36), rear right (−0.84, +1.475, 0.36)
  The brake disc and caliper belong to the wheel object, inside its 0.30 m width.
- **Wheel arches**: no body geometry within 0.42 m of a hub along Y, below z = 0.80, between |x| = 0.685 and 0.995 on either side, so the wheel can steer and bounce.
- **Wing**: blade about 1.80 m wide including its end plates, 0.30 m deep. Its hinge line runs along X at y = +1.90, z = 1.00, the blade's front edge. Rotating it about that line lifts its rear edge (+Y side) upwards. The rear deck must have surface at the hinge point (0, 1.90, 1.00).
- **Lights**: headlight slits and the front light line, the tail light bar, reverse lights, and amber blinkers at the four corners (they can be short sections at the ends of the front line and the tail bar). Each light is its own faces with its own UV island so the emission masks below can light it. The ten thruster throats also get their own UV islands.

## Spec

- Triangle budget: `Roadster_Body` at most 60,000, each wheel at most 5,000, the wing at most 3,000; at most 85,000 visible in total. The collision mesh doesn't count. Spend them where the eye goes: the silhouette, the creases, the canopy edge, the lights, the diffuser, the wheels.
- Model with whatever tools you like (subdivision, bevels, booleans, shrinkwrap), but apply every modifier before export and scoring: the scored meshes must be plain meshes with no n-gons (quads and triangles only), no loose geometry, consistent outward normals.
- **Shading**: smooth shading with sharp edges marked on the real creases (or Smooth by Angle around 30°) so curved panels read smooth and the folds stay crisp. Export the normals (see the FBX settings).
- Real size in metres. Rotation 0 and scale 1 applied on every object.
- Objects, with these exact names and origins:
  - `Roadster_Body`: everything except the wheels and the wing. Origin at (0, 0, 0).
  - `Roadster_Wheel_FL`, `Roadster_Wheel_FR`, `Roadster_Wheel_RL`, `Roadster_Wheel_RR`: one object per wheel (tyre, rim, disc, caliper), origin exactly at its hub. L is the +X side. The rims and spokes of the left and right wheels may mirror.
  - `Roadster_Spoiler`: the wing blade and its supports, origin on its hinge line at (0, 1.90, 1.00).
  - `Roadster_Collision`: a convex collision hull of the whole car (body and wheels, without mirrors), at most 250 triangles. Build it with `bmesh.ops.convex_hull` so it is strictly convex. Hide it from renders.
- **One material** shared by all visible objects, with **two UV maps** on every visible object: the first (`UVMap`) for all textures below, the second (`UV2`) a non-overlapping layout inside 0–1 used by the game for dirt (it may be a copy of the first). Both without overlaps, inside 0–1, at least 30% of the texture covered (the scorer checks).
- **Textures** in the output folder, all in the first UV map, for the game's vehicle shader:
  - `T_Roadster_D.png`, 4096 × 4096: base colour in RGB; alpha 1 on the white painted body panels and 0 elsewhere (the game repaints alpha-1 areas in the colour the player picks). Paint the panel gaps, the fine trim lines and the dark recesses into it so they hold up from the chase camera.
  - `T_Roadster_MaskMap.png`, 4096 × 4096: R metallic (1 on bronze, titanium, brake discs; 0 elsewhere), G ambient occlusion (bake it from the model: gaps, intakes, diffuser bays, wheel wells), B 0, A smoothness (about 0.8 paint, 0.95 glass, 0.6 bronze, 0.5 titanium, 0.2 rubber, 0.3 black plastics).
  - `T_Roadster_N.png`, 4096 × 4096: a tangent-space normal map. Flat (128, 128, 255) is acceptable; baked fine detail (tyre sidewall, grilles, fan blades) is better if you have time.
  - `T_Roadster_E.png`, 2048 × 2048: emission colour: cool white on headlights, the front light line and reverse lights, red on the tail bar, amber on blinkers, pale blue on the ten thruster throats, black elsewhere.
  - `T_Roadster_EM_1.png`, 2048 × 2048: emission masks, R = headlights and front light line, G = tail/brake light bar, B = reverse lights; 1 on the light, 0 elsewhere.
  - `T_Roadster_EM_2.png`, 2048 × 2048: R = right (−X) blinkers, G = left (+X) blinkers, B = the ten thruster throats.
  In the Blender material, connect the base colour, metallic, roughness and normal so your renders show the real look; the masks are for the game.
- Export `Roadster.fbx` with exactly these settings (checked in Unity 2022.3; with them Blender −Y becomes Unity +Z, scale 1 and rotation 0):

  ```python
  bpy.ops.export_scene.fbx(filepath=OUT + "/Roadster.fbx", use_selection=True, object_types={"MESH"},
      global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
      axis_forward="-Z", axis_up="Y", bake_space_transform=True, use_space_transform=True,
      mesh_smooth_type="FACE", use_triangles=True, use_tspace=True, bake_anim=False,
      add_leaf_bones=False, path_mode="RELATIVE", embed_textures=False)
  ```

  with only the seven objects selected.
- Save the scene as `Roadster.blend` in the output folder. Keep it under 80 MB (don't pack the images).

## Starting point

Open `{REPO}/art/roadster-v6/Roadster.blend` (`bpy.ops.wm.open_mainfile`) and work from it. Save everything into the output folder below, never into `art/roadster-v6`. Write only into the output folder.

## Checking your work

A scorer measures the result against this spec. Run it after exporting, read every failure, fix it, export again and rerun until it prints `SCORE PASS`. Start it from the running Blender with `execute_blender_code`, as a separate background Blender process, because a `blender -b` started from your shell sandbox crashes while probing the GPU:

```python
import subprocess
p = subprocess.run(["/Applications/Blender.app/Contents/MacOS/Blender", "-b", OUT + "/Roadster.blend",
    "--python", "{REPO}/art/tools/score.py",
    "--", OUT + "/spec.json"], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
result = {"exit": p.returncode, "log": p.stdout[-4000:]}
```

It writes `score.json` in the output folder. Do not edit the scorer or `spec.json`.

Passing the scorer is the floor. The real test is likeness. At least three times during the build (after the blockout, after the detail pass and at the end), render your model from the same angles as `01-front.jpg`, `02-rear.jpg`, `03-rear-wing.jpg` and `05-hero.jpg`, put each next to its photo, write down every difference you see in proportion, silhouette, crease placement, light shapes and colour, and fix them before moving on. Render in Eevee with soft studio lighting so the surfaces read.

## Output folder

`{OUT}`

Put everything there. Save the renders in `{OUT}/renders/`: `01-blockout.png`, `02-detail.png` and so on, and `compare-1.png`, `compare-2.png`, `compare-final.png` (each a sheet of render next to photo for the four angles). End with `renders/review-sheet.png`: front three-quarter, rear three-quarter, side, top, and the game's chase camera (behind and above). Save the build code you used as `{OUT}/build_roadster.py` so the model can be regenerated.

## Finish

End with a short report: what you built, triangles per object, the final scorer result, the remaining differences from the photos you could not fix, and anything in the spec you could not meet and why.

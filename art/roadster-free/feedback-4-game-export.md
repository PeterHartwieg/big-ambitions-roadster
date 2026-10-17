Round 4 is approved. Now make a game version of it for Big Ambitions (Unity 2022.3, HDRP). The look must stay as close to round 4 as possible; this is a technical conversion, not a redesign.

Work on a copy: open `Roadster.blend`, then immediately save as `Roadster-game.blend` in the same folder, and never save over `Roadster.blend`.

**What the game needs**

1. **Pose and clean-up.** Wing stowed (frame 1). Delete the studio floor, lights and cameras. Delete the interior (it is invisible behind the tinted glass in the game, which renders glass opaque) and every part that can't be seen from outside the car: inner chassis, inspection helpers, hidden fasteners. Delete parts smaller than about 2 cm that only add triangles (lug bolts, brake pistons, rotor cooling channels and the like). Delete the brake calipers: the game spins and steers the whole wheel object, so a caliper inside it would spin.
2. **Apply every modifier**, then join everything into exactly these seven objects, with rotation 0 and scale 1 applied:
   - `Roadster_Body`: all static parts (body, glass, lights, lower band, rear propulsion, fans, nozzles). Origin at (0, 0, 0).
   - `Roadster_Wheel_FL`, `Roadster_Wheel_FR`, `Roadster_Wheel_RL`, `Roadster_Wheel_RR`: one per wheel (tyre, rim, inserts, hub, brake disc). Origin exactly at its hub, the current wheel empties' positions. **Name them by position, not by the current names:** F = the −Y axle, R = the +Y axle, L = the **+X** side, R = the **−X** side. (The game maps Blender +X to the car's left.)
   - `Roadster_Wing`: blade, end plates and the moving links, in the stowed pose. Origin on its hinge axis.
   - `Roadster_Collision`: a strictly convex hull of the whole car with wheels and without the wing, at most 250 triangles (`bmesh.ops.convex_hull`), hidden from renders.
3. **Triangles:** at most 150,000 visible in total: body at most 110,000, each wheel at most 7,000, the wing at most 6,000. Reduce the dense parts (decimate, rebuild with fewer segments) while keeping the silhouette, the creases and the details that read from a few metres away. Render the same four views before and after (front three-quarter, side, rear, rear three-quarter) and fix anything that visibly changed.
4. **Materials.** Unity only gets flat values, so replace each procedural material with plain Principled values (base colour, metallic, roughness, emission for lights) that look as close as possible, and merge similar ones down to at most 12 materials. Name the white body paint material exactly `Paint`, the glass `Glass`, the red tail light `TailLight`, the front light strips and headlamps `HeadLight`, the amber marker lights `Indicator`, and the bronze nozzles `Bronze`. Keep other names short ASCII (no bullets or special characters).
5. **Shading:** keep smooth shading with sharp edges on the creases (weighted normals are fine), so the exported normals carry the look.
6. **UVs:** one UV map called `UVMap` on every visible object (Smart UV Project is enough; the materials are untextured).
7. **Export** `Roadster-game.fbx` in this folder, with only the seven objects selected and exactly these settings (checked in Unity: Blender −Y becomes Unity forward, scale 1, rotation 0):

   ```python
   bpy.ops.export_scene.fbx(filepath=OUT + "/Roadster-game.fbx", use_selection=True, object_types={"MESH"},
       global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
       axis_forward="-Z", axis_up="Y", bake_space_transform=True, use_space_transform=True,
       mesh_smooth_type="FACE", use_triangles=True, use_tspace=True, bake_anim=False,
       add_leaf_bones=False, path_mode="RELATIVE", embed_textures=False)
   ```

8. **Write `game-export.json`** in this folder, in Blender coordinates and metres:
   - `wheels`: for each of the four, `hub` [x, y, z], `radius` (tyre outer radius) and `width`;
   - `wing`: `hinge_point` [x, y, z], `hinge_axis` (unit vector), `deploy_degrees` (signed rotation about that axis from stowed to the round 4 deployed pose);
   - `bounds`: min and max of all visible geometry;
   - `triangles`: per object;
   - `materials`: for each material, `base_color` (linear RGB 0 to 1), `metallic`, `smoothness` (1 − roughness), and `emission` (linear RGB, or null).
9. Render `renders/game/` with the before/after views and a straight side view of the seven objects only.

End with a short report: what you deleted, the triangle counts, the materials list, and anything that looks different from round 4.

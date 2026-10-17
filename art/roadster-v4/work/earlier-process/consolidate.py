import ast,json
from pathlib import Path
p=Path('/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-v4')
s=(p/'build_roadster.py').read_text();tree=ast.parse(s)
keep=['materials','Geo','solid','grid','box','frame','lathe','cyl','tube','interp','nozzle','fan','collision','stats','aim','studio','select_visible','prepare_atlas','raster_ids','srgb','save_pixels','texture_tables','bake_colour_textures','bake_ao_in_process','start_ao','merge_ao','final_material','finish','start_score','production_cleanup','frame_asset','studio_strips']
found={node.name:ast.get_source_segment(s,node) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
# All source material categories are used only during authoring; the final material is shared.
header=s[:s.index('def materials():')]
header=header.replace('Roadster v4. Run in Blender 5.2. All dimensions in metres, front -Y.\nBuild stages: build(); render_round(tag); prepare_atlas(); bake_textures(); finish().','Roadster v4 correction pass. Blender 5.2, metres, front -Y, left +X.\nRun regenerate() in the connected Blender UI. Starts from the read-only v3 scene,\npreserves its four wheel meshes, builds the shell, compares reference cameras,\nbakes an atlas and geometric AO, exports the seven meshes, and runs score.py.\nOnly OUT is written. Reference photos are private inputs and are not packed.')
parts=[header]
parts += [found[k] for k in keep[:12]]
parts += ["VISIBLE=['Roadster_Body','Roadster_Wheel_FL','Roadster_Wheel_FR','Roadster_Wheel_RL','Roadster_Wheel_RR','Roadster_Spoiler']\nHUBS={'FL':(.84,-1.475,.36),'FR':(-.84,-1.475,.36),'RL':(.84,1.475,.36),'RR':(-.84,1.475,.36)}"]
parts += [found[k] for k in keep[12:]]
parts += [(p/'shape.py').read_text()]
parts += [(p/'review.py').read_text()]
parts += ['CAMERAS='+repr(json.loads((p/'camera-match.json').read_text()))]
(p/'build_roadster.py').write_text('\n\n'.join(parts)+'\n')

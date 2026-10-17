import bpy,json
out='/Users/peterhartwieg/Coding_Projects/big-ambitions-roadster/art/roadster-free'
ns={};exec(open(out+'/round2_shape.py').read().split('delete_names=')[0],ns)
c=json.load(open(out+'/round2_current_fingerprints.json'))
r={'accepted_objects_checked':len(ns['before']),'changed_objects':[n for n in ns['before'] if c['objects'].get(n)!=ns['before'][n]],'materials_checked':len(ns['materials_before']),'changed_materials':[n for n in ns['materials_before'] if c['materials'].get(n)!=ns['materials_before'][n]]}
open(out+'/round2_verified_preservation.json','w').write(json.dumps(r,indent=2))

"""Run from Blender 5.2's Python console:
exec(compile(open('/absolute/path/to/roadster-v8a/run_all.py').read(),
             '/absolute/path/to/roadster-v8a/run_all.py','exec'))
No scipy, Pillow, prior meshes or network needed. Takes several minutes.
Only writes inside its own folder. The neighbouring reference JPGs are read-only.
"""
import os,runpy,json
O=os.path.dirname(os.path.abspath(__file__))
runpy.run_path(O+'/measure.py')
S=runpy.run_path(O+'/solve.py');S['main']()
sol=json.load(open(O+'/solution.json'));json.dump({'x':sol['x'],'info':sol['info']},open(O+'/candidate-cold.json','w'),indent=2)
runpy.run_path(O+'/compare_current_spec.py')
U=runpy.run_path(O+'/uncertainty.py');U['main']()
runpy.run_path(O+'/overlay.py')
F=runpy.run_path(O+'/finalize.py');F['export_profile_evidence'](U);F['write_report']()
runpy.run_path(O+'/validate.py')
if os.path.exists(O+'/Proportions.blend1'):os.remove(O+'/Proportions.blend1')

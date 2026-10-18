"""Read-only saved first-lap initialization check before any physical rollout."""
import hashlib,json,time
from pathlib import Path
from retry.joint533_projection import initial_progress
from retry.drive519_control import project,reference
from retry.plan513_model import load_root
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response533-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());p=json.loads(Path('/workspace/haic-response532-private/frozen-paths-private.json').read_text());rows=[]
    for case in json.loads((D/'risks-private.json').read_text()):
        state=dict(case['root_without_roads']);state['roads']=s['root']['roads'];root=load_root(state);base=p['baseline'];old=project(root.center,base,None)['s'];fixed=initial_progress(root,base,case['index']-1);error=abs(fixed-case['progress']);assert old<0 and error<1e-8
        rows.append(dict(label=case['label'],old_signed_fraction=old/base['length'],corrected_first_lap_fraction=fixed/base['length'],baseline_stored_progress_error_m=error,old_reference_m_s=reference(old,base)[0],corrected_reference_m_s=reference(fixed,base)[0]))
    root=load_root(s['root']);cold=initial_progress(root,p['baseline'],0);assert cold==project(root.center,p['baseline'],None)['s']
    out=dict(rows=rows,cold_signed_projection_preserved=True,scope='Harnessinitializationonly;knownfirst-lap prefix completed>0 unwrapnegativeown-paths. Shared528controller/projecttrackingunchanged. Original533draftand530/531/532resultsretained;no model/native everrunbeforefix.',active_model='retry/joint533_model_fixed.py',active_model_sha256=hashlib.sha256((G/'retry/joint533_model_fixed.py').read_bytes()).hexdigest(),projection_sha256=hashlib.sha256((G/'retry/joint533_projection.py').read_bytes()).hexdigest(),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0)
    with (G/'retry/joint533_projection_check.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()

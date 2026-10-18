"""Freeze saved541 entry, one common world plane and immutable control-shooting input."""
import datetime,hashlib,json,time
from pathlib import Path
from retry.lap518_control import project

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');O=Path('/workspace/haic-response545-private');O.mkdir(mode=0o700,exist_ok=False);read=lambda p:json.loads(p.read_text());paths=read(D/'frozen-paths-private.json');full=read(D/'native-full-records-private.json');split=51+sum(x['raw_ticks'] for x in full[0]['rows']);rr=[read(p) for p in sorted(D.glob('raw-*.json'))][split:];rr=[r for r in rr if r['phase']=='action'];a=read(D/'action-candidate-055.json');past=[r for r in rr if r['action']<55 and r['action']>24];target=read(D/'action-candidate-079.json')['after_root_without_roads'];q=project(target['center'],paths['candidate'],next(r['station'] for r in reversed(rr) if r['action']==79));entry=dict(completed=54,history=[sum(z['ratio']>1 for r in past for z in r['forces']),4*len(past)],root=a['before_root_without_roads']);gate=dict(point=target['center'],tangent=q['tangent'],curvature=paths['candidate']['curvature'][q['i']],selection='fixed saved541end79 COM plane; tangent of frozenreference atthatpoint; chosenbefore545physics')
 for name,value in [('entry-private.json',entry),('gate-private.json',gate),('frozen-paths-private.json',paths)]:
  p=O/name
  with p.open('x') as f:json.dump(value,f)
  p.chmod(0o600)
 out=dict(status='PREPARED_NO_NEW_PHYSICS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entry_action=55,gate_after_saved_action=79,prefix_optimized_holds=20,total_holds=32,decision_variables=40,new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,private_inputs_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*private.json')})
 with (G/'retry/shoot545_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

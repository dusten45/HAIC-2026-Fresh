"""Saved541 body/velocity heading and corner selection; no new physics."""
import collections,datetime,hashlib,json,math,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');O=Path('/workspace/haic-response543-private');O.mkdir(mode=0o700,exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();full=read(D/'native-full-records-private.json');split=51+sum(r['raw_ticks'] for r in full[0]['rows']);rows=[read(p) for p in sorted(D.glob('raw-*.json'))][split:];rows=[r for r in rows if r['phase']=='action'];front=[]
 for r in rows:
  if r['action']<=24:continue
  for z in r['forces']:
   if z['wheel']>=2 or z['ratio']<=1:continue
   h=r['before']['wheels'][z['wheel']]['heading'];f=(-math.sin(h),math.cos(h));lf=sum(f[j]*z['vector'][j] for j in range(2));lat=f[1]*z['vector'][0]-f[0]*z['vector'][1]
   if lat*lat>lf*lf:front.append(r);break
 first=min(r['action'] for r in front);tight=min(rows,key=lambda r:r['margin']);risk=tight['action']-16;assert first==32 and risk==55
 groups={}
 for label,lo,hi in [('firstcorner',25,44),('firstexit_and_fast',45,80),('middlecorner',100,124),('latecorner',140,160)]:
  rr=[r for r in rows if lo<=r['action']<=hi];beta=[]
  for r in rr:
   h=r['before_planar']['angle'];v=r['before']['velocity'];f=(-math.sin(h),math.cos(h));beta.append(math.atan2(f[0]*v[1]-f[1]*v[0],sum(f[j]*v[j] for j in range(2))))
  groups[label]=dict(mean_abs_body_velocity_heading_rad=sum(map(abs,beta))/len(beta),max_abs_body_velocity_heading_rad=max(map(abs,beta)),seconds=.02*len(rr))
 roots=[]
 for label,index in [('primary_first_front_lateral_clip',first),('risk_16holds_before_minimum_margin',risk)]:
  a=read(D/f'action-candidate-{index:03d}.json');past=[r for r in rows if 24<r['action']<index];roots.append(dict(label=label,index=index,completed=index-1,history=[sum(z['ratio']>1 for r in past for z in r['forces']),4*len(past)],root=a['before_root_without_roads']))
 with (O/'pilot-roots-private.json').open('x') as f:json.dump(roots,f)
 for name in ('frozen-paths-private.json','approved-case-private.json'):
  p=O/name
  with p.open('xb') as f:f.write((D/name).read_bytes())
  p.chmod(0o600)
 out=dict(status='SAVED541_CORNER_FRAME_DIAGNOSIS',groups=groups,primary_action=first,risk_action=risk,actual_minimum_margin_action=tight['action'],actual_minimum_margin_m=tight['margin'],hypothesis='Body-heading pursuit may treat body/velocity sideslip as geometric heading error. Test velocity-direction pursuit with identical target/lookahead/gain/clamp and unchanged source pedal certification. It can also understeer: not assumed better.',past_failure_preserved='512 held nonzero24thsteer on straight approach: actual margin failure action34/cross-track4.945. New feedback recalculates each action including forecasts; no frozen command/geometryonly safety. 533 solver nonconvergence preserved/no optimizer resume.',new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,source_sha256={str(p):sha(p) for p in [G/'retry/lap518_control.py',G/'retry/structure537_control.py',G/'retry/plan512_result.md',G/'retry/joint533_result.md',D/'native-full-records-private.json']})
 with (G/'retry/velocity543_analysis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

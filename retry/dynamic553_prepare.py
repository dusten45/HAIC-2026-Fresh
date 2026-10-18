"""Freeze exactly552 segment, source551 common-plane baseline and state inputs."""
import bisect,datetime,hashlib,json,math,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response553-private')
def run():
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();D.mkdir(mode=0o700,exist_ok=False);old=Path('/workspace/haic-response551-private');e=rd(Path('/workspace/haic-response552-private/probe-input-private.json'));paths=rd(old/'frozen-paths-private.json');path=paths['candidate'];data=rd(old/'cold-candidate-private.json');assert e['completed']==25;node=bisect.bisect_left(path['arcs'],e['target_station']);a=path['points'][node];b=path['points'][(node+1)%len(path['points'])];l=math.dist(a,b);gate=dict(point=a,tangent=[(b[j]-a[j])/l for j in range(2)],curvature=path['curvature'][node],station=e['target_station']);dot=lambda p,g:sum((p[j]-g['point'][j])*g['tangent'][j] for j in range(2));before=e['root'];cross=None;rows=[]
 for row in data['trace']:
  if row['index']<=e['completed']:continue
  after=row['root_without_roads'];rows.append(row)
  if cross is None and dot(before['center'],gate)<0<=dot(after['center'],gate):
   f=-dot(before['center'],gate)/(dot(after['center'],gate)-dot(before['center'],gate));vel=[before['planar']['linear']['velocity'][j]+f*(after['planar']['linear']['velocity'][j]-before['planar']['linear']['velocity'][j]) for j in range(2)];n=len(rows)-1;cross=dict(index=row['index'],raw=row['raw'],lower_s=.02*n,upper_s=.02*(n+1),time_s=.02*(n+f),speed=math.hypot(*vel))
  before=after
 assert cross is not None;endindex=cross['index']+12;end=next(r for r in data['trace'] if r['index']==endindex and r['raw']==4);i=min(len(path['ds'])-1,bisect.bisect_left(path['arcs'][1:],end['progress']));a,b=path['points'][i],path['points'][(i+1)%len(path['points'])];l=math.dist(a,b);return_gate=dict(point=end['root_without_roads']['center'],tangent=[(b[j]-a[j])/l for j in range(2)],curvature=path['curvature'][i],station=end['progress']);clock=.08*(endindex-e['completed']);return_base=dict(index=endindex,raw=4,lower_s=clock-.02,upper_s=clock,time_s=clock,speed=math.hypot(*end['root_without_roads']['planar']['linear']['velocity']));entry=dict(**e,gate=gate,return_gate=return_gate,baseline_gate=cross,baseline_return=return_base);base_rows=[r for r in data['trace'] if e['completed']<r['index']<=endindex]
 for name,value in [('entry-private.json',entry),('baseline-prefix-private.json',dict(trace=base_rows,gate=cross,return_gate=return_base))]:
  p=D/name
  with p.open('x') as f:json.dump(value,f,indent=2)
  p.chmod(0o600)
 p=D/'frozen-paths-private.json'
 with p.open('xb') as f:f.write((old/'frozen-paths-private.json').read_bytes())
 p.chmod(0o600);out=dict(passed=True,prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),same552_root26=True,baseline551_reused=True,baseline_source_raw_recomputed=0,baseline_gate=cross,baseline_return=return_base,baseline_return_is_after12holds=True,entry_sha256=sha(D/'entry-private.json'),baseline_prefix_sha256=sha(D/'baseline-prefix-private.json'),fixed_path_sha256=sha(p),source551_record_sha256=sha(old/'cold-candidate-private.json'),new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/dynamic553_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

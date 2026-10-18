"""Saved541 actual/source arithmetic only: no model integration or environment calls."""
import bisect,collections,datetime,hashlib,json,math,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');O=Path('/workspace/haic-response542-private');O.mkdir(mode=0o700,exist_ok=False)
 def stop(*a):raise RuntimeError('READ_ANALYSIS_COST_CAP')
 signal.signal(signal.SIGPROF,stop);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,60)
 read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();path=read(D/'frozen-paths-private.json')['candidate'];full=read(D/'native-full-records-private.json');split=51+sum(r['raw_ticks'] for r in full[0]['rows']);raw=[read(p) for p in sorted(D.glob('raw-*.json'))][split:];rows=[r for r in raw if r['phase']=='action'];actions={read(p)['record']['index']:read(p) for p in D.glob('action-candidate-*.json')};high=collections.Counter();failed=collections.Counter();clip=collections.Counter();timegroups=collections.defaultdict(list);choices=[];cumclips=samples=0;runningmax=0.;max_at=None;clipactions=collections.Counter()
 for i,a in actions.items():
  detail=a['governor_detail']
  if i<=24:continue
  h=next(z for z in detail['reports'] if z['mode']=='HIGH');high[(h['reason'],'first_hold' if h['model_ticks']<4 else 'future_tail')]+=1
  for r in detail.get('trials',[]):
   if not r['ok']:failed[(r['reason'],'first_hold' if r['model_ticks']<4 else 'future_tail')]+=1
  choices.append(dict(index=i,mode=detail['mode'],high_reason=h['reason'],high_ticks=h['model_ticks'],high_first_hold_pass=h.get('first_hold_pass'),selected= a['record']['action'],margin=a['record']['min_margin']))
 for r in rows:
  a=actions[r['action']]['record']['action'];s=max(0.,min(path['length'],r['station']));j=max(0,min(len(path['ds'])-1,bisect.bisect_left(path['arcs'][1:],s)));qs=path['launch_squared'];ff=(qs[j+1]-qs[j])/(2*path['ds'][j]);kind='launch' if r['action']<=24 else ('flat90' if abs(ff)<1e-8 and abs(r['reference_speed']-90)<1e-6 else 'accelerating_reference' if ff>1e-8 else 'braking_reference' if ff< -1e-8 else 'otherflat');timegroups[kind].append(r)
  if r['action']<=24:continue
  samples+=4
  for z in r['forces']:
   if z['ratio']<=1:continue
   cumclips+=1;w=r['before']['wheels'][z['wheel']];f=(-math.sin(w['heading']),math.cos(w['heading']));side=(f[1],-f[0]);v=z['vector'];lf=sum(v[k]*f[k] for k in range(2));lat=sum(v[k]*side[k] for k in range(2));fraction=lat*lat/(lf*lf+lat*lat);axle='front' if z['wheel']<2 else 'rear';clip[(axle,'lateral_dominant' if fraction>.5 else 'longitudinal_dominant')]+=1;clipactions[r['action']]+=1
  if cumclips/samples>runningmax:runningmax=cumclips/samples;max_at=dict(action=r['action'],running_wheel_samples=samples,cumulative_clips=cumclips,model_time_s=r['time']-1.02)
 groups={}
 for kind,rr in timegroups.items():
  groups[kind]=dict(seconds=.02*len(rr),mean_speed=sum(r['speed'] for r in rr)/len(rr),mean_reference=sum(r['reference_speed'] for r in rr)/len(rr),mean_positive_deficit=sum(max(0.,r['reference_speed']-r['speed']) for r in rr)/len(rr),mean_positive_overspeed=sum(max(0.,r['speed']-r['reference_speed']) for r in rr)/len(rr),mean_peak_force=sum(max(z['ratio'] for z in r['forces']) for r in rr)/len(rr),min_margin=min(r['margin'] for r in rr),brake_seconds=.02*sum(actions[r['action']]['record']['action'][2]>0 for r in rr))
 out=dict(status='SAVED541_DIAGNOSIS_NO_NEW_PHYSICS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs={str(p):sha(p) for p in [D/'frozen-paths-private.json',D/'native-full-records-private.json',G/'retry/structure537_control.py',G/'retry/lap518_control.py',G/'retry/joint541_summary.json']},native_groups=groups,rejected_high_reason_and_location={'/'.join(k):v for k,v in high.items()},rejected_trials_reason_and_location={'/'.join(k):v for k,v in failed.items()},running_clipped_wheel_decomposition={'/'.join(k):v for k,v in clip.items()},running_clipping_max=runningmax,running_clipping_max_at=max_at,clipped_actions=dict(sorted(clipactions.items())),geometry_reference_length_m=path['length'],actual_polyline_distance_m=sum(math.dist(r['before_position'],r['position']) for r in rows),new_model_ticks=0,new_native_actions=0,new_seeds=0,protected_queries=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (O/'selection-diagnosis-private.json').open('x') as f:json.dump(choices,f)
 with (G/'retry/diagnosis542_analysis.json').open('x') as f:json.dump(out,f,indent=2)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(out,indent=2))
if __name__=='__main__':run()

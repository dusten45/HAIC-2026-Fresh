"""Saved538actual bottlenecks. No controller or model imports."""
import bisect,hashlib,json,math,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('ANALYSIS_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response538-private');O=Path('/workspace/haic-response539-private');read=lambda p:json.loads(Path(p).read_text());p=read(D/'frozen-paths-private.json')['candidate'];start=read(D/'close-baseline-private.json')['counts']['raw_completed']+51;rows=[]
 for f in sorted(D.glob('raw-*.json')):
  if int(f.stem.split('-')[-1])<=start:continue
  r=read(f)
  if r['phase']!='action':continue
  u=min(max(r['station'],0.),p['length']);i=max(0,min(len(p['ds'])-1,bisect.bisect_left(p['arcs'],u)-1));q0,q1=p['launch_squared'][i:i+2];ff=(q1-q0)/(2*p['ds'][i]);force=max(z['ratio'] for z in r['forces']);rows.append(dict(index=r['action'],raw_time=r['time'],s=r['station'],v=r['speed'],target=r['reference_speed'],surplus=r['speed']-r['reference_speed'],ff=ff,top80=abs(q0-6400)<1e-6 and abs(q1-6400)<1e-6,force=force,margin=r['margin'],path_error=r['path_error'],body_speed=r['body_speed_max']))
 def stats(rr):
  if not rr:return dict(seconds=0.)
  return dict(seconds=.02*len(rr),mean_speed=sum(r['v'] for r in rr)/len(rr),mean_reference=sum(r['target'] for r in rr)/len(rr),mean_surplus=sum(r['surplus'] for r in rr)/len(rr),mean_peak_force=sum(r['force'] for r in rr)/len(rr),max_peak_force=max(r['force'] for r in rr),min_margin=min(r['margin'] for r in rr),max_body_speed=max(r['body_speed'] for r in rr),max_path_error=max(r['path_error'] for r in rr))
 groups={'fixed_launch':stats([r for r in rows if r['index']<=24]),'flat_top80':stats([r for r in rows if r['top80']]),'top80_with_force_below_0_7':stats([r for r in rows if r['top80'] and r['force']<.7]),'positive_ff':stats([r for r in rows if r['ff']>1]),'negative_ff':stats([r for r in rows if r['ff']< -1]),'non_top_near_constant':stats([r for r in rows if not r['top80'] and abs(r['ff'])<=1]),'reference_band_above_4':stats([r for r in rows if r['surplus']>4]),'near_force_admission':stats([r for r in rows if r['index']>24 and r['force']>.95]),'footprint_below_1':stats([r for r in rows if r['margin']<1.])}
 longest=[];run=[]
 for r in rows:
  if r['top80']:run.append(r)
  else:
   if len(run)>len(longest):longest=run
   run=[]
 if len(run)>len(longest):longest=run
 out=dict(status='SAVED_538_ACTUAL_ANALYSIS',actual_s=.02*len(rows),groups_overlap=True,groups=groups,longest_flat_run=dict(seconds=.02*len(longest),first_action=longest[0]['index'],last_action=longest[-1]['index']),interpretation='Actual nominal cap80 is distinct from speeds near84.85 allowed by reference band. Top exposure and low force are evidence for a new current-path reference-cap test, not recoverable-time or physical-limit proof. Prior529useddifferentGaussianpath/policy.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,model_ticks=0)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/profile539_analysis.json').open('x') as f:json.dump(out,f,indent=2)
 with (O/'accounting-rows-private.json').open('x') as f:json.dump(rows,f)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

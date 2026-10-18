"""Read saved actual launch; replay source wheel algebra without physics steps."""
import json,math,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('ANALYSIS_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response538-private');O=Path('/workspace/haic-response540-private');read=lambda p:json.loads(Path(p).read_text());start=read(D/'close-baseline-private.json')['counts']['raw_completed']+51;rows=[]
 acts={read(p)['record']['index']:read(p)['record'] for p in D.glob('action-candidate-*.json')}
 for p in sorted(D.glob('raw-*.json')):
  if int(p.stem.split('-')[-1])<=start:continue
  r=read(p)
  if r['phase']!='action' or r['action']>48:continue
  a=acts[r['action']]['action'];wheels=[]
  for i,w in enumerate(r['before']['wheels']):
   g=w['gas']+min(.1,a[1]-w['gas']) if i>=2 else w['gas'];omega=w['omega']+.02*40000*r['effects'][1]*g/1.6/(abs(w['omega'])+5.);forward=(-math.sin(w['heading']),math.cos(w['heading']));v=[r['before']['velocity'][j]+w['offset'][j] for j in range(2)];vf=sum(forward[j]*v[j] for j in range(2));slip=.54*omega-vf;wheels.append(dict(gas=g,slip_m_s=slip,ratio=r['forces'][i]['ratio'],clipped=r['forces'][i]['ratio']>1))
  rows.append(dict(index=r['action'],raw_time=r['time'],speed=r['speed'],progress=r['station'],margin=r['margin'],target=r['reference_speed'],rear_gas=sum(w['gas'] for w in wheels[2:])/2,rear_slip=sum(w['slip_m_s'] for w in wheels[2:])/2,peak_force=max(w['ratio'] for w in wheels),clipped=sum(w['clipped'] for w in wheels),wheels=wheels))
 groups={}
 for label,rr in [('launch_first_0_48s',rows[:24]),('launch_middle_0_48_to_1_28s',rows[24:64]),('launch_last_0_64s',rows[64:96]),('postlaunch_first_0_96s',rows[96:144]),('firstcorner_to_3_84s',rows[144:])]:
  groups[label]=dict(seconds=.02*len(rr),start_speed=rr[0]['speed'],end_speed=rr[-1]['speed'],mean_rear_gas=sum(r['rear_gas'] for r in rr)/len(rr),mean_rear_slip_m_s=sum(r['rear_slip'] for r in rr)/len(rr),mean_peak_force=sum(r['peak_force'] for r in rr)/len(rr),force_peak=max(r['peak_force'] for r in rr),clipped=sum(r['clipped'] for r in rr),samples=4*len(rr),min_margin=min(r['margin'] for r in rr))
 out=dict(status='SAVED538_LAUNCH_ANALYSIS',groups=groups,launch_end_reference_m_s=rows[95]['target'],launch_end_speed_m_s=rows[95]['speed'],launch_end_positive_deficit_m_s=rows[95]['target']-rows[95]['speed'],launch_final_clipping=[sum(r['clipped'] for r in rows[:96]),384],interpretation='Fixed.32 spends clipping budget early while laterlaunch has unused force/engine input and speed deficit; current-state source-force allocation is a structural candidate, not a fixedgas sweep. Exposure/deficit is not recoverable-time gain. Launch2.5/15% is separate from tracking1.06/10%.',model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/launch540_analysis.json').open('x') as f:json.dump(out,f,indent=2)
 with (O/'launch-rows-private.json').open('x') as f:json.dump(rows,f)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

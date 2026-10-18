"""Saved model prefixes and common-arc clocks; no integration or policy calls."""
import hashlib,json,math,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('STATIC_DIAGNOSTIC_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];read=lambda p:json.loads(Path(p).read_text());static=read('/workspace/haic-response515-private/collected-map-state-private.json');p=read('/workspace/haic-response540-private/frozen-paths-private.json')['candidate'];out=[]
 for stage in (538,540):
  case=read(f'/workspace/haic-response{stage}-private/cold-candidate-private.json');prev=static['root'];rr=[];times={};milestones=[50.,100.,150.,200.,p['length']/2,p['length']]
  for i,r in enumerate(case['trace']):
   if r['index']<=24:
    vals=[];a=r['action'];state=prev['planar']['linear']
    for w in state['wheels'][2:]:
     g=w['gas']+min(.1,a[1]-w['gas']);omega=w['omega']+.02*40000*state['engine_multiplier']*g/(1.6*(abs(w['omega'])+5.));omega=0. if a[2]>=.9 else omega-math.copysign(min(15*a[2],abs(omega)),omega) if a[2]>0 else omega;f=(-math.sin(w['heading']),math.cos(w['heading']));vf=sum(f[j]*(state['velocity'][j]+w['offset'][j]) for j in range(2));vals.append((g,.54*omega-vf))
    rr.append(dict(gas=sum(v[0] for v in vals)/2,slip=sum(v[1] for v in vals)/2,force=max(f['ratio'] for f in r['forces']),clipped=sum(f['clipped'] for f in r['forces'])))
   if i:
    before=case['trace'][i-1]['progress'];after=r['progress']
    for m in milestones:
     if before<m<=after and str(m) not in times:times[str(m)]=.02*i+.02*(m-before)/(after-before)
   prev=r['root_without_roads']
  groups={}
  for name,rows in [('first_0_48s',rr[:24]),('middle_0_8s',rr[24:64]),('last_0_64s',rr[64:])]:groups[name]=dict(mean_rear_gas=sum(r['gas'] for r in rows)/len(rows),mean_rear_slip_m_s=sum(r['slip'] for r in rows)/len(rows),mean_peak_force=sum(r['force'] for r in rows)/len(rows),clipped=sum(r['clipped'] for r in rows),samples=4*len(rows))
  out.append(dict(stage=stage,launch_groups=groups,common_arc_milestone_clocks_s=times,model_finish_s=case['summary']['model_finish_episode_s']))
 gains={k:out[0]['common_arc_milestone_clocks_s'][k]-out[1]['common_arc_milestone_clocks_s'][k] for k in out[0]['common_arc_milestone_clocks_s']}
 result=dict(status='SAVED_LAUNCH_RESPONSE_ACCOUNTING_COMPLETE',stages=out,common_arc_realized_clock_gains_s=gains,interpretation='Model data,20mslinearclockallocation,notofficialmilestonetime or independent recoverable gains. Newlaunch uses more of allowed clipping budget; torque/slip allocation is not a claim of aggregate clipping reduction. Large endlaunch speed/progress does not equal whole-lap improvement.',new_model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/launch540_diagnostic.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__':run()

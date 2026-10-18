"""Saved common-arc model accounting only; never integrate physics."""
import bisect,json,math,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('SAVED_DIAGNOSTIC_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];read=lambda p:json.loads(Path(p).read_text());paths=read('/workspace/haic-response539-private/frozen-paths-private.json');p=paths['baseline'];L=p['length'];static=read('/workspace/haic-response515-private/collected-map-state-private.json');pos=static['root']['center'];best=(1e99,0.)
 for i,a in enumerate(p['points']):
  b=p['points'][(i+1)%len(p['points'])];dx,dy=b[0]-a[0],b[1]-a[1];t=max(0.,min(1.,sum((pos[j]-a[j])*(b[j]-a[j]) for j in range(2))/(dx*dx+dy*dy)));d=math.dist(pos,(a[0]+t*dx,a[1]+t*dy))
  if d<best[0]:best=(d,p['arcs'][i]+t*p['ds'][i])
 first=best[1] if best[1]<=L/2 else best[1]-L;edges=sorted(set([0.,L]+p['arcs']+[L*i/12 for i in range(13)]));allstats=[]
 for stage in (538,539):
  saved=read(f'/workspace/haic-response{stage}-private/cold-candidate-private.json');commands={x['index']:x['detail']['mode'] for x in saved['commands']};groups={};bins={};prev=first
  def add(dst,key,dt,r):
   z=dst.setdefault(key,dict(seconds=0.,weighted_peak_force=0.,min_margin=1e99,governor_seconds=0.));z['seconds']+=dt;z['weighted_peak_force']+=dt*max(f['ratio'] for f in r['forces']);z['min_margin']=min(z['min_margin'],r['margin']);z['governor_seconds']+=dt*(commands[r['index']] not in ('SOURCE_FULL','FIXED_LAUNCH'))
  for r in saved['trace']:
   cur=r['progress'];assert cur>prev;cuts=[prev]+[v for v in edges if prev<v<cur]+[cur]
   for a,b in zip(cuts,cuts[1:]):
    mid=(a+b)/2;dt=.02*(b-a)/(cur-prev)
    if 0<=mid<L:
     i=max(0,min(len(p['ds'])-1,bisect.bisect_right(p['arcs'],mid)-1));q0,q1=p['launch_squared'][i:i+2];ff=(q1-q0)/(2*p['ds'][i]);label='baseline_flat80' if abs(q0-6400)<1e-6 and abs(q1-6400)<1e-6 else ('baseline_forward' if ff>1 else ('baseline_braking' if ff< -1 else 'baseline_other'));binid=str(min(11,int(mid/L*12))+1)
    else:label='outside_supported_arc';binid='outside'
    add(groups,label,dt,r);add(bins,binid,dt,r)
   prev=cur
  for dst in (groups,bins):
   for z in dst.values():z['mean_peak_force']=z.pop('weighted_peak_force')/z['seconds']
  assert abs(sum(z['seconds'] for z in groups.values())-.02*len(saved['trace']))<1e-8
  allstats.append(dict(stage=stage,groups=groups,bins=bins))
 delta={k:allstats[0]['groups'][k]['seconds']-allstats[1]['groups'][k]['seconds'] for k in allstats[0]['groups']}
 out=dict(status='SAVED_COMMON_ARC_ACCOUNTING_COMPLETE',stages=allstats,realized_time_difference_by_fixed_baseline_segment_s=delta,total_model_gain_s=sum(delta.values()),interpretation='All labels fixed by538profile at common533arc. Boundary timing is linearly allocated from20ms samples, not sub-tick measurement. These realized timing differences include coupled steering/progress/arrival effects and are not independently recoverable or causal components.',native_actions=0,model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/profile539_diagnostic.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:v for k,v in out.items() if k!='stages'},indent=2))
if __name__=='__main__':run()

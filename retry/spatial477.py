"""Saved-only common space/time and hold response; no new trajectories."""
import json,math,time
from pathlib import Path
from retry.loss389_analyze import read,sha,save
from retry.signed417_executor import canonical_projection

def run(root):
 root=Path(root);d=root/'stage477-revision1';start=time.process_time();wall=time.perf_counter();p=read(d/'plan.json');line=read(p['fixed_plan'])['line'];arms=['Projected4Reference','AllocationP4'];rows={a:read(d/('whole_'+a+'-private.json'))['rows'] for a in arms};streams={a:read(d/('whole_'+a+'-observer-private.json'))['posts'] for a in arms};points={}
 for a in arms:
  rr=[];failed=False
  for i,z in enumerate(streams[a],1):
   q=canonical_projection(line,z['position'],z['velocity'],z['phase']);failed|=z['path_error_m']>3 or z['damage']>0 or z['collision'] or z['grass'] or z['wheel_road_contacts']<4
   rr.append(dict(tick=i,physical_time_s=z['time'],elapsed_s=i/50,arc_m=q['arc'],post_path_error_m=q['path_error_m'],frozen_guard_path_error_m=z['path_error_m'],speed_m_s=math.hypot(*z['velocity']),force_ratio=max(t['force_ratio'] for t in z['preclip']),M=max(0.,max(t['force_ratio']-1 for t in z['preclip'])),safe_through=not failed))
  points[a]=rr
 prefix=0
 for x,y in zip(rows[arms[0]],rows[arms[1]]):
  if x!=y:break
  prefix+=1
 max_common=min(max(q['arc_m'] for q in points[a] if q['safe_through']) for a in arms);common=[]
 for arc in range(50,5*math.floor(max_common/5)+1,5):
  hits={}
  for a in arms:
   prev=0.
   for q in points[a]:
    if q['arc_m']>=arc:
     hits[a]={**q,'elapsed_bracket_s':[prev,q['elapsed_s']]};break
    prev=q['elapsed_s']
  if len(hits)==2:
   x,y=(hits[a] for a in arms);common.append(dict(arc_m=arc,old=x,allocated=y,old_minus_allocated_bracket_s=[x['elapsed_bracket_s'][0]-y['elapsed_bracket_s'][1],x['elapsed_bracket_s'][1]-y['elapsed_bracket_s'][0]],both_safe=x['safe_through'] and y['safe_through']))
 first_bad={a:next((q for q in points[a] if not q['safe_through']),None) for a in arms};endtick=min(len(qs) for qs in points.values());same_time=[dict(old=points[arms[0]][i],allocated=points[arms[1]][i]) for i in range(endtick)];firstbadindex=first_bad[arms[0]]['tick']-1
 packets=[read(f) for f in d.glob('allocation-proof-*.json')];changes=[]
 for packet in packets:
  if packet['label']!='whole_AllocationP4' or not packet['changed']:continue
  wi=packet['action'];row=rows['AllocationP4'][wi-1];tires=row['tires'];changes.append(dict(action=wi,physical_time_s=row['raw_hull'][0]['time'],first_objective_q0=packet['proof']['objective_q0'],first_objective_allocated=packet['proof']['objective'],held_raw_M=[max(0.,max(t['force_ratio']-1 for t in tires if t['raw_tick']==k)) for k in range(1,row['predicted']['raw_ticks']+1)],held_guard_path_max_m=max(z['path_error_m'] for z in streams['AllocationP4'][(wi-1)*4:wi*4]),held_safe=not row['safety']))
 before_first_change={a:next((dict(physical_time_s=h['time'],wheel=t['wheel'],lat_alone_ratio=abs(t['raw_lat_N'])/t['friction_limit']) for row in rows[a] for h in row['raw_hull'] for t in row['tires'] if t['raw_tick']==h['raw_tick'] and abs(t['raw_lat_N'])>t['friction_limit']),None) for a in arms}
 full=dict(stage=477,prefix_exact_rows=prefix,prefix_exact_raw_ticks=4*prefix,common_space_5m=common,same_time_20ms=same_time,baseline_first_failure_same_time=same_time[firstbadindex],first_bad=first_bad,first_lateral_alone_above_limit=before_first_change,intervention_hold_responses=changes,analysis_posthoc=True,not_policy_triggers=True,new_physics=0,new_native=0,CPU_s=time.process_time()-start,wall_s=time.perf_counter()-wall)
 save(d/'spatial-time-private.json',full)
 public={k:v for k,v in full.items() if k not in ['common_space_5m','same_time_20ms']};public['common_space_tail']=[x for x in common if x['arc_m']>=295];public['new_archive']=False;save(Path(__file__).resolve().parent/'compare477_spatial.json',public);print(json.dumps(public))
if __name__=='__main__':run(__import__('sys').argv[1])

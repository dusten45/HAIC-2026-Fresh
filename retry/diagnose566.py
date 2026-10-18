"""Read-only spatial/time reconciliation for saved551/562/565 source tapes."""
import hashlib,json,math,time
from pathlib import Path
from retry.clip561_core import atomic_write,plain
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response566-private')
P={
 '551':Path('/workspace/haic-response551-private/cold-candidate-private.json'),
 'paths':Path('/workspace/haic-response551-private/frozen-paths-private.json'),
 '562prefix':Path('/workspace/haic-response562-private/prefix-modified-private.json'),
 '562feedback':Path('/workspace/haic-response562-private/feedback-suffix-private.json'),
 '565':Path('/workspace/haic-response565-private/final-tape-private.json'),
 '565result':G/'retry/interior565_result.json',
 'finish_source':G/'core/finish_line.py'}
rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows_for():
 b=rd(P['551']);prefix=rd(P['562prefix']);feedback=rd(P['562feedback']);five=rd(P['565']);return {'551':b['trace'],'562':prefix['rows']+feedback['rows'],'565':five['rows']},b,prefix,feedback,five

def root(row):return row['root_without_roads']
def fields(r):
 q=root(r);v=q['planar']['linear']['velocity'];return q['center'],v,q['planar']['angle'],q['planar']['yaw']
def wrap(x):return math.atan2(math.sin(x),math.cos(x))
def crossing(rows,point,normal,after=-1):
 prev=None;prevrow=None
 for j,r in enumerate(rows):
  c,v,a,y=fields(r);s=sum((c[k]-point[k])*normal[k] for k in range(2))
  raw=r.get('global_raw_after',j+1)
  if prev is not None and prev<0<=s and raw>after:
   f=-prev/(s-prev);c0,_,a0,y0=fields(prevrow);tm0=prevrow.get('global_raw_after',raw-1)*.02;tm1=raw*.02;speed0=math.hypot(*fields(prevrow)[1]);speed1=math.hypot(*v);dh=wrap(a-a0);dx=[c0[k]+f*(c[k]-c0[k]) for k in range(2)];lat=(-normal[1]*(dx[0]-point[0])+normal[0]*(dx[1]-point[1]));
   clips_before=None;clips_after=None
   return dict(raw_before=raw-1,raw_after=raw,raw_bracket_source_s=[tm0,tm1],fraction=f,diagnostic_crossing_source_s=tm0+f*(tm1-tm0),global_elapsed_clock_s=tm0+f*(tm1-tm0)+1.02,lateral_m=lat,speed_m_s=speed0+f*(speed1-speed0),heading_rad=a0+f*dh,yaw_rate_rad_s=y0+f*(y-y0),clip_count_before_raw=clips_before,clip_count_after_raw=clips_after)
  prev,prevrow=s,r
 return None

def station_point(path,s):
 arcs=path['arcs'];pts=path['points'];i=next((i for i in range(len(path['ds'])) if arcs[i+1]>=s),len(path['ds'])-1);f=(s-arcs[i])/path['ds'][i];a=pts[i];b=pts[(i+1)%len(pts)];p=[a[j]+f*(b[j]-a[j]) for j in range(2)];v=[b[j]-a[j] for j in range(2)];n=math.hypot(*v);return p,[x/n for x in v]

def force_clip_summary(rows):
 launch=tracking=0;out={}
 for r in rows:
  n=r['index'];clips=sum(bool(f['clipped']) for f in r['forces'])
  if n<=24:launch+=clips
  else:tracking+=clips
  if r['raw']==4:out[n]=dict(launch_clipped=launch,tracking_clipped=tracking,tracking_samples=max(0,n-24)*16)
 return dict(launch_clipped=launch,tracking_clipped=tracking,tracking_samples=(len(rows)-96)*4 if len(rows)>96 else 0)

def clip_history_at(rows,target,include_current=True):
 total=0
 for j,r in enumerate(rows):
  raw=r.get('global_raw_after',j+1)
  if r['index']>24 and (raw<target or (include_current and raw==target)):
   total+=sum(bool(f['clipped']) for f in r['forces'])
 return total

def main():
 D.mkdir(mode=0o700,exist_ok=True);cpu,wall=time.process_time(),time.perf_counter();atomic_write(D/'STARTED.json',dict(source_sha256=sha(G/'retry/diagnose566.py'),scope='read-only saved-record analysis; zero source ticks'),True);rows,base,prefix,fb,five=rows_for();assert all(len(v)==662 for v in rows.values());result=rd(P['565result']);gates=[]
 # Established action54/66/75 planes, anchored by saved551 raw4 root and velocity.
 for idx in (54,66,75):
  r=next(r for r in rows['551'] if r['index']==idx and r['raw']==4);c,v,*_=fields(r);sp=math.hypot(*v);gates.append((f'action{idx}',c,[z/sp for z in v],float(r['progress'])))
 # Fixed path cross-sections; their origin/tangent never depends on candidate path or route choice.
 path=rd(P['paths'])['candidate']
 for s in range(100,1000,100):
  point,tangent=station_point(path,float(s));gates.append((f'path_s{s}',point,tangent,float(s)))
 summary={};crossings={}
 for name,rr in rows.items():
  summary[name]=dict(raw=len(rr),clip_history=force_clip_summary(rr));crossings[name]={}
  for gate,point,normal,s in gates:
   q=crossing(rr,point,normal)
   if q is not None:
    q['tracking_clip_history_before_raw']=clip_history_at(rr,q['raw_before'],include_current=False)
    q['tracking_clip_history_after_raw']=clip_history_at(rr,q['raw_after'],include_current=True)
    q['source_elapsed_from_action35_s']=q['diagnostic_crossing_source_s']-136*.02
    q['station_s']=s;crossings[name][gate]=q
   else:crossings[name][gate]=None
  # Tracker official end record and its sampled center-plane bracket.
  if name=='551':tr=base['source_tracker']
  else:tr=rr[-1]['tracker']
  tr_center=tr['center'];tr_forward=tr['forward'];centerhit=None
  prev=None
  for j,r in enumerate(rr):
   c,v,a,y=fields(r);long=sum((c[k]-tr_center[k])*tr_forward[k] for k in range(2));lat=(c[0]-tr_center[0])*tr_forward[1]-(c[1]-tr_center[1])*tr_forward[0];raw=r.get('global_raw_after',j+1)
   if prev is not None and prev[0]<0<=long and abs(lat)<=tr['half_width'] and raw>500:
    centerhit=dict(raw_before=raw-1,raw_at_or_after=raw,raw_bracket_source_s=[(raw-1)*.02,raw*.02],lat_at_sample_m=lat,previous_longitudinal_m=prev[0],current_longitudinal_m=long);break
   prev=(long,r)
  firstcandidate=next((r for r in rr if r.get('tracker',{}).get('candidate_crossing_time_s') is not None),None)
  depthhit=None;prevdepth=None
  for j,r in enumerate(rr):
   c,v,a,y=fields(r);long=sum((c[k]-tr_center[k])*tr_forward[k] for k in range(2));raw=r.get('global_raw_after',j+1)
   if prevdepth is not None and prevdepth[0]<tr['half_depth']<=long and raw>500:
    depthhit=dict(raw_before=raw-1,raw_at_or_after=raw,raw_bracket_source_s=[(raw-1)*.02,raw*.02],previous_longitudinal_m=prevdepth[0],current_longitudinal_m=long);break
   prevdepth=(long,r)
  if firstcandidate is None and centerhit is not None:firstcandidate=dict(global_raw_after=centerhit['raw_at_or_after'],index=rr[centerhit['raw_at_or_after']-1]['index'])
  summary[name]['finish']=dict(finish_time_s=tr['finish_time_s'],official_source_finish_s=tr['finish_time_s']-1.02,qualified_time_s=tr['qualified_time_s'],candidate_sample_time_s=tr['candidate_crossing_time_s'],candidate_row_raw=firstcandidate.get('global_raw_after') if firstcandidate else None,candidate_row_index=firstcandidate.get('index') if firstcandidate else None,candidate_sample_source_time_s=(centerhit['raw_at_or_after']*.02 if centerhit else None),candidate_tracker_clock_match=bool(centerhit and abs((centerhit['raw_at_or_after']*.02+1.02)-tr['finish_time_s'])<1e-9),center_plane_bracket=centerhit,confirmation_bracket=depthhit,center_lateral_end_m=tr['previous_lateral'],center_longitudinal_end_m=tr['previous_longitudinal'],half_depth_m=tr['half_depth'],half_width_m=tr['half_width'])
 # Plane interval durations and cumulative vs551, strictly diagnostic interpolations.
 times={n:{g:v['diagnostic_crossing_source_s'] for g,v in q.items() if v is not None} for n,q in crossings.items()};intervals={}
 for name in rows:
  prior=0.;lastgate='start';items=[]
  for gate,t in sorted(times[name].items(),key=lambda z:z[1]):
   s=next(x[3] for x in gates if x[0]==gate)
   items.append(dict(gate=gate,station_s=s,cumulative_source_time_s=t,cumulative_from_action35_s=t-2.72,interval_since_previous_gate_s=t-prior,previous_gate=lastgate));prior=t;lastgate=gate
  intervals[name]=items
 deltas={}
 for gate,_,__,s in gates:
  ref=times['551'].get(gate)
  if ref is not None:
   vals={n:times[n].get(gate) for n in rows};deltas[gate]=dict(station_s=s,time_from_action35_s={n:(v-2.72 if v is not None else None) for n,v in vals.items()},delta_vs551_ms={n:(1000*(v-ref) if v is not None else None) for n,v in vals.items()})
 official={n:v['finish']['official_source_finish_s'] for n,v in summary.items()}
 prefix_exact=all(rows['551'][i]['root_without_roads']==rows['562'][i]['root_without_roads']==rows['565'][i]['root_without_roads'] and rows['551'][i]['forces']==rows['562'][i]['forces']==rows['565'][i]['forces'] for i in range(136))
 raw_steps=[]
 for rr in rows.values():
  for j in range(1,len(rr)):
   raw_steps.append(rr[j].get('global_raw_after',j+1)*.02-rr[j-1].get('global_raw_after',j)*.02)
 dt=min(raw_steps)
 t75={n:crossings[n]['action75']['source_elapsed_from_action35_s'] for n in rows}
 checks=dict(three_full_662_raw=all(len(v)==662 for v in rows.values()),common_original_prefix_136_raw_fullstate_force_exact=prefix_exact,action75_matches_565_saved_finite_endpoint=abs(t75['565']-result['finite_plane_times_s'][2])<1e-9,saved_whole_source_times_all_equal=len(set(official.values()))==1 and abs(official['562']-rd(G/'retry/handoff562_result.json')['whole_source_finish_s'])<1e-9 and abs(official['565']-result['whole_attempt_finish_s'])<1e-9,tracker_candidate_clock_matches_sampled_center_plane=all(summary[n]['finish']['candidate_tracker_clock_match'] for n in rows),same_center_candidate_raw=all(summary[n]['finish']['candidate_row_raw']==661 for n in rows),same_depth_confirmation_raw=all(summary[n]['finish']['confirmation_bracket']['raw_at_or_after']==662 for n in rows),all_selected_spatial_gates_crossed=all(crossings[n][g] is not None for n in rows for g,_,__,_ in gates),no_source_physics_calls=True)
 out=dict(input_sha256={k:sha(v) for k,v in P.items()},source_sha256={p:sha(G/p) for p in ['retry/diagnose566.py','core/finish_line.py','retry/interior565_result.json','retry/handoff562_result.json']},trajectory_summary=summary,spatial_crossings=crossings,gate_interval_durations=intervals,cumulative_time_deltas_vs551=deltas,official_finish_time_s=official,official_finish_quantum_s=dt,read_only_checks=checks,analysis_passed=all(checks.values()),finish_raw_resolution=dict(candidate_sample_raw={n:summary[n]['finish']['candidate_row_raw'] for n in rows},confirmation_raw={n:summary[n]['finish']['confirmation_bracket']['raw_at_or_after'] if summary[n]['finish']['confirmation_bracket'] else None for n in rows},all_same_candidate_tick=len(set(summary[n]['finish']['candidate_row_raw'] for n in rows))==1,all_same_confirmation_tick=len(set(summary[n]['finish']['confirmation_bracket']['raw_at_or_after'] if summary[n]['finish']['confirmation_bracket'] else None for n in rows))==1),finite_565_cumulative_gain_ms=result['finite_cumulative_gain_ms'],whole_565_gain_vs551_ms=result['whole_gain_vs551_ms'],conclusion='Saved fixed-plane interpolants show finite gains,which are partly repaid at later fixed spatial stations. All three official tracker times tie because their center-crossing candidate is sampled on raw661; the interpolated center-plane times remain diagnostic only.',model_ticks=0,force_calls=0,geometry_calls=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 atomic_write(G/'retry/diagnose566_result.json',out,True);print(json.dumps(plain(out),indent=2))
if __name__=='__main__':main()

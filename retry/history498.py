"""Nominal-only498 authority. Original finite history validator is unchanged."""
import copy,math
from dataclasses import asdict
import numpy as np
from retry.schema493 import digest
from retry.pilot420_json import json_ready

def check(v,msg):
 if not v:raise RuntimeError('498_OWN_'+msg)
def same(a,b):return digest(json_ready(a))==digest(json_ready(b))
def authenticate_own(c,root,transitions,policy_digest,hist,project,mods):
 check(len(transitions)==len(c.rows)==len(c.stream.actions)==len(c.capture_holds495)>0,'COVERAGE')
 check(c.stream.root_memory==root['before'] and c.stream.root_ledger==root['ledger'],'ROOT_MEMORY_LEDGER')
 check(mods['online481'].physical_identity(c.stream.root_state)==mods['online481'].physical_identity(root['state']),'ROOT_STATE')
 check(c.stream.root_rng['digest']==root['RNG']['digest'],'ROOT_RNG')
 initial=mods['planner419_model_ledger'].ForecastLedger(**copy.deepcopy(root['ledger']));ledger=initial;clock=initial.last_clock_tick;memory=copy.deepcopy(root['before']);previous=None;prevrow=None;offset=0;L=c.L
 h=c.stream.root_state['physical']['hull'];arc=project(c.line,h['position'],h['velocity'],memory['C']['phase'])['arc']
 for i,(t,row,a) in enumerate(zip(transitions,c.rows,c.stream.actions),1):
  q=row['predicted'];n=q['raw_ticks'];posts=c.stream.posts[offset:offset+n]
  check(t['index']==i and t['policy_digest']==policy_digest and t['row_digest']==mods['io481'].canonical(row),'POLICY_ROW')
  check(t['RNG_digest']==root['RNG']['digest'],'RNG')
  check(t['memory_before']==memory==row['memory_before']==a['memory_before'],'MEMORY_BEFORE')
  check(same(t['ledger_before'],asdict(ledger)),'LEDGER_BEFORE')
  check(row['command']==a['command']==a['nominal'],'NOMINAL_ONLY_NO_OVERRIDE')
  check(row['memory_after']==a['memory_after'],'MEMORY_AFTER')
  check(n==len(posts)==len(row['raw_hull']) and len(row['tires'])==4*n and 1<=n<=4,'RAW_COVERAGE')
  check(a['action_index']==i and a['raw_end_clock']==clock+n,'CLOCK')
  hist._join_snapshot(t['state_before'],c.stream.root_state,previous,prevrow,clock,c.stream.root_state['elapsed_raw_steps']+offset)
  if i==1:check(mods['online481'].physical_identity(t['state_before'])==mods['online481'].physical_identity(root['state']),'FIRST_STATE')
  else:check(same(t['state_before'],transitions[i-2]['state_after']),'FULL_STATE_CHAIN')
  first=row['raw_hull'][0];oldh=t['state_before']['physical']['hull']
  check(first['origin_position']==oldh['position'] and first['COM_linear_velocity']==oldh['velocity'] and first['angle']==oldh['angle'] and first['yaw']==oldh['angular_velocity'],'PRE_PHYSICAL')
  for j,(post,pre) in enumerate(zip(posts,row['raw_hull']),1):
   tires=row['tires'][4*(j-1):4*j]
   check(post['raw_clock']==clock+j and post['time']==pre['time']+1/50 and post['pre_hull']==pre and post['preclip']==tires,'POST_PREFORCE')
   check([(z['raw_tick'],z['wheel']) for z in tires]==[(j,w) for w in range(4)],'WHEEL_ORDER')
  projected,flags=mods['pilot420_backend'].metrics(q,row['tires'],row['raw_hull'],c.line,row['memory_after']['C']['phase'])
  check(set(flags)==set(row['safety']),'SAFETY_REPLAY')
  check(not flags or i==len(c.rows),'CONTINUED_UNSAFE')
  check(not q['terminal'] or i==len(c.rows),'CONTINUED_TERMINAL')
  check(n==4 or q['terminal'],'PARTIAL')
  progress=ledger.progress_m+(projected['arc']-arc+L/2)%L-L/2;arc=projected['arc'];check(progress==row['model_progress']==a['model_progress_m'],'PROGRESS')
  ledger=ledger.advance_prediction(mods['planner419_model_ledger'].ModelPrediction(progress,clock+n,q['finished']))
  check(same(asdict(ledger),t['ledger_after']) and same(asdict(ledger),a['ledger_after']),'LEDGER_AFTER')
  check(not ledger.deadline_missed or i==len(c.rows),'CONTINUED_DEADLINE')
  check(q['position']==posts[-1]['position'] and q['velocity']==posts[-1]['velocity'] and q['time']==posts[-1]['time'],'RETURN_JOIN')
  hist._join_snapshot(t['state_after'],c.stream.root_state,posts[-1],row,clock+n,c.stream.root_state['elapsed_raw_steps']+offset+n)
  check(t['memory_after']==row['memory_after'] or (q['finished'] and t['memory_after']['C']['phase']=='DONE'),'RETURN_MEMORY')
  memory=t['memory_after'];clock+=n;offset+=n;previous=posts[-1];prevrow=row
 check(offset==len(c.stream.posts) and same(asdict(ledger),asdict(c.ledger)) and memory==c.ctrl.memory(),'FINAL_CHAIN')
 last=c.rows[-1];unsafe=last['predicted']['raw_ticks'] if last['safety'] or (last['predicted']['terminal'] and not last['predicted']['finished']) else 0
 tracker,times=hist._replay_observed(c.stream.root_state['finish_tracker'],c.stream.posts,initial.last_clock_tick,c.stream.root_state['physical']['actual_time'],unsafe)
 check(same(tracker,mods['pilot420_backend'].snapshot(c.m)['finish_tracker']),'TRACKER_REPLAY')
 check(ledger.done==(tracker['finish_time_s'] is not None),'FINISH_LEDGER')
 return dict(stage=498,scope='REGISTERED_NOMINAL_ONLY_OWN_HISTORY',actions=len(c.rows),raw_ticks=offset,policy_digest=policy_digest,full_state_memory_RNG_ledger_chain=True,tracker_replayed=True,fake_allocator_receipts=False,actual_execution_allowed=False)

def secondary(rows,line,project):
 out=[]
 for i,row in enumerate(rows,1):
  q=row['predicted'];z=project(line,q['position'],q['velocity'],row['memory_after']['C']['phase']);j=z['index'];edge=np.asarray(line[(j+1)%len(line)])-np.asarray(line[j]);t=edge/np.linalg.norm(edge);normal=np.asarray([-t[1],t[0]]);foot=np.asarray(line[j]) if z['u']==0 else np.asarray(line[(j+1)%len(line)]) if z['u']==1 else np.asarray(line[j])+z['u']*edge;v=np.asarray(q['velocity']);f=np.asarray([-math.sin(q['angle']),math.cos(q['angle'])]);right=np.asarray([math.cos(q['angle']),math.sin(q['angle'])]);front=[x for x in row['tires'] if x['wheel']<2]
  # Preserve tick-aligned components separately; maxima are never vector-summed.
  out.append(dict(hold=i,time=q['time'],speed_m_s=q['speed_m_s'],signed_error_m=float((np.asarray(q['position'])-foot)@normal),heading_deg=math.degrees(math.atan2(t[0]*f[1]-t[1]*f[0],t@f)),normal_velocity_m_s=float(v@normal),body_lateral_velocity_m_s=float(v@right),front_max_abs_lateral_N=max(abs(x['raw_lat_N']) for x in front),front_max_abs_longitudinal_N=max(abs(x['raw_long_N']) for x in front),front_max_force_ratio=max(x['force_ratio'] for x in front),front_clip_count=sum(x['clipped'] for x in front),steering_increment_rad=row['memory_after']['laststeer']-row['memory_before']['laststeer']))
 return out

"""Pure481 finite-policy history authentication. No world or integration calls.

The legacy436 command whitelist is left untouched. Live histories require a
separately hash-bound authorization for every own hold; frozen435 is an explicit,
byte-identical historical fixture only, never authority for a new finite policy.
"""
import copy,hashlib,json,math,struct
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.boundary434 import replay,command,encoded,decode,legacy_digest,tracker_config,FinishLineTracker
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.headroom413_run import metrics
from retry.executor397 import canonical_projection,CoherentExecutor

class HistoryStop481(ValueError):pass
def require(value,reason):
    if not value:raise HistoryStop481('481_HISTORY:'+reason)
def same(a,b):return encoded(a)==encoded(b)
def digest(value):return legacy_digest(value)
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked(path,expected):
    require(type(expected) is str and len(expected)==64,'file_hash_shape')
    require(Path(path).is_file() and file_sha(path)==expected,'receipt_file_hash:'+str(path))
    from retry.io481 import load_receipt
    return load_receipt(path)
def bits(value):
    vector=command(value);packed=struct.pack('<3f',*vector)
    require(tuple(struct.unpack('<3f',packed))==vector,'command_not_exact_float32')
    return packed.hex()

def _join_snapshot(snapshot,root,previous,previous_row,clock,elapsed):
    require(set(snapshot)==set(root) and set(snapshot['physical'])==set(root['physical']),'full_snapshot_schema')
    require(len(snapshot['physical']['wheels'])==4,'full_four_wheel_snapshot')
    p=snapshot['physical'];h=p['hull']
    require(round(p['actual_time']*50)==clock and snapshot['elapsed_raw_steps']==elapsed,'snapshot_clock_elapsed')
    if previous is not None:
        require(p['actual_time']==previous['time'] and h['position']==previous['position'] and h['velocity']==previous['velocity'],'snapshot_post_hull_time_join')
        require(same(snapshot['finish_tracker'],previous['tracker_after']),'snapshot_post_tracker_join')
        require(p['damage']==previous['damage'] and p['unique_tiles']/p['road_count']==previous['progress'],'snapshot_damage_tile_progress')
    if previous_row is not None:
        q=previous_row['predicted']
        require(h['angle']==q['angle'] and h['angular_velocity']==q['angular_velocity'],'snapshot_yaw_angle_join')

def _finite(auth,a,decision):
    mode=auth.get('mode','online');require(mode in ('baseline','online'),'live_mode')
    selected=bits(auth['command']);nominal=bits(auth['nominal']);qstar=bits(auth['qstar'])
    require(selected==bits(a['command']) and nominal==bits(a['nominal']),'own_selected_or_nominal_mismatch')
    commands=auth['commands'];require(type(commands) is dict and 1<=len(commands)<=3,'finite_command_count')
    require(all(key==bits(value) for key,value in commands.items()),'candidate_bit_identity')
    require(auth['selected_key']==selected and selected in commands,'selected_candidate_key')
    q=auth['qstar'];n=auth['nominal'];require(struct.pack('<f',q[0])==struct.pack('<f',n[0]),'qstar_steering_changed')
    require(not(n[1]>0 and n[2]>0),'simultaneous_nominal_pedals')
    active=1 if n[1]>0 else 2 if n[2]>0 else None
    if active is None:
        require(qstar==nominal,'inactive_qstar_changed');expected={nominal}
    else:
        inactive=3-active
        require(struct.pack('<f',q[inactive])==struct.pack('<f',0.) and struct.pack('<f',n[inactive])==struct.pack('<f',0.),'inactive_pedal_not_positive_zero')
        require(0<=q[active]<=n[active],'qstar_outside_original_pedal')
        zero=list(n);zero[active]=0.;expected={nominal,qstar,bits(zero)}
    if mode=='baseline':require(selected==qstar and set(commands)=={qstar},'baseline_not_frozen_qstar')
    else:
        require(set(commands)==expected,'finite_candidate_set_changed')
        options=decision['options'];require(type(options) is dict and set(options)==set(commands),'decision_option_domain')
        admissible=[]
        for key,option in options.items():
            require(bits(option['command'])==key and type(option['aliases']) is list and option['aliases'] and all(type(alias) is str for alias in option['aliases']),'option_command_aliases')
            trace=checked(option['first_path'],option['first_sha256']);rows=trace['rows']
            require(len(rows)<=1,'option_not_single_hold')
            ratios=[t['force_ratio'] for row in rows for t in row['tires']]
            require(all(type(ratio) in (int,float) and math.isfinite(ratio) and ratio>=0 for ratio in ratios),'option_force_numeric')
            score=max((max(0.,ratio-1.) for ratio in ratios),default=None)
            require(option['M80']==score,'option_score_not_observed_raw_max')
            eligible=bool(len(rows)==1 and not rows[0]['safety'] and trace['status'] in ('ACTIVE','FINISHED') and not trace['model_ledger']['deadline_missed'] and (not rows[0]['predicted']['terminal'] or rows[0]['predicted']['finished']))
            require(type(option['valid']) is bool and option['valid']==eligible,'option_eligibility_record')
            if rows:
                require(bits(rows[0]['command'])==key and same(rows[0]['memory_before'],a['memory_before']) and same(rows[0]['memory_after'],a['memory_after']),'option_other_command_or_memory')
            expected_pedal=commands[key][active] if active is not None else 0.
            require(option['active_pedal']==expected_pedal,'option_active_pedal')
            if option['valid']:
                require(score is not None and math.isfinite(score),'valid_option_without_score');admissible.append((score,-expected_pedal,key))
        require(admissible and min(admissible)[2]==selected,'selected_not_exact_minimum_tiebreak')
        require(auth['selected_repeat_exact'] is True,'selected_repeat_not_exact')
        proof=decision['selected_repeat_proof'];require(proof['full_trace_exact'] is True,'repeat_proof_not_exact')
        require(proof['first_path']==options[selected]['first_path'] and proof['first_sha256']==options[selected]['first_sha256'],'selected_first_option_binding')
        require(proof['repeat_path']==auth['repeat_path'] and proof['repeat_sha256']==auth['repeat_sha256'],'repeat_receipt_binding')
        require(Path(proof['first_path']).resolve()!=Path(auth['repeat_path']).resolve(),'selected_repeat_same_file')
        first=checked(proof['first_path'],proof['first_sha256']);repeat=checked(auth['repeat_path'],auth['repeat_sha256'])
        fields=('rows','model_ledger','final_state','controller_memory','status','error')
        require(all(key in first and key in repeat and same(first[key],repeat[key]) for key in fields),'selected_full_repeat_mismatch')
        for key in ('guardian_certificate','finish_ticks'):
            require((key in first)==(key in repeat) and (key not in first or same(first[key],repeat[key])),'selected_repeat_optional_semantics:'+key)
        require(len(first['rows'])==1 and bits(first['rows'][0]['command'])==selected,'selected_repeat_other_hold')
        require(same(first['rows'][0]['memory_before'],a['memory_before']) and same(first['rows'][0]['memory_after'],a['memory_after']),'selected_repeat_other_memory')
        # The own-vs-selected body join is a source-tolerance check upstream;
        # cold restored predictions need not be bit-identical to the warm own hold.
    return mode

def _historical(root,initial,posts,actions,state,memory,ledger,auths):
    require(type(auths) is list and len(auths)==1 and auths[0].get('mode')=='historical435','historical_fixture_marker')
    proof=auths[0];sources=proof['sources'];require(type(sources) is dict and len(sources)>=4,'historical_sources_missing')
    for path,expected in sources.items():checked(path,expected)
    hp=Path(proof['history_path']);require(hp.name=='parent_P-observer-private.json' and hp.parent.name=='stage435','historical_not_saved435')
    require(str(hp) in sources and proof['history_sha256']==sources[str(hp)],'historical_history_hash')
    observed=checked(hp,proof['history_sha256']);number=observed['link']['world_number'];folder=hp.parent
    paths=[folder/('world'+str(number)+'-before-constructor-private.json'),folder/'parent_P-private.json',folder/'P_decision55-context-stop-private.json']
    require(all(str(path) in sources for path in paths),'historical_full_source_set')
    constructor,parent,stop=[checked(path,sources[str(path)]) for path in paths]
    require(same(root,constructor['state']) and same(initial,observed['link']['model_ledger']),'historical_root_or_initial_changed')
    require(same(posts,observed['posts']) and same(actions,observed['actions']),'historical_observed_history_changed')
    observed_current=copy.deepcopy(state);frozen_current=copy.deepcopy(stop['live_parent'])
    # This sole structural diagnostic is explicitly omitted by the known cold
    # restoration contract; preserve every other physical/tracker/clock field.
    observed_current['physical'].pop('source_world_contacts',None);frozen_current['physical'].pop('source_world_contacts',None)
    require(same(observed_current,frozen_current) and same(memory,stop['memory_before_nominal']) and same(ledger,parent['model_ledger']),'historical_current_boundary_changed')
    return dict(mode='FROZEN435_ONLY',source_count=len(sources),history_sha256=proof['history_sha256'])

def _replay_observed(root_tracker,posts,clock,t,unsafe_tail):
    """Use434 for safe prefix; retain a typed stopped final hold without promotion.

   434.safe_tick intentionally rejects unsafe samples. For an unsafe or source
    nonfinish-terminal final hold, replay unchanged tracker algebra on final1..4
    posts and validate its exact safety flags against its frozen row downstream.
    This never permits another action after that unsafe hold.
    """
    if not unsafe_tail:return replay(root_tracker,posts,clock,t)
    prefix=posts[:-unsafe_tail];tail=posts[-unsafe_tail:]
    if prefix:
        initial,times=replay(root_tracker,prefix,clock,t);clock=prefix[-1]['raw_clock'];t=prefix[-1]['time']
    else:initial=copy.deepcopy(root_tracker);times={}
    tracker=FinishLineTracker(**decode(encoded(initial)))
    for index,row in enumerate(tail):
        require(type(row['raw_clock']) is int and row['raw_clock']==clock+1 and row['time']==t+1/50,'unsafe_tail_raw_clock_time')
        require(row['phase'] in ('FIRST_LAP','FINISH_CONFIRM') and 0<=row['progress']<=1,'unsafe_tail_phase_progress')
        require(tracker.finish_time_s is None,'unsafe_tail_after_official_finish')
        tracker.update(tuple(row['position']),tuple(row['velocity']),row['progress'],row['time'])
        require(same(asdict(tracker),row['tracker_after']),'unsafe_tail_tracker_replay')
        # A typed final unsafe/nonfinish-terminal hold may cancel a pending
        # event through the unchanged source algebra. Preserve that outcome;
        # the proof grants neither continuation nor completion authority.
        times[row['time']]=row['raw_clock'];clock=row['raw_clock'];t=row['time']
        if tracker.finish_time_s is not None:require(index==len(tail)-1,'unsafe_tail_confirmation_not_last')
    return asdict(tracker),times

def validate_history(root_state,initial_ledger,posts,actions,authorizations,state,memory,ledger,line,policy_digest,*,historical=False):
    """Authenticate observed own history, with no new physics or actual authority.

    Every live authorization binds a hash-checked context receipt containing
    complete state/before/after/ledger/RNG/nominal/qstar/allocation_number. The
    io481 reader expands authenticated state references back to exact payloads.
    """
    require(type(policy_digest) is str and len(policy_digest)==64 and all(c in '0123456789abcdef' for c in policy_digest),'policy_digest')
    require(type(posts) is list and type(actions) is list and posts and actions,'missing_observed_history')
    # Serialization checks reject nonfinite numbers and unsupported values.
    for value in (root_state,initial_ledger,posts,actions,state,memory,ledger):encoded(value)
    initial=ForecastLedger(**initial_ledger);current=ForecastLedger(**ledger)
    require(not initial.done and not initial.deadline_missed,'initial_stop')
    root_tracker=root_state['finish_tracker'];require(root_tracker['candidate_crossing_time_s'] is None and root_tracker['finish_time_s'] is None,'old_root_event')
    require(round(root_state['physical']['actual_time']*50)==initial.last_clock_tick,'root_raw_clock')
    historical_proof=_historical(root_state,initial_ledger,posts,actions,state,memory,ledger,authorizations) if historical else None
    if not historical:require(type(authorizations) is list and len(authorizations)==len(actions),'missing_action_authorizations')
    last_frozen=actions[-1]['frozen_row'];last_q=last_frozen['predicted']
    unsafe_tail=last_q['raw_ticks'] if last_frozen['safety'] or (last_q['terminal'] and not last_q['finished']) else 0
    final,times=_replay_observed(root_tracker,posts,initial.last_clock_tick,root_state['physical']['actual_time'],unsafe_tail)
    require(tracker_config(final)==tracker_config(root_tracker) and same(final,state['finish_tracker']),'final_tracker_or_config')
    arr=np.asarray(line,float);require(arr.ndim==2 and arr.shape[1]==2 and np.isfinite(arr).all(),'line_schema')
    lengths=np.linalg.norm(np.roll(arr,-1,axis=0)-arr,axis=1);require(np.all(lengths>0),'line_segments');L=float(sum(lengths))
    model=initial;clock=initial.last_clock_tick;offset=0;memory_chain=actions[0]['memory_before'];previous=None;previous_row=None;token=None;allocations=[];rng_digest=None
    hull=root_state['physical']['hull'];previous_arc=canonical_projection(arr,hull['position'],hull['velocity'],memory_chain['C']['phase'])['arc']
    for index,a in enumerate(actions,1):
        row=a['frozen_row'];q=row['predicted'];n=q['raw_ticks'];require(type(n) is int and 1<=n<=4,'raw_action_length')
        chunk=posts[offset:offset+n];require(len(chunk)==n and a['action_index']==index and chunk[-1]['raw_clock']==a['raw_end_clock']==clock+n,'own_action_clock_index')
        require(same(a['memory_before'],memory_chain) and same(row['memory_before'],memory_chain) and same(row['memory_after'],a['memory_after']),'memory_chain')
        require(bits(a['command'])==bits(row['command']),'frozen_own_command')
        if historical:
            nominal=command(a['nominal']);require(command(a['command']) in (nominal,(nominal[0],1.,0.),(0.,0.,0.30000001192092896)),'historical436_recipe_whitelist')
        else:
            auth=authorizations[index-1]
            require(auth['policy_digest']==policy_digest and auth['action_index']==index,'authorization_policy_action')
            require(type(auth['parent_token']) is str and auth['parent_token'],'authorization_parent_token')
            if token is None:token=auth['parent_token']
            require(auth['parent_token']==token,'parent_token_changed')
            require(auth['before_memory_digest']==digest(a['memory_before']) and auth['after_memory_digest']==digest(a['memory_after']) and auth['ledger_before_digest']==digest(asdict(model)),'authorization_memory_ledger_digest')
            require(type(auth['allocation_number']) is int and auth['allocation_number']>0,'allocation_number')
            require(not allocations or auth['allocation_number']>allocations[-1],'allocation_reused_or_reordered');allocations.append(auth['allocation_number'])
            decision=checked(auth['decision_path'],auth['decision_sha256'])
            expected_auth={k:v for k,v in auth.items() if k not in ('decision_path','decision_sha256')}
            require(same(decision['authorization'],expected_auth),'decision_authorization_changed')
            context=checked(auth['context_path'],auth['context_sha256']);before=context['state']
            require(same(context['before'],a['memory_before']) and same(context['after'],a['memory_after']) and same(context['ledger'],asdict(model)),'context_memory_or_ledger')
            require(bits(context['nominal'])==bits(auth['nominal']) and bits(context['qstar'])==bits(auth['qstar']) and context['allocation_number']==auth['allocation_number'],'context_command_or_allocation')
            allocation_input=checked(context['allocation_input_path'],context['allocation_input_sha256'])
            allocation_proof=checked(context['allocation_proof_path'],context['allocation_proof_sha256'])
            for packet in (allocation_input,allocation_proof):
                require(packet['number']==context['allocation_number'] and packet['label']==context['label'] and packet['action']==context['index']+1,'allocation_receipt_identity')
                require(packet['phase']==context['after']['C']['phase'],'allocation_receipt_phase')
            require(bits(allocation_input['nominal'])==bits(auth['nominal']) and same(allocation_input['current_wheels'],context['wheels']),'allocation_current_input_binding')
            require(bits(allocation_proof['command'])==bits(auth['qstar']),'allocation_proved_qstar_binding')
            rng=context['RNG'];require(type(rng['global_pickle']) is bytes and hashlib.sha256(rng['global_pickle']).hexdigest()==rng['digest'],'context_RNG_payload')
            if rng_digest is None:rng_digest=rng['digest']
            require(rng['digest']==rng_digest,'own_history_global_RNG_changed')
            require(auth['state_before_digest']==digest(before),'authorization_full_state_digest')
            if index==1:require(same(before,root_state),'first_state_not_root')
            _join_snapshot(before,root_state,previous,previous_row,clock,root_state['elapsed_raw_steps']+offset)
            _finite(auth,a,decision)
        before_tracker=root_tracker if previous is None else previous['tracker_after'];pending=before_tracker['candidate_crossing_time_s']
        before_phase=a['memory_before']['C']['phase'];after_phase=a['memory_after']['C']['phase']
        require(before_phase in ('FIRST_LAP','FINISH_CONFIRM') and (before_phase!='FINISH_CONFIRM' or pending is not None),'phase_without_registered_pending')
        require(after_phase==('FINISH_CONFIRM' if pending is not None else before_phase) and all(p['phase']==after_phase for p in chunk),'source_act_phase_order')
        require(len(row['raw_hull'])==n and len(row['tires'])==4*n,'raw_hull_tire_coverage')
        first=row['raw_hull'][0];old_hull=root_state['physical']['hull'] if previous is None else None
        require(first['time']==(root_state['physical']['actual_time'] if previous is None else previous['time']),'raw_pre_time_join')
        require(first['origin_position']==(old_hull['position'] if previous is None else previous['position']) and first['COM_linear_velocity']==(old_hull['velocity'] if previous is None else previous['velocity']),'raw_pre_physical_join')
        require(first['angle']==(old_hull['angle'] if previous is None else previous_row['predicted']['angle']) and first['yaw']==(old_hull['angular_velocity'] if previous is None else previous_row['predicted']['angular_velocity']),'raw_pre_angle_yaw_join')
        for local,(post,pre) in enumerate(zip(chunk,row['raw_hull']),1):
            tires=row['tires'][4*(local-1):4*local]
            require(post['time']==pre['time']+1/50 and post['pre_hull']==pre and same(post['preclip'],tires),'post_preclip_frozen_join')
            require([(t['raw_tick'],t['wheel']) for t in tires]==[(local,w) for w in range(4)],'wheel_tick_order')
        projected,flags=metrics(q,row['tires'],row['raw_hull'],arr,after_phase)
        require(set(flags)==set(row['safety']),'frozen_safety_flags_changed')
        require(not flags or index==len(actions),'continued_after_unsafe_own_hold')
        observed_flags=set()
        for post in chunk:
            require(math.isfinite(post['path_error_m']) and post['path_error_m']>=0,'post_path_numeric')
            require(math.isfinite(post['damage']) and post['damage']>=0 and type(post['wheel_road_contacts']) is int and 0<=post['wheel_road_contacts']<=4,'post_physical_domain')
            if post['path_error_m']>3:observed_flags.add('path_error_over3m')
            if post['damage']>0:observed_flags.add('damage_increase')
            if post['collision']:observed_flags.add('collision_or_obstacle')
            if post['grass'] or post['wheel_road_contacts']<4:observed_flags.add('road_loss_or_grass')
        require(observed_flags==set(row['safety'])-{'reverse'},'observer_frozen_safety_join')
        require(q['position']==chunk[-1]['position'] and q['velocity']==chunk[-1]['velocity'] and q['time']==chunk[-1]['time'],'predicted_observed_post_join')
        finished=chunk[-1]['tracker_after']['finish_time_s'] is not None
        require(bool(q['finished'])==finished,'official_finish_disagreement')
        require(q.get('finish_time_s')==chunk[-1]['tracker_after']['finish_time_s'] and q.get('qualified_time_s')==chunk[-1]['tracker_after']['qualified_time_s'],'predicted_tracker_event_join')
        require(not q['terminal'] or index==len(actions),'continued_after_terminal_hold')
        if n<4:require(q['terminal'] and index==len(actions),'partial_nonterminal_hold')
        progress=model.progress_m+(projected['arc']-previous_arc+L/2)%L-L/2;previous_arc=projected['arc']
        require(progress==a['model_progress_m']==row['model_progress'],'canonical_progress_chain')
        model=model.advance_prediction(ModelPrediction(progress,a['raw_end_clock'],finished))
        require((not model.deadline_missed or index==len(actions)) and same(asdict(model),a['ledger_after']),'full_forecast_ledger_chain_or_continued_after_deadline')
        clock=a['raw_end_clock'];offset+=n;memory_chain=a['memory_after'];previous=chunk[-1];previous_row=row
    require(offset==len(posts) and clock==current.last_clock_tick and same(asdict(model),ledger),'unaccounted_history_or_final_ledger')
    _join_snapshot(state,root_state,previous,previous_row,clock,root_state['elapsed_raw_steps']+len(posts))
    if not same(memory_chain,memory):
        after_done=copy.deepcopy(memory_chain);after_done['C']['phase']='DONE'
        require(current.done and final['finish_time_s'] is not None and same(after_done,memory),'final_memory_not_nominal_or_legitimate_DONE')
    event=final['finish_time_s'] if final['finish_time_s'] is not None else final['candidate_crossing_time_s'];qualified=final['qualified_time_s']
    if event is not None:
        require(event in times and initial.last_clock_tick<times[event]<=clock and qualified is not None and qualified<=event<=state['physical']['actual_time'],'event_not_authenticated_in_own_history')
        if final['finish_time_s'] is None:
            require(not current.done and final['departed_start_area'] and final['crossing_from_back'],'pending_source_registration')
            h=state['physical']['hull'];CoherentExecutor._confirm_valid(None,dict(time=state['physical']['actual_time'],pos=h['position'],vel=h['velocity']),final)
        else:require(current.done and final['candidate_crossing_time_s'] is None and not final['crossing_from_back'],'own_finish_ledger_tracker')
    else:require(not current.done,'done_without_official_event')
    return dict(stage=481,scope='FROZEN435_HISTORY_ONLY' if historical else 'OWN_FINITE_POLICY_HISTORY',policy_digest=policy_digest,parent_token=token,
                actions=len(actions),raw_ticks=len(posts),root_raw_clock=initial.last_clock_tick,current_raw_clock=clock,
                state_digest=digest(state),memory_digest=digest(memory),ledger_digest=digest(ledger),event_time_s=event,
                event_raw_clock=None if event is None else times[event],pending=final['candidate_crossing_time_s'] is not None,
                own_model_finished=current.done,physical_safe=not bool(actions[-1]['frozen_row']['safety']),progress_deadline_missed=current.deadline_missed,
                terminal_nonfinish=bool(actions[-1]['frozen_row']['predicted']['terminal'] and not current.done),
                actual_DONE_allowed=False,actual_execution_allowed=False,historical_proof=historical_proof)

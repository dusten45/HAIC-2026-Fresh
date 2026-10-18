"""567 late-segment finite-difference screen and bounded fresh-feedback test."""
import copy, datetime, hashlib, json, math, signal, time, traceback
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np

from retry.clip561_core import atomic_write, prefix_slacks
import retry.handoff562_model as d
import retry.structure537_control as policy
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
from retry.closure524_control import tick as source_tick
from retry.speed516_control import force_rows
from retry.corner515_model import margin
from retry.lap518_finish import hull_pose
from core.finish_line import FinishLineTracker

G=Path(__file__).resolve().parents[1]; PRIV=Path('/workspace/haic-response567-private')
CONTRACT=G/'retry/late567_contract.json'
TAPE=Path('/workspace/haic-response565-private/final-tape-private.json')
STATIC=Path('/workspace/haic-response515-private/collected-map-state-private.json')
PATHS=Path('/workspace/haic-response551-private/frozen-paths-private.json')
LEDGER=Path('/workspace/haic-response519-private/model-ledger-private.json')
rd=lambda p:json.loads(p.read_text()); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canon=lambda x:json.loads(json.dumps(d.plain(x)))

class Meter:
    def __init__(self, study, limit, label):
        self.s=study; self.counter=[0]; self.limit=limit; self.label=label
        self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,body_checks=0,max_body=0.)
        self.cpu=time.process_time(); self.wall=time.perf_counter()
    def guard(self,reserve=0):
        if self.counter[0]>self.limit or self.cost['force_evaluations']+reserve>4*self.limit or self.cost['geometry_checks']>self.limit*2:
            raise RuntimeError('567_SOURCE_WORK_CAP:'+self.label)
        if time.process_time()-self.cpu>250 or time.perf_counter()-self.wall>350: raise RuntimeError('567_CASE_TIME_CAP:'+self.label)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.s.deadline): raise RuntimeError('567_DEADLINE')
    def force(self,root,action): self.guard(4); return force_rows(root,action)
    def tick(self,root,gas,brake,index,counter):
        self.guard(); after=source_tick(root,gas,brake,self.s.index,counter)
        body=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels))
        self.cost['body_checks']+=1; self.cost['max_body']=max(self.cost['max_body'],body)
        if not math.isfinite(body) or body>=100: raise RuntimeError('567_MODEL_BODY_DOMAIN')
        return after
    def geometry(self,root):
        self.guard(); self.cost['geometry_checks']+=1
        if self.cost['geometry_checks']>self.limit*2: raise RuntimeError('567_GEOMETRY_CAP')
        return margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])

class Study:
    def __init__(self):
        self.contract=rd(CONTRACT); self.deadline=self.contract['deadline_utc']; self.static=rd(STATIC); self.paths=rd(PATHS); self.tape=rd(TAPE); self.ledger=rd(LEDGER)
        self.rows=self.tape['rows']; self.commands={int(x['index']):np.asarray(x['action'],np.float32) for x in self.tape['commands']}
        self.index=bounds(self.static['root']['roads']); self.edge=boundary_index(self.static['boundary']); self.base_row=next(r for r in self.rows if r['global_raw_after']==528)
        root=d.load_root(dict(self.base_row['root_without_roads'],roads=self.static['root']['roads'])); visited=set(self.ledger['initial_visited'])
        for row in self.rows[:528]:
            rr=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']))
            for ids in rr.current_contacts: visited.update(ids)
        self.initial=dict(root=root,visited=visited,tracker=FinishLineTracker(**self.base_row['tracker']),elapsed=self.base_row['episode_after_s'],global_raw=528,progress=self.base_row['progress'],launch=[55,384],tracking=list(self.base_row['proposed_history']))
        tr=self.initial['tracker']; self.finish_center=tuple(tr.center); self.finish_forward=tuple(tr.forward)
        self.x0=np.array([v for i in range(133,153) for v in (float(self.commands[i][0]),float(self.commands[i][1]-self.commands[i][2]))],dtype=np.float64)
        self.aggregate=dict(ticks=80,force=320,geometry=80,cpu=1.029738328,wall=1.029843956,fd_columns=0,candidates=0,feedback_calls=0)
        self.start_hash=hashlib.sha256(json.dumps({'root':self.base_row['root_without_roads'],'tracker':self.base_row['tracker'],'progress':self.base_row['progress'],'tracking':self.initial['tracking'],'visited':sorted(visited)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def actions(self,x):
        return {133+j:np.asarray([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(20)}
    def run_fixed(self,x,label,limit=400):
        state=copy.deepcopy(self.initial); phase=Meter(self,limit,label); actual=[]; ratios=[]; g=[]; last_s=state['progress']; plane=None; s900=None; longitudinal_prev=None
        controlled=self.actions(x)
        tape={**controlled,**{i:a for i,a in self.commands.items() if i>=153}}
        tr=state['tracker']; forward=self.finish_forward; center=self.finish_center
        try:
            for i in sorted(tape):
                action=tape[i]
                for raw in range(1,5):
                    prev_root=state['root']; prev_s=state['progress']; oldtime=1.02+state['elapsed']
                    rec,reason=d.Study.raw(self,state,action,i,raw,phase); actual.append(rec)
                    if reason: return dict(label=label,safe=False,reason=reason,state=state,rows=actual,phase=phase)
                    ratios.extend(z['ratio'] for z in rec['forces'])
                    delta=rec['progress']-prev_s; lim=max(5.,2*math.dist(prev_root.center,state['root'].center))
                    g.extend([rec['margin']-.5,3.-rec['path_error'],4.85-rec['reference_overspeed'],*[1.059-z['ratio'] for z in rec['forces']],100.-rec['body'],delta+.5,lim-delta])
                    rel=(state['root'].center[0]-center[0],state['root'].center[1]-center[1]); long=rel[0]*forward[0]+rel[1]*forward[1]
                    if longitudinal_prev is not None and plane is None and longitudinal_prev[1]<0<=long:
                        a=-longitudinal_prev[1]/(long-longitudinal_prev[1]); plane=longitudinal_prev[0]+a*(oldtime-longitudinal_prev[0])
                    longitudinal_prev=(1.02+state['elapsed'],long)
                    if s900 is None and prev_s<900<=state['progress']:
                        a=(900-prev_s)/(state['progress']-prev_s);s900=oldtime+a*.02
            order=prefix_slacks(ratios,*self.initial['tracking'])
            safe=bool(min(g)>=-1e-12 and min(order)>=-1e-12 and state['tracker'].finish_time_s is not None)
            return dict(label=label,safe=safe,reason=None if safe else 'NO_SAFE_FINISH',state=state,rows=actual,g=np.asarray(g),order=order,plane=plane,s900=s900,official_tracker_raw=(state['global_raw'] if state['tracker'].finish_time_s is not None else None),official_finish_s=state['tracker'].finish_time_s-1.02 if state['tracker'].finish_time_s is not None else None,phase=phase)
        finally: self.add_cost(phase)
    def run_program(self,x,label):
        state=copy.deepcopy(self.initial); phase=Meter(self,400,label); actual=[]; acts=self.actions(x)
        try:
            for i in range(133,153):
                for raw in range(1,5):
                    rec,reason=d.Study.raw(self,state,acts[i],i,raw,phase);actual.append(rec)
                    if reason:return dict(safe=False,reason=reason,state=state,rows=actual,phase=phase)
            return dict(safe=True,state=state,rows=actual,phase=phase)
        finally:self.add_cost(phase)
    def add_cost(self,p):
        self.aggregate['ticks']+=p.counter[0]; self.aggregate['force']+=p.cost['force_evaluations']; self.aggregate['geometry']+=p.cost['geometry_checks']; self.aggregate['cpu']+=time.process_time()-p.cpu; self.aggregate['wall']+=time.perf_counter()-p.wall
    def feedback(self,program,label):
        state=copy.deepcopy(program['state']); phase=Meter(self,20000,label); actual=[]; commands=[]; oldtick,oldforce=policy.tick,policy.force_rows
        try:
            for index in range(153,368):
                phase.guard(6400); geom=policy.geometry_context(self.static,65000)
                policy.tick=phase.tick; policy.force_rows=phase.force
                try: action,detail=policy.choose(state['root'],self.paths['candidate'],self.paths['backup'],state['progress'],phase.counter,phase.cost,20000,history=tuple(state['tracking']),geometry=geom)
                finally: policy.tick,policy.force_rows=oldtick,oldforce
                if action is None: return dict(safe=False,reason='NO_ADMISSIBLE_ACTION',state=state,rows=actual,commands=commands,phase=phase)
                commands.append(dict(index=index,action=action.tolist(),detail=detail))
                for raw in range(1,5):
                    rec,reason=d.Study.raw(self,state,action,index,raw,phase); actual.append(rec)
                    if reason: return dict(safe=False,reason=reason,state=state,rows=actual,commands=commands,phase=phase)
                    if state['tracker'].finish_time_s is not None: return dict(safe=True,reason='SOURCE_FINISH',state=state,rows=actual,commands=commands,phase=phase)
                    if 50+state['global_raw']>=1224: return dict(safe=False,reason='SOURCE_TIME_LIMIT',state=state,rows=actual,commands=commands,phase=phase)
            return dict(safe=False,reason='POLICY_LIMIT',state=state,rows=actual,commands=commands,phase=phase)
        finally: self.add_cost(phase)
    def replay(self,x,commands,label):
        """Independent deterministic replay from the locked raw-528 state."""
        state=copy.deepcopy(self.initial); phase=Meter(self,1200,label); recs=[]; oldtick,oldforce=policy.tick,policy.force_rows
        tape={**self.actions(x),**{q['index']:np.asarray(q['action'],np.float32) for q in commands}}
        try:
            for i in sorted(tape):
                a=tape[i]
                for k in range(1,5):
                    row,reason=d.Study.raw(self,state,a,i,k,phase);recs.append(row)
                    if reason: raise RuntimeError('independent replay safety mismatch '+reason)
                    if state['tracker'].finish_time_s is not None: break
                if state['tracker'].finish_time_s is not None: break
            return state,recs,phase
        finally: self.add_cost(phase)

def main():
    PRIV.mkdir(mode=0o700,exist_ok=True)
    # Refuse a second calibration run: its cost and frozen margins are part of the contract ledger.
    if (PRIV/'continue-error-private.json').exists(): raise RuntimeError('567 preregistered calibration already stopped; retry prohibited')
    if (PRIV/'calibration-private.json').exists(): raise RuntimeError('567 calibration already exists')
    s=Study(); start=time.perf_counter(); cpu=time.process_time(); original_tick,original_force=policy.tick,policy.force_rows
    try:
        base=s.run_fixed(s.x0,'locked-incumbent-calibration')
        if not base['safe']: raise RuntimeError('locked late trajectory failed exact gates: '+str(base['reason']))
        if base['g'].shape[0] % 1 or len(base['order'])==0: raise RuntimeError('567 malformed constraint vectors')
        J=[]; JO=[]; steps=[]; fd_records=[]
        scales=np.tile([.003,.03],20)
        for j in range(40):
            h=1e-5 if j%2==0 else 1e-4; xp=s.x0.copy(); xp[j]=float(np.float32(xp[j]+h)); dh=xp[j]-s.x0[j]
            if dh==0: raise RuntimeError('567 float32-zero FD step')
            ev=s.run_fixed(xp,f'567-FD-{j:02d}')
            if not ev['safe'] or ev['g'].shape!=base['g'].shape or ev['order'].shape!=base['order'].shape: raise RuntimeError('567 FD gate/shape failure at '+str(j))
            J.append((ev['g']-base['g'])/dh); JO.append((ev['order']-base['order'])/dh);steps.append(dh);fd_records.append(dict(column=j,step=dh,plane_s=ev['plane'],s900_s=ev['s900']))
        J=np.asarray(J).T; JO=np.asarray(JO).T; s.aggregate['fd_columns']=40
        # Two fixed opposite checks are evaluated before any proposal and never changed.
        patterns=[]
        for sign,name in ((1.,'calibration-plus'),(-1.,'calibration-minus')):
            x=s.x0+sign*.05*scales
            for j in range(0,40,2): x[j]=np.float32(x[j])
            x=x.astype(np.float32).astype(np.float64)
            ev=s.run_fixed(x,name)
            if not ev['safe'] or ev['g'].shape!=base['g'].shape or ev['order'].shape!=base['order'].shape: raise RuntimeError('567 fixed calibration gate/shape failure '+name)
            dx=x-s.x0; pred=base['g']+J@dx; opred=base['order']+JO@dx
            patterns.append(dict(name=name,x=x,ev=ev,g_over=np.maximum(0.,pred-ev['g']),o_over=np.maximum(0.,opred-ev['order']),plane_pred=base['plane']+float(np.dot(np.asarray([0.]),np.asarray([0.])))))
            patterns[-1]['plane_pred']=base['plane']+float(np.dot((np.asarray([0.]) if False else np.zeros(1)),np.zeros(1)))
        # Fixed coordinatewise empirical interiors, with propagated float32 ULP and binary64 floor.
        ulp=np.array([abs(float(np.spacing(np.float32(v)))) for v in s.x0])
        quant=np.abs(J)@ulp; oquant=np.abs(JO)@ulp
        gerr=np.maximum(patterns[0]['g_over'],patterns[1]['g_over']); oerr=np.maximum(patterns[0]['o_over'],patterns[1]['o_over'])
        gmargin=2*(gerr+quant+4*np.finfo(float).eps); omargin=2*(oerr+oquant+4*np.finfo(float).eps)
        # Time finite differences use the same actual float32 columns.
        jt=[]
        for j,dh in enumerate(steps):
            # Values are retained below in the raw calibration tape; recompute scalar slope from FD record output.
            jt.append((fd_records[j]['plane_s']-base['plane'])/dh)
        jt=np.asarray(jt); grad_z=jt*scales; norm=float(np.linalg.norm(grad_z))
        if not math.isfinite(norm) or norm==0: raise RuntimeError('567 no finite local descent direction')
        direction=-grad_z/norm*.05; xtrial=(s.x0+direction*scales).astype(np.float32).astype(np.float64)
        if np.array_equal(xtrial.astype(np.float32),s.x0.astype(np.float32)): raise RuntimeError('567 duplicate/float32-zero proposal')
        trial=s.run_fixed(xtrial,'567-small-refutation-candidate')
        predicted=base['plane']+float(np.dot(jt,xtrial-s.x0))
        interior=bool(trial['safe'] and np.all(trial['g']>=gmargin) and np.all(trial['order']>=omargin) and trial['plane'] is not None and predicted<base['plane']-1e-6)
        atomic_write(PRIV/'calibration-private.json',dict(start_hash=s.start_hash,baseline={k:base[k] for k in ('plane','s900','official_finish_s','official_tracker_raw')},FD_steps=steps,FD_plane_times=[q['plane_s'] for q in fd_records],calibrations=[dict(name=q['name'],plane=q['ev']['plane'],s900=q['ev']['s900'],max_g_over=float(max(q['g_over'])),max_order_over=float(max(q['o_over']))) for q in patterns],physical_interior_max=float(max(gmargin)),prefix_interior_max=float(max(omargin)),proposal=xtrial.tolist(),proposal_predicted_plane_s=predicted,proposal_actual_plane_s=trial['plane'],proposal_actual_s900_s=trial['s900'],proposal_physical_and_prefix_interior=interior,proposal_g_min=float(min(trial['g'])) if trial.get('g') is not None else None,proposal_order_min=float(min(trial['order'])) if trial.get('order') is not None else None,source_cost=dict(s.aggregate),input_hashes={str(p):sha(p) for p in (TAPE,STATIC,PATHS,LEDGER)}))
        result={'completed':True,'start_hash':s.start_hash,'local_baseline_center_plane_s':base['plane'],'local_baseline_s900_s':base['s900'],'official_tracker_finish_s':base['official_finish_s'],'official_tracker_raw':base['official_tracker_raw'],'FD_columns':40,'fixed_calibration_checks':2,'fixed_interior_physical_max':float(max(gmargin)),'fixed_interior_prefix_max':float(max(omargin)),'small_proposal_center_plane_predicted_s':predicted,'small_proposal_center_plane_actual_s':trial['plane'],'small_proposal_s900_s':trial['s900'],'proposal_passed_exact_safety_and_interior':interior,'candidate_full_feedback_calls':0,'candidate_status':'AWAITING_FEEDBACK_GATE' if interior else 'STOPPED_AT_LOCAL_GATE','new_native_actions':0,'new_resets':0,'HOLDOUT':0,'SEALED':0,'paid_compute':0,'reserve_used':0,'DEV_only':True,'cost':s.aggregate,'cpu_s':time.process_time()-cpu,'wall_s':time.perf_counter()-start}
        atomic_write(PRIV/'local-calibration-private.json',dict(baseline_rows=base['rows'],fd=fd_records,calibration=[q['ev']['rows'] for q in patterns],proposal_rows=trial['rows'],proposal_state=d.short(trial['state']['root'])))
        atomic_write(G/'retry/late567_calibration_result.json',result)
        atomic_write(G/'retry/late567_cost.json',dict(initial_baseline_replay_ticks=80,local_and_calibration=s.aggregate,candidate_feedback_calls=0,independent_replay_ticks=0,aggregate_ticks=s.aggregate['ticks'],aggregate_cpu_s=s.aggregate['cpu'],aggregate_wall_s=s.aggregate['wall'],contract_caps=rd(CONTRACT)['cost_caps']))
        print(json.dumps(result,indent=2))
        if not interior: return
        # Fresh feedback continuation from the exact candidate handoff.
        program=s.run_program(xtrial,'567-feedback-program')
        # The local program replay produces the same physical checkpoint; require it before chooser starts.
        if not program['safe']: raise RuntimeError('567 candidate program failed exact safety')
        if not (program['state']['global_raw']==trial['state']['global_raw'] and canon(d.short(program['state']['root']))==canon(d.short(trial['state']['root']))): raise RuntimeError('567 candidate handoff mismatch')
        fb=s.feedback(program,'567-fresh-feedback')
        s.aggregate['feedback_calls']+=1
        if not fb['safe']: result.update(candidate_status='FRESH_FEEDBACK_FAILED',feedback_failure=fb['reason'])
        else:
            plane=None; s900=None; allrows=program['rows']+fb['rows']; allroots=[]
            for row in allrows:
                rr=d.load_root(dict(row['root_without_roads'],roads=s.static['root']['roads'])); allroots.append(rr)
            for k in range(1,len(allroots)):
                p0,p1=allroots[k-1].center,allroots[k].center; f=s.finish_forward;c=s.finish_center
                l0=(p0[0]-c[0])*f[0]+(p0[1]-c[1])*f[1];l1=(p1[0]-c[0])*f[0]+(p1[1]-c[1])*f[1]
                if plane is None and l0<0<=l1: plane=1.02+allrows[k-1]['episode_after_s']+(-l0/(l1-l0))*.02
                if s900 is None and allrows[k-1]['progress']<900<=allrows[k]['progress']:
                    frac=(900-allrows[k-1]['progress'])/(allrows[k]['progress']-allrows[k-1]['progress']);s900=1.02+allrows[k-1]['episode_after_s']+frac*.02
            promoted=bool(fb['state']['tracker'].finish_time_s is not None and plane is not None and plane<base['plane']-1e-6)
            result.update(candidate_status='PROMOTED_SAFE_DIAGNOSTIC' if promoted else 'SAFE_BUT_NOT_PROMOTED',fresh_feedback_safe_finish=fb['state']['tracker'].finish_time_s is not None,fresh_feedback_center_plane_s=plane,fresh_feedback_s900_s=s900,official_tracker_finish_s=fb['state']['tracker'].finish_time_s-1.02 if fb['state']['tracker'].finish_time_s else None,official_tracker_candidate_raw=fb['state']['global_raw'],official_raw_improved=bool(fb['state']['global_raw']<662),promoted=promoted)
            replay_state,replay_rows,replay_phase=s.replay(xtrial,fb['commands'],'567-independent-command-replay')
            same=len(replay_rows)==len(program['rows'])+len(fb['rows']) and all(canon(a['root_without_roads'])==canon(b['root_without_roads']) and canon(a['forces'])==canon(b['forces']) for a,b in zip(replay_rows,program['rows']+fb['rows']))
            cp=canon(d.short(replay_state['root']))==canon(d.short(fb['state']['root'])) and canon(asdict(replay_state['tracker']))==canon(asdict(fb['state']['tracker']))
            if not (same and cp): raise RuntimeError('567 independent source replay mismatch')
            result['independent_replay_exact']=True
            atomic_write(PRIV/'candidate-private.json',dict(x=xtrial.tolist(),program_rows=program['rows'],feedback_rows=fb['rows'],commands=fb['commands'],checkpoint=d.short(fb['state']['root']),tracker=asdict(fb['state']['tracker']),independent_replay_rows=replay_rows))
        atomic_write(G/'retry/late567_calibration_result.json',result)
        atomic_write(G/'retry/late567_cost.json',dict(initial_baseline_replay_ticks=80,source_cost=s.aggregate,aggregate_ticks=s.aggregate['ticks'],aggregate_cpu_s=s.aggregate['cpu'],aggregate_wall_s=s.aggregate['wall'],contract_caps=rd(CONTRACT)['cost_caps']))
        print(json.dumps(result,indent=2))
    except BaseException as e:
        atomic_write(PRIV/'continue-error-private.json',dict(error=type(e).__name__+': '+str(e),traceback=traceback.format_exc(),cost=s.aggregate if 's' in locals() else None))
        atomic_write(G/'retry/late567_calibration_result.json',dict(completed=False,error=type(e).__name__+': '+str(e),cost=s.aggregate if 's' in locals() else None))
        raise
    finally:
        policy.tick,policy.force_rows=original_tick,original_force

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw): raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    main()

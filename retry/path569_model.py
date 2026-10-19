"""Finite-segment vector tube and seed-feasible displacement error budgets."""
import copy,datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.late568_model as base
from retry.path569_design import capsule,envelopes,project_all
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect

G=base.G;D=Path('/workspace/haic-response569-private');d=base.d;rd=d.rd;sha=d.sha;SCALE=base.SCALE
CAPS=dict(local=dict(ticks=25000,force=110000,geometry=30000,CPU_s=500,wall_s=700),feedback=dict(ticks=90000,force=500000,geometry=120000,CPU_s=1100,wall_s=1500),verification=dict(ticks=1200,force=5000,geometry=1300,CPU_s=35,wall_s=50))
TOTAL=dict(ticks=116200,force=615000,geometry=151300,CPU_s=1700,wall_s=2300)
base.D=D;base.CAPS=CAPS;base.TOTAL=TOTAL

class Study(base.Study):
    def __init__(self):
        assert D.is_dir() and rd(G/'retry/path569_design.json')['passed']
        if (D/'STARTED.json').exists():raise RuntimeError('569_ALREADY_STARTED')
        self.tape,self.static,self.paths,self.ledger=map(rd,base.INPUTS[:4]);self.phases=[];self.cpu=time.process_time();self.wall=time.perf_counter();self.events=[];self.feedback_calls=0;self.accepts=[];self.proposals=0;self.fd_completed=0;self.linears=0;self.new_calibrations=0
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};row=self.tape['rows'][527];visited=set(self.ledger['initial_visited'])
        for r in self.tape['rows'][:528]:
            for ids in r['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**row['tracker']),elapsed=row['episode_after_s'],global_raw=528,progress=row['progress'],launch=row['launch_history_before'].copy(),tracking=row['proposed_history'].copy());self.s900=base.station_point(self.paths['candidate'],900.)
        cache=rd(D/'stored-model-private.json');self.seed_x=np.asarray(cache['seed']['x']);self.seed_cache=cache;self.design=rd(G/'retry/path569_design.json')
        self.start_id=digest(dict(root=row['root_without_roads'],tracker=row['tracker'],progress=row['progress'],tracking=self.start['tracking'],visited=sorted(visited)));assert self.start_id==rd(G/'retry/late567_baseline_result.json')['start_checkpoint_sha256']
        sources=['retry/path569_model.py','retry/path569_design.py','retry/late568_model.py','retry/durable568.py','tests/test_durable568.py',*d.SOURCES];inputs=base.INPUTS[:4]+[D/'stored-model-private.json',G/'retry/path569_design.json',G/'retry/late568_contract.json']
        self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',design='Stored568-only design passed before source work. Frozen finite-segment capsule norm via affine world position; signed-only strips rejected at endpoints. Sufficient for source path<=3 when frozen segment eligible; equivalence only for minimizing segment. Exact original projection always rechecks.',start='Same exact565raw528/launch55/384/tracking64/1728/visited/tracker/clock. No seed replay. Initial40FD+2calibrations reused from568same seed/control/horizon/source; all prior costs separate.',error_rule='No impossible margin clipping. Every tightening is L*t with t>=normalized infinity step and zero-step margin0. L=2*(positive empirical optimism or world-position error+controlULP)/.05. Capsule:distance(predposition,finitesegment)+Lposition*t<=3. Scalar geometry/force/rank envelopes also displacement-dependent; no universal validity claim. Recalibrate two fixed opposite patterns for every fresh center. Exact seed inclusion and all finite coefficient/upper bound checks before each solve.',solver='LP normalized40controls+one infinity-norm epigraph. Exact capsule convex-model check after every LP; add supporting-plane cuts from violating projected point,at most8LP/cutrounds. Only an exact-model-feasible float32 point can open source. Known physical slack upper bounds force1.059/body100/reference84.85/rank1/path3 plus finite localbox attainable caps enforced. Footprint signed-distance scalar errors remain potentially conservative and are reported independently.',bounds='Scales steer.003/pedal.03;radius.05,.025,.0125 only;total displacement<=.15 from seed. At most2source proposals per center;two failed proposals shrink radius by.5 each,no model/threshold changes. Float32 algebraic repairs alpha1,1-2^-12,1-2^-10,1-2^-8 only;no source sweep. No model predicted time gain>=1microsecond ->stop.',caps=dict(linearizations_including_reused=3,new_FD_columns=80,new_calibration_checks=4,source_proposals=6,bounded_backtracks=3,feedback_calls=4,safe_working_accepts=3,LP_cut_rounds_per_solve=8,quantization_repairs=4),admission='Source diagnostic surrogate and strict program separate. Program133..152 must pass every original global raw safety gate;its fresh existing537feedback must finish safely. Surrogate saved-tail violation is diagnostic,never policy adoption. Exact sign/segment/source projection rechecked;unsafe probe never incumbent. Working accepts require continuous hullplane gain>=1microsecond,no later officialcandidate raw;wholepromotion strictly earlier officialcandidate raw. Original551reference/exact ratio>1 counts/tracker/body<100/TimeLimit preserved.',final='Only a new selected safe working/whole trajectory receives one full independent source command-tape replay with exact565prefix528 plus candidate suffix;no accepted candidate ->no existingwhole replay.',budgets=CAPS,aggregate=TOTAL,feedback_case=base.CASE,actual_cap=0,HOLDOUT=0,SEALED=0,new_seed_paid_other_environment=0,research_remaining=22758,reserve=84000,reserve_used=0,source_kernel_cap_unchanged=200000,source_sha256={p:sha(G/p) for p in sources},input_sha256={str(p):sha(p) for p in inputs})
        atomic_write(G/'retry/path569_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/path569_contract.json'),source_ticks=0));self.journal=Journal(D/'raw-journal-private.jsonl');self.localphase=base.Phase(self,'local')
    def cost(self):
        value=super().cost();value.pop('prior567_separate',None);value['prior568_separate']=dict(ticks=11256,CPU_s=267.501622644);value['saved_only_design']=dict(ticks=0,CPU_s=self.design['CPU_s'],wall_s=self.design['wall_s']);return value
    def save_cost(self):atomic_write(G/'retry/path569_cost.json',self.cost(),True)
    def metric(self,rows):
        value=super().metric(rows);value['P']=np.asarray([r['root_without_roads']['center'] for r in rows]);return value
    def raw(self,state,a,index,k,phase,diagnostic=False):
        previous=state['progress'];row,reason=super().raw(state,a,index,k,phase,diagnostic)
        if 'root_without_roads' in row and state['global_raw']>528:
            q=d.project(state['root'].center,self.paths['candidate'],previous);t=q['tangent'];point=state['root'].center;row.update(active_segment=q['i'],signed_lateral=t[0]*(point[1]-q['point'][1])-t[1]*(point[0]-q['point'][0]))
            mode={};offset=state['global_raw']-529
            if hasattr(self,'segIdx') and 0<=offset<134:
                i=int(self.segIdx[offset]);cd,_,u,_=capsule(np.asarray(point),self.segA[offset],self.segB[offset]);s=self.paths['candidate']['arcs'][i]+float(np.clip(u,0,1))*self.paths['candidate']['ds'][i];s+=round((previous-s)/self.paths['candidate']['length'])*self.paths['candidate']['length'];mode=dict(reference_segment=i,segment_changed=q['i']!=i,frozen_segment_eligible=previous-5<=s<=previous+30,frozen_segment_distance=float(cd))
            row.update(mode);self.journal.append('SOURCE_PATH_RECHECK',global_raw=state['global_raw'],label=phase.label,diagnostic=diagnostic,active_segment=q['i'],projection_t=q['t'],exact_path_distance=q['distance'],signed_lateral=row['signed_lateral'],path_pass=q['distance']<=3.,**mode)
        return row,reason
    def frozen_segments(self,center):
        previous=np.asarray([self.start['progress']]+[r['progress'] for r in center['rows'][:-1]]);idx,dist,eligible,*_=project_all(center['P'],previous,self.paths['candidate']);pts=np.asarray(self.paths['candidate']['points']);self.segA=pts[idx];self.segB=np.roll(pts,-1,axis=0)[idx];self.segIdx=idx
        assert np.max(abs(dist-(3-center['g'][1::10])))<1e-8
    def fresh_linear(self,center,tail):
        self.linears+=1;assert self.linears<=3;J=[];R=[];O=[];T=[];P=[];steps=[];unsafe=[]
        for j,v in enumerate(center['x']):
            h=1e-5 if j%2==0 else 1e-4;hi=float(np.float32(.4)) if j%2==0 else 1.;x=center['x'].copy();x[j]=float(np.float32(v+(h if v+h<=hi else -h)));step=x[j]-v
            if step==0:raise RuntimeError('FLOAT32_ZERO_FD')
            ev=self.local(x,f'FD-{self.linears:02d}-{j:02d}',tail);self.fd_completed+=1
            if ev['times']['hull_finish'] is None:raise RuntimeError('FD_FINISH_UNBRACKETED')
            J.append((ev['g']-center['g'])/step);R.append((ev['ratios']-center['ratios'])/step);O.append((ev['order']-center['order'])/step);T.append((ev['times']['hull_finish']-center['times']['hull_finish'])/step);P.append((ev['P']-center['P'])/step);steps.append(step)
            if not ev['physical_safe']:unsafe.append(j)
        linear=dict(J=np.asarray(J).T,R=np.asarray(R).T,O=np.asarray(O).T,T=np.asarray(T),P=np.stack(P,axis=2));atomic_write(D/f'linear-{self.linears}-private.json',dict(linear=linear,steps=steps,unsafe_probe_columns=unsafe));patterns=[]
        for n,sign in enumerate([1.,-1.]):
            x=center['x'].copy()
            for j,v in enumerate(x):
                delta=sign*(1 if j%2==0 else -1)*.05*SCALE[j];lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.)
                if not lo<=v+delta<=hi:delta=-delta
                x[j]=float(np.float32(v+delta))
            patterns.append(self.local(x,f'cal-{self.linears}-{n}',tail));self.new_calibrations+=1
        return linear,envelopes(center,linear,patterns)
    def solve(self,center,linear,env,rho,tag):
        keep=np.asarray(center['labels'])!='path';J=linear['J']*SCALE;R=linear['R']*SCALE;P=linear['P']*SCALE;T=linear['T']*SCALE;lg=np.asarray(env['g']);lp=np.asarray(env['position']);cm={}
        for raw,m in enumerate(env['order']):
            n=4*(raw+1);k=(1728+n)//10-64;rank=np.argsort(-center['ratios'][:n],kind='stable')
            for i in rank[max(k,0):]:cm[int(i)]=max(cm.get(int(i),0),float(m))
        ids=np.array(sorted(cm),int);lr=np.array([max(cm[int(i)],env['ratio'][int(i)]) for i in ids]);A=[np.c_[-J[keep],lg[keep]],np.c_[R[ids],lr]];B=[center['g'][keep],1-center['ratios'][ids]]
        # Finite local-model attainable upper bounds for every scalar target.
        upper=center['g']+rho*np.sum(abs(J),axis=1);universal=np.array([1.059 if x=='force' else 100. if x=='body' else 84.85 if x=='reference' else np.inf for x in center['labels']]);cap=np.minimum(upper,universal)
        A.append(np.c_[np.zeros((sum(keep),40)),lg[keep]]);B.append(cap[keep]);A.append(np.c_[np.zeros((len(lp),40)),lp]);B.append(np.full(len(lp),3.));A.append(np.c_[np.zeros((len(lr),40)),lr]);B.append(np.ones(len(lr)))
        known=np.isfinite(universal);A.append(np.c_[J[known],np.zeros(sum(known))]);B.append(universal[known]-center['g'][known])
        I=np.eye(40);A.extend([np.c_[I,-np.ones(40)],np.c_[-I,-np.ones(40)]]);B.extend([np.zeros(40),np.zeros(40)])
        bounds=[]
        for j,v in enumerate(center['x']):
            lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(v-self.seed_x[j])/SCALE[j];bounds.append((max(-rho,-.15-offset,(lo-v)/SCALE[j]),min(rho,.15-offset,(hi-v)/SCALE[j])))
        bounds.append((0.,rho));v=self.segB-self.segA;unit=v/np.linalg.norm(v,axis=1)[:,None];normal=np.c_[-unit[:,1],unit[:,0]]
        def add_normals(indices,normals):
            for i,n in zip(indices,normals):
                support=max(n@self.segA[i],n@self.segB[i]);A.append(np.r_[n@P[i],lp[i]][None,:]);B.append(np.asarray([3.+support-n@center['P'][i]]))
        for n in [normal,-normal,unit,-unit]:add_normals(range(134),n)
        A0=np.vstack(A);b0=np.concatenate(B);origin_pass=bool(np.all(b0>=-1e-10) and center['physical_safe'] and np.all(capsule(center['P'],self.segA,self.segB)[0]<=3.))
        pre=dict(exact_seed_included=origin_pass,all_targets_zero_at_zero_step=True,minimum_model_origin_slack=float(min(b0)),local_scalar_upper_min=float(min(upper)),local_scalar_upper_max=float(max(upper)),capsule_radius_upper=3.,finite_coefficients=bool(np.all(np.isfinite(A0))),rho=rho)
        atomic_write(D/(tag+'-precheck-private.json'),pre)
        if not origin_pass or not pre['finite_coefficients']:return None,dict(reason='MODEL_SEED_OR_UPPER_BOUND_PRECHECK_FAILED',precheck=pre)
        for cut in range(8):
            aa=np.vstack(A);bb=np.concatenate(B);sol=linprog(np.r_[T,1e-8],A_ub=aa,b_ub=bb,bounds=bounds,method='highs')
            if not sol.success:return None,dict(reason='LP_FAILED',status=int(sol.status),cut_round=cut+1,precheck=pre)
            z=sol.x[:40];t=sol.x[40];pred=center['P']+np.einsum('ijk,k->ij',P,z);dist,res,_,_=capsule(pred,self.segA,self.segB);bad=np.flatnonzero(dist+lp*t>3.+1e-9)
            if len(bad):add_normals(bad,res[bad]/dist[bad,None]);continue
            for repair,alpha in enumerate([1.,1.-2**-12,1.-2**-10,1.-2**-8]):
                x=(center['x']+alpha*SCALE*z).astype(np.float32).astype(float);zz=(x-center['x'])/SCALE;tt=float(max(abs(zz)));pred=center['P']+np.einsum('ijk,k->ij',P,zz);model_path=capsule(pred,self.segA,self.segB)[0]+lp*tt;linear_violation=max(0.,float(max(aa@np.r_[zz,tt]-bb)));path_violation=max(0.,float(max(model_path-3.)))
                bound_violation=max([0.]+[max(lo-v,v-hi) for v,(lo,hi) in zip(np.r_[zz,tt],bounds)])
                if linear_violation<=1e-8 and path_violation<=1e-8 and bound_violation<=1e-8:
                    gain=-float(T@zz);meta=dict(cut_round=cut+1,repair=repair,normalized_step=tt,predicted_gain_ms=1000*gain,linear_model_violation=linear_violation,capsule_model_violation=path_violation,bound_violation=bound_violation,precheck=pre)
                    return (x if gain>=1e-6 else None),dict(meta,reason=None if gain>=1e-6 else 'NO_MICROSECOND_MODEL_DESCENT')
            return None,dict(reason='NO_FLOAT32_MODEL_FEASIBLE_STEP',cut_round=cut+1,precheck=pre)
        return None,dict(reason='CAPSULE_CUT_LIMIT8',precheck=pre)
    def run(self):
        result={};error=None;stop=None;whole=None;selected=None;verification=None;working=None;working_raw=661;nonimproving=0;backtracks=0
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP569')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP569')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s'])
        try:
            tail={i:a for i,a in self.commands.items() if i>=153};seed=self.metric(self.tape['rows'][528:]);seed.update(x=self.seed_x.copy(),label='saved565seed',rows=self.tape['rows'][528:]);center=working=seed;linear={k:np.asarray(v) for k,v in self.seed_cache['linear'].items()};env=self.seed_cache['envelope'];self.linears=1;seen=set()
            for n in range(3):
                if n:linear,env=self.fresh_linear(center,tail)
                self.frozen_segments(center);accepted=False;rho=.05
                atomic_write(D/f'envelope-{n}-private.json',env)
                for attempt in range(2):
                    tag=f'proposal-{n}-{attempt}';x,meta=self.solve(center,linear,env,rho,tag)
                    if x is None:self.events.append(dict(label=tag,source_evaluated=False,model=meta));stop=meta['reason'];break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,tag+'-diagnostic',tail);event=dict(label=tag,source_evaluated=True,model=meta,surrogate_physical_safe=probe['physical_safe'],surrogate_violations=probe['violation_counts'],feedback_called=False,working_accept=False,whole_promotion=False)
                    program=self.strict_program(x,tag+'-strict-program');event['strict_program_safe']=program['safe']
                    if program['safe']:
                        exact=all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) for a,b in zip(program['rows'],probe['rows'][:80]));assert exact
                        fb=self.feedback(program,tag+'-feedback');event.update(feedback_called=True,safe_finish=fb['safe_finish'],feedback_failure=fb['failure'])
                        if fb['safe_finish']:
                            metrics=self.metric(program['rows']+fb['rows']);raw=round((fb['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-metrics['times']['hull_finish'];event.update(official_candidate_raw=raw,confirmation_raw=fb['state']['global_raw'],official_finish_s=fb['state']['tracker'].finish_time_s-1.02,actual_times=metrics['times'],diagnostic_gain_ms=1000*gain)
                            if metrics['physical_safe'] and raw<=working_raw and gain>=1e-6:
                                case=dict(x=x.copy(),program=program,feedback=fb,metrics=metrics);self.accepts.append(case);selected=case;working=metrics;working_raw=raw;event['working_accept']=True;accepted=True;nonimproving=0
                                if raw<661 and (whole is None or raw<round((whole['feedback']['state']['tracker'].finish_time_s-1.02)/.02)):whole=case;event['whole_promotion']=True
                                tail={i:a for i,a in self.commands.items() if i>=153};tail.update({q['index']:np.asarray(q['action'],np.float32) for q in fb['commands']});center=self.local(x,f'refresh-{n}',tail)
                                if not center['physical_safe']:stop='REFRESH_CENTER_NOT_EXACT_FEASIBLE'
                            else:nonimproving+=1
                        else:nonimproving+=1
                    else:event['program_failure']=program['reason'];nonimproving+=1
                    self.events.append(event);atomic_write(D/(tag+'-decision-private.json'),event)
                    if accepted or stop:break
                    if self.feedback_calls>=4:stop='FEEDBACK_LIMIT4';break
                    backtracks+=1;rho*=.5
                    if backtracks>=3:stop='BACKTRACK_LIMIT3';break
                    if nonimproving>=2:stop='TWO_POLICY_NONIMPROVEMENTS';break
                if stop or not accepted:stop=stop or 'TWO_BOUNDED_PROPOSALS_WITHOUT_ACCEPT';break
                if self.feedback_calls>=4:stop='FEEDBACK_LIMIT4';break
                if len(self.accepts)>=3:stop='WORKING_ACCEPT_LIMIT3';break
            stop=stop or 'LINEARIZATION_LIMIT3';selected=whole or selected
            if selected is not None:verification=self.verify(selected)
            result.update(completed=True,stop_reason=stop,seed_times=seed['times'],final_working_times=working['times'],safe_working_accepts=len(self.accepts),official_whole_promotion=whole is not None,official_incumbent_candidate_raw=round((whole['feedback']['state']['tracker'].finish_time_s-1.02)/.02) if whole else 661,official_incumbent_finish_s=whole['feedback']['state']['tracker'].finish_time_s-1.02 if whole else 13.219999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events)
        except BaseException as e:
            error=type(e).__name__+':'+str(e);atomic_write(D/'ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True);result.update(completed=False,error=error,events=self.events,safe_working_accepts=len(self.accepts))
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.save_cost();self.journal.close()
            try:audit=inspect(D/'raw-journal-private.jsonl')
            except BaseException as e:audit=dict(valid=False,error=str(e))
            atomic_write(G/'retry/path569_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/path569_contract.json'),stored_only_design_passed=True,private_raw_uploaded=False));result.update(error=error,cost=self.cost(),linearizations=self.linears,reused_FD_columns=40,new_FD_columns=self.fd_completed,new_calibration_checks=self.new_calibrations,source_proposals=self.proposals,bounded_backtracks=backtracks,actual_feedback_calls=self.feedback_calls,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/path569_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**k):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()

"""Bounded same-tail continuation with active-constraint diagnostics."""
import copy,datetime,json,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.repair571_model as parent
from retry.geometry571 import vertices,layout,active_component,component
from retry.path569_design import capsule
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect

G=parent.G;D=Path('/workspace/haic-response572-private');OLD=Path('/workspace/haic-response571-private');base=parent.base;d=parent.d;rd=d.rd;sha=d.sha;SCALE=parent.SCALE
CAPS=dict(local=dict(ticks=42000,force=175000,geometry=45000,CPU_s=1150,wall_s=1550),evaluation=dict(ticks=2500,force=10500,geometry=2700,CPU_s=75,wall_s=110),verification=dict(ticks=1200,force=5000,geometry=1300,CPU_s=35,wall_s=50))
TOTAL=dict(ticks=45700,force=190500,geometry=49000,CPU_s=1400,wall_s=1850)
base.D=D;base.CAPS=CAPS;base.TOTAL=TOTAL;parent.D=D;parent.CAPS=CAPS;parent.TOTAL=TOTAL;parent.parent.D=D

class Study(parent.Study):
    def __init__(self):
        assert D.is_dir() and (G/'retry/reference572_diagnosis.json').exists()
        if (D/'STARTED.json').exists():raise RuntimeError('572_ALREADY_STARTED')
        self.tape,self.static,self.paths,self.ledger=map(rd,base.INPUTS[:4]);self.cpu=time.process_time();self.wall=time.perf_counter();self.phases=[];self.events=[];self.accepts=[];self.proposals=0;self.linears=0;self.fd_completed=0;self.calibrations=0;self.evaluations=0;self.restorations=0;self.geometry_queries=0
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};r=self.tape['rows'][527];visited=set(self.ledger['initial_visited'])
        for row in self.tape['rows'][:528]:
            for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**r['tracker']),elapsed=r['episode_after_s'],global_raw=528,progress=r['progress'],launch=r['launch_history_before'].copy(),tracking=r['proposed_history'].copy());self.s900=base.station_point(self.paths['candidate'],900.)
        self.incumbent=rd(OLD/'proposal-4-0-diagnostic-private.json');self.seed_x=np.asarray(self.incumbent['x']);roots=[d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads'])) for row in self.incumbent['rows']];self.initialV=np.stack([vertices(root) for root in roots]);self.vertex_layout=layout(roots[0]);self.start_id=digest(dict(root=r['root_without_roads'],tracker=r['tracker'],progress=r['progress'],tracking=self.start['tracking'],visited=sorted(visited)));assert self.start_id==rd(G/'retry/late567_baseline_result.json')['start_checkpoint_sha256']
        self.floor={};self.known_components=set();self.observations=[];self.features=[];self.sensitivity_summaries=[]
        for path in sorted(OLD.glob('*-support-private.json')):
            value=rd(path)
            for k,v in zip(value['keys'],value['error_coefficients']):self.floor[k]=max(self.floor.get(k,0),v)
            for f in value['features']:self.known_components.add((f['raw'],f['kind'],f['polygon'],f['feature']))
        self.diagnosis=rd(G/'retry/reference572_diagnosis.json');atomic_write(D/'reused-geometry-history-private.json',dict(floor=self.floor,components=sorted(self.known_components),same_center_FD=False))
        sources=['retry/reference572_model.py','retry/reference572_diagnose.py','retry/repair571_model.py','retry/geometry571.py','retry/geometry571_design.py','tests/test_geometry571.py','retry/tail570_model.py','retry/path569_model.py','retry/path569_design.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES];inputs=base.INPUTS[:4]+[OLD/'proposal-4-0-diagnostic-private.json',G/'retry/repair571_result.json',G/'retry/reference572_diagnosis.json',D/'reused-geometry-history-private.json']
        self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',start='571finalsafe sourceplan660/13.20. Same565raw528fullstate/history/visited/tracker/clock;launch55/384,tracking64/1728;original565prefix528 unchanged. No same-centerFD at final571point:DO NOTreuse previous-centerFD as exactcurrent. Fresh68FD initial andafteraccepts;reuse exactfinaltrajectory,geometryfeatureIDs andobserved coefficient floors only;no seed replay.',saved_diagnosis='Actualpeakreference raw532,535,539 (hold133..135). Stored previous-center gradients identify causalearlycontrols andflatlocalprofile derivative. Mere near-zero slack is not evidence of a physical optimum. Conditionalreference-onlyLP omitsotherconstraints and is not a sourcecandidate. Keep reference and4.85limit unchanged.',method='Samefull68variable commandtrajectory,134rawdiagnostic,strictwholefinish. Existing finite-segment2Dcapsule,signedpolygon/component supports,displacementL*t,errorobserved recovery,exactprefixcounts and551reference. Recenter andRETAIN all previously learned componentIDs including632/633 acrosscenters,plusraw573..580 base;alwayssource exactgeometry authoritative. No buffer grid or physicaltolerance relaxation.',diagnostics='Record conditional LPphysical-reference/force/footprint duals andsignedsupportduals at UNROUNDED localmodel optimum,plus bound activity,actualreference minima andcontrol sensitivities. These are localfixedbranch/trust/model diagnostics,not nonlinear/global optimality or physics bounds.',caps=dict(linearizations=4,new_FD=272,new_calibration_checks=8,source_proposals=10,strict_full_finish_cases=10,measured_error_recoveries=3,safe_working_accepts=4,attempts_per_center=3,primitive_queries=64,LP_cut_rounds=8,quantization_repairs=4),bounds='Same steer.003/pedal.03 scales. Percenter rho.05;one measured-error reoptimization atsame rho;then.025. Totalnormalizeddisplacement<=.20 from571final. Fourfloat32algebraicrepairalphas,8capsulecutrounds. Frozen coefficient factor2derivedfromobserved errors/actualmovement;zero displacement margins0 andseed/upperbounds checked.',progress='Accept exactsafe wholefinish hullinterpolantgain>=1microsecond andno laterofficialcandidate raw. Officialpromotion ONLY candidate raw<660. Three consecutive accepted gains TOTAL<.10ms AND lasttwoeach<.05ms ->OBSERVED_SMALL_PROGRESS_WINDOW. Two safewhole nonimprovements ortwo failed repairs with<10%violation reduction ->measuredstagnation. Otherwise cap4accept/4linear/10proposals/3recoveries ends boundedrun;not convergence proof. Check full actual gains,predictionerrors and perconstraint margins.',validation='All diagnostic/state/action/history/forceverdict durable before source tick. Everycandidate originalstrictglobalforce/path/footprint/reference/count/bodydomain andofficialtrackerqualifier/confirmation. Samecommanddiagnostic-strictprefix/time exactcheck. OnlyselectedNEWsafeimprovingtape independently replayedfrominitialsource state withoriginalprefix;none->no oldwhole replay. Native actual0;no feedback/native/latency/disturbance guarantee.',budgets=CAPS,aggregate=TOTAL,actual_cap=0,HOLDOUT=0,SEALED=0,new_seed_paid_other_environment=0,research_remaining=22758,reserve=84000,reserve_used=0,source_kernel_cap_unchanged=200000,source_sha256={p:sha(G/p) for p in sources},input_sha256={str(p):sha(p) for p in inputs})
        atomic_write(G/'retry/reference572_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/reference572_contract.json'),source_ticks=0));self.journal=Journal(D/'raw-journal-private.jsonl');self.localphase=base.Phase(self,'local')
    def cost(self):
        value=base.Study.cost(self);value.pop('prior567_separate',None);value['prior571_separate']=dict(ticks=39993,CPU_s=1040.234367377);value['saved_only_diagnosis']=dict(ticks=0,CPU_s=self.diagnosis['CPU_s'],wall_s=self.diagnosis['wall_s']);value['primitive_geometry_queries']=self.geometry_queries;return value
    def save_cost(self):atomic_write(G/'retry/reference572_cost.json',self.cost(),True)
    def linearize(self,center,first=False):
        linear,env=parent.Study.linearize(self,center,first=False);T=linear['T']*SCALE;norm=float(np.linalg.norm(T));descent=-T/norm if norm else np.zeros(68);refs=[]
        for row in sorted(center['rows'],key=lambda r:-r['reference_overspeed'])[:5]:
            offset=row['global_raw_after']-529;grad=linear['J'][offset*10+2]*SCALE;n=min(68,2*(offset//4+1));assert np.all(grad[n:]==0)
            refs.append(dict(raw=row['global_raw_after'],actual_slack=4.85-row['reference_overspeed'],slack_change_on_L2_time_descent=float(grad@descent),dominant_controls=[dict(hold=133+int(j)//2,control='steer' if j%2==0 else 'pedal',slack_slope_per_normalized_unit=float(grad[j])) for j in np.argsort(-abs(grad))[:n if n<6 else 6]],future_control_derivatives_zero=True))
        summary=dict(linearization=self.linears,center_label=center['label'],reference=refs,dominant_time_controls_ms=[dict(hold=133+int(j)//2,control='steer' if j%2==0 else 'pedal',slope_ms_per_normalized_unit=float(T[j]*1000)) for j in np.argsort(-abs(T))[:10]],scope='Fresh exact-center FD,local only;not global/physical optimum bounds');self.sensitivity_summaries.append(summary);atomic_write(D/f'sensitivity-{self.linears}-private.json',summary);return linear,env
    def prepare_features(self,center):
        parent.Study.prepare_features(self,center)
        for raw,kind,poly,feature in sorted(self.known_components):
            if any(f['raw']==raw and f['kind']==kind and f['polygon']==poly and f['feature']==feature for f in self.features):continue
            root=d.load_root(dict(center['rows'][raw]['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();f=component(root,self.static,kind,poly,feature);f['raw']=raw;self.features.append(f)
    def recover(self,center,linear,env,probe,case):
        detail=parent.Study.recover(self,center,linear,env,probe,case)
        if detail.get('added_component'):self.known_components.add((detail['raw']-529,detail['kind'],detail['polygon'],detail['feature']))
        return detail

    def strict_finish(self,x,label):
        self.evaluations+=1;assert self.evaluations<=10;state=copy.deepcopy(self.start);phase=base.Phase(self,'evaluation');rows=[];commands=self.actions(x);failure=None
        with phase.session(label):
            try:
                for offset in range(134):
                    i,k=divmod(528+offset,4);row,reason=self.raw(state,commands[i+1],i+1,k+1,phase);rows.append(row)
                    if reason:failure=reason;break
                    if state['tracker'].finish_time_s is not None:break
                    if 50+state['global_raw']>=1224:failure='SOURCE_TIME_LIMIT';break
                safe=failure is None and state['tracker'].finish_time_s is not None
                return dict(x=x.copy(),safe_finish=safe,failure=failure or (None if safe else 'NO_FINISH_IN_HORIZON'),rows=rows,state=state,label=label)
            finally:atomic_write(D/(label+'-private.json'),dict(x=x,rows=rows,checkpoint=base.checkpoint(state),failure=failure,cost=self.cost()))
    def solve(self,center,linear,env,rho,tag):
        N=len(center['x'])
        keep=np.asarray(center['labels'])!='path';J=linear['J']*SCALE;R=linear['R']*SCALE;P=linear['P']*SCALE;T=linear['T']*SCALE;lg=np.asarray(env['g']);lp=np.asarray(env['position']);cm={}
        for raw,m in enumerate(env['order']):
            n=4*(raw+1);k=(1728+n)//10-64;rank=np.argsort(-center['ratios'][:n],kind='stable')
            for i in rank[max(k,0):]:cm[int(i)]=max(cm.get(int(i),0),float(m))
        ids=np.array(sorted(cm),int);lr=np.array([max(cm[int(i)],env['ratio'][int(i)]) for i in ids]);A=[np.c_[-J[keep],lg[keep]],np.c_[R[ids],lr]];B=[center['g'][keep],1-center['ratios'][ids]]
        support_q,support_J,support_L=self.support_model(center,linear,rho,tag)
        A.append(np.c_[-support_J*SCALE,support_L]);B.append(support_q)
        A.append(np.c_[np.zeros((len(support_L),N)),support_L]);B.append(support_q+rho*np.sum(abs(support_J*SCALE),axis=1))
        # Finite local-model attainable upper bounds for every scalar target.
        upper=center['g']+rho*np.sum(abs(J),axis=1);universal=np.array([1.059 if x=='force' else 100. if x=='body' else 84.85 if x=='reference' else np.inf for x in center['labels']]);cap=np.minimum(upper,universal)
        A.append(np.c_[np.zeros((sum(keep),N)),lg[keep]]);B.append(cap[keep]);A.append(np.c_[np.zeros((len(lp),N)),lp]);B.append(np.full(len(lp),3.));A.append(np.c_[np.zeros((len(lr),N)),lr]);B.append(np.ones(len(lr)))
        known=np.isfinite(universal);A.append(np.c_[J[known],np.zeros(sum(known))]);B.append(universal[known]-center['g'][known])
        I=np.eye(N);A.extend([np.c_[I,-np.ones(N)],np.c_[-I,-np.ones(N)]]);B.extend([np.zeros(N),np.zeros(N)])
        bounds=[]
        for j,v in enumerate(center['x']):
            lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(v-self.seed_x[j])/SCALE[j];bounds.append((max(-rho,-.20-offset,(lo-v)/SCALE[j]),min(rho,.20-offset,(hi-v)/SCALE[j])))
        bounds.append((0.,rho));v=self.segB-self.segA;unit=v/np.linalg.norm(v,axis=1)[:,None];normal=np.c_[-unit[:,1],unit[:,0]]
        def add_normals(indices,normals):
            for i,n in zip(indices,normals):
                support=max(n@self.segA[i],n@self.segB[i]);A.append(np.r_[n@P[i],lp[i]][None,:]);B.append(np.asarray([3.+support-n@center['P'][i]]))
        for n in [normal,-normal,unit,-unit]:add_normals(range(134),n)
        A0=np.vstack(A);b0=np.concatenate(B);origin_pass=bool(np.all(b0>=-1e-10) and center['physical_safe'] and np.all(capsule(center['P'],self.segA,self.segB)[0]<=3.))
        pre=dict(signed_support_constraints=len(support_q),minimum_seed_support_slack=float(min(support_q)),maximum_support_error_coefficient=float(max(support_L)),exact_seed_included=origin_pass,all_targets_zero_at_zero_step=True,minimum_model_origin_slack=float(min(b0)),local_scalar_upper_min=float(min(upper)),local_scalar_upper_max=float(max(upper)),capsule_radius_upper=3.,finite_coefficients=bool(np.all(np.isfinite(A0))),rho=rho)
        atomic_write(D/(tag+'-precheck-private.json'),pre)
        if not origin_pass or not pre['finite_coefficients']:return None,dict(reason='MODEL_SEED_OR_UPPER_BOUND_PRECHECK_FAILED',precheck=pre)
        for cut in range(8):
            aa=np.vstack(A);bb=np.concatenate(B);sol=linprog(np.r_[T,1e-8],A_ub=aa,b_ub=bb,bounds=bounds,method='highs')
            if not sol.success:return None,dict(reason='LP_FAILED',status=int(sol.status),cut_round=cut+1,precheck=pre)
            z=sol.x[:N];t=sol.x[N];pred=center['P']+np.einsum('ijk,k->ij',P,z);dist,res,_,_=capsule(pred,self.segA,self.segB);bad=np.flatnonzero(dist+lp*t>3.+1e-9)
            if len(bad):add_normals(bad,res[bad]/dist[bad,None]);continue
            for repair,alpha in enumerate([1.,1.-2**-12,1.-2**-10,1.-2**-8]):
                x=(center['x']+alpha*SCALE*z).astype(np.float32).astype(float);zz=(x-center['x'])/SCALE;tt=float(max(abs(zz)));pred=center['P']+np.einsum('ijk,k->ij',P,zz);model_path=capsule(pred,self.segA,self.segB)[0]+lp*tt;linear_violation=max(0.,float(max(aa@np.r_[zz,tt]-bb)));path_violation=max(0.,float(max(model_path-3.)))
                bound_violation=max([0.]+[max(lo-v,v-hi) for v,(lo,hi) in zip(np.r_[zz,tt],bounds)])
                if linear_violation<=1e-8 and path_violation<=1e-8 and bound_violation<=1e-8:
                    gain=-float(T@zz);dual=self.dual_snapshot(center,keep,ids,support_q,sol,bounds);meta=dict(local_duals=dual,cut_round=cut+1,repair=repair,normalized_step=tt,predicted_gain_ms=1000*gain,linear_model_violation=linear_violation,capsule_model_violation=path_violation,bound_violation=bound_violation,precheck=pre)
                    return (x if gain>=1e-6 else None),dict(meta,reason=None if gain>=1e-6 else 'NO_MICROSECOND_MODEL_DESCENT')
            return None,dict(reason='NO_FLOAT32_MODEL_FEASIBLE_STEP',cut_round=cut+1,precheck=pre)
        return None,dict(reason='CAPSULE_CUT_LIMIT8',precheck=pre)
    def run(self):
        result={};error=None;stop=None;whole=None;selected=None;verification=None;working=None;working_raw=660;safe_stale=0;repair_stale=0;last_bad=None;seen=set()
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP572')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP572')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s'])
        try:
            seed=self.metric(self.incumbent['rows']);seed.update(x=self.seed_x.copy(),rows=self.incumbent['rows'],label='571final-safe-working');assert seed['physical_safe'] and np.array_equal(seed['V'],self.initialV);center=working=seed
            for n in range(4):
                if time.process_time()-self.cpu>=1200 or time.perf_counter()-self.wall>=1680:stop='OPTIMIZATION_TIME_RESERVE';break
                if n and self.localphase.counter[0]+68*134+4*134>CAPS['local']['ticks']:stop='LOCAL_RESERVE';break
                self.prepare_features(center);self.frozen_segments(center);linear,env=self.linearize(center,first=n==0);accepted=False;rho=.05
                for attempt in range(3):
                    if self.proposals>=10:stop='PROPOSAL_LIMIT10';break
                    label=f'proposal-{n}-{attempt}';x,meta=self.solve(center,linear,env,rho,label)
                    if x is None:self.events.append(dict(label=label,source_evaluated=False,model=meta));stop=meta['reason'];break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,label+'-diagnostic');case=self.strict_finish(x,label+'-strict-finish');event=dict(label=label,source_evaluated=True,model=meta,diagnostic_physical_safe=probe['physical_safe'],diagnostic_violations=probe['violation_counts'],strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],working_accept=False,official_promotion=False);self.events.append(event)
                    if case['safe_finish']:
                        exact=len(case['rows'])<=len(probe['rows']) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(case['rows'],probe['rows']));actual=self.metric(case['rows']);matched=actual['times']['hull_finish']==probe['times']['hull_finish'];assert exact and matched
                        raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-actual['times']['hull_finish'];event.update(strict_diagnostic_prefix_exact=exact,objective_same_command_time_exact=matched,actual_times=actual['times'],diagnostic_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],official_finish_s=case['state']['tracker'].finish_time_s-1.02)
                        if actual['physical_safe'] and gain>=1e-6 and raw<=working_raw:
                            case['metrics']=actual;self.accepts.append(case);selected=case;working=actual;working_raw=raw;accepted=True;safe_stale=0;repair_stale=0;last_bad=None;event['working_accept']=True
                            if raw<660 and (whole is None or raw<round((whole['state']['tracker'].finish_time_s-1.02)/.02) or (raw==round((whole['state']['tracker'].finish_time_s-1.02)/.02) and actual['times']['hull_finish']<whole['metrics']['times']['hull_finish'])):whole=case;event['official_promotion']=True
                            center=probe
                            if not center['physical_safe']:stop='POSTFINISH_DIAGNOSTIC_CENTER_UNSAFE'
                        else:safe_stale+=1
                    else:
                        scales=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in probe['labels']]);bad=max(0.,float(max(-probe['g']/scales)),float(max(-probe['order']/.01)));event['measured_normalized_violation']=bad
                        if last_bad is not None:
                            repair_stale=repair_stale+1 if bad>=.9*last_bad else 0
                        last_bad=bad
                        if attempt<2 and self.restorations<3:event['measured_error_recovery']=self.recover(center,linear,env,probe,case)
                        else:stop='RECOVERY_ATTEMPT_OR_GLOBAL_LIMIT'
                    atomic_write(D/(label+'-decision-private.json'),event)
                    if accepted or stop:break
                    if safe_stale>=2:stop='TWO_SAFE_WHOLE_NONIMPROVEMENTS';break
                    if repair_stale>=2:stop='TWO_REPAIR_STAGNATIONS';break
                    if attempt>=1 or case['safe_finish']:rho*=.5
                if stop or not accepted:stop=stop or 'THREE_BOUNDED_ATTEMPTS_WITHOUT_ACCEPT';break
                recent=[e['diagnostic_gain_ms'] for e in self.events if e.get('working_accept')][-3:]
                if len(recent)==3 and sum(recent)<.10 and all(g<.05 for g in recent[-2:]):stop='OBSERVED_SMALL_PROGRESS_WINDOW';break
                if len(self.accepts)>=4:stop='ACCEPT_LIMIT4';break
            stop=stop or 'LINEARIZATION_LIMIT4'
        except BaseException as e:
            error=type(e).__name__+':'+str(e);atomic_write(D/'ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            try:
                selected=whole or selected
                if selected is not None:verification=self.verify_plan(selected)
            except BaseException as e:
                error=(error+';' if error else '')+'VERIFY:'+type(e).__name__+':'+str(e);atomic_write(D/'VERIFY_ERROR-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
            self.save_cost();self.journal.close()
            try:audit=inspect(D/'raw-journal-private.jsonl')
            except BaseException as e:audit=dict(valid=False,error=str(e))
            atomic_write(G/'retry/reference572_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/reference572_contract.json'),private_raw_uploaded=False,source_hashes_match=all(sha(G/p)==h for p,h in self.contract['source_sha256'].items()),primitive_unit_tests_reused=4))
            promoted=whole is not None and verification is not None and error is None
            result.update(completed=error is None,error=error,stop_reason=stop,scope='Same full68 source openloop plan;native/feedbacktransition/robustness unproven',seed_times=seed['times'] if 'seed' in locals() else None,final_working_times=working['times'] if working is not None else None,safe_working_accepts=len(self.accepts),official_whole_promotion=promoted,official_incumbent_candidate_raw=round((whole['state']['tracker'].finish_time_s-1.02)/.02) if promoted else 660,official_incumbent_finish_s=whole['state']['tracker'].finish_time_s-1.02 if promoted else 13.199999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events,cost=self.cost(),linearizations=self.linears,reused_FD_columns=0,local_sensitivity_summaries=self.sensitivity_summaries,new_FD_columns=self.fd_completed,new_calibrations=self.calibrations,source_proposals=self.proposals,strict_full_finish_cases=self.evaluations,measured_error_recoveries=self.restorations,feedback_calls=0,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/reference572_result.json',result);print(json.dumps(plain(result),indent=2))
    def dual_snapshot(self,center,keep,ids,support_q,sol,bounds):
        mapping=np.flatnonzero(keep);marg=np.asarray(sol.ineqlin.marginals);res=np.asarray(sol.ineqlin.residual);physical=[]
        for j,i in enumerate(mapping):
            label=center['labels'][i]
            physical.append(dict(label=label,raw=529+int(i)//10,seed_physical_slack=float(center['g'][i]),linear_residual=float(res[j]),conditional_rhs_sensitivity_seconds=float(marg[j])))
        reference=sorted([p for p in physical if p['label']=='reference'],key=lambda p:(-abs(p['conditional_rhs_sensitivity_seconds']),p['seed_physical_slack']))[:6]
        top_physical=sorted(physical,key=lambda p:-abs(p['conditional_rhs_sensitivity_seconds']))[:8];start=len(mapping)+len(ids);keys=[f"{f['raw']}:{f['kind']}:{f['polygon']}:{f['feature']}:{v}" for f in self.features for v in self.vertex_layout[f['polygon']]];assert len(keys)==len(support_q)
        support=[dict(feature=key,seed_support_slack=float(support_q[j]),linear_residual=float(res[start+j]),conditional_rhs_sensitivity_seconds_per_meter=float(marg[start+j])) for j,key in enumerate(keys)];support=sorted(support,key=lambda p:-abs(p['conditional_rhs_sensitivity_seconds_per_meter']))[:6]
        lower=np.asarray(sol.lower.marginals);upper=np.asarray(sol.upper.marginals);active=sorted(range(68),key=lambda j:-(abs(lower[j])+abs(upper[j])))[:6];bound=[dict(hold=133+j//2,control='steer' if j%2==0 else 'pedal',lower_sensitivity=float(lower[j]),upper_sensitivity=float(upper[j])) for j in active]
        return dict(reference=reference,dominant_physical=top_physical,dominant_signed_support=support,dominant_control_bounds=bound,scope='Unrounded LP optimum at frozen local Jacobian/rank/support/error envelope/trust radius. RHS derivatives are conditional model values,not whole source response,global optimum or permission to change a threshold.')

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()

"""570 method2: every remaining command is optimized and then executed exactly."""
import copy,datetime,json,signal,time,traceback
from pathlib import Path
import numpy as np
import retry.path569_model as prev
from retry.path569_design import capsule,envelopes
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect
from scipy.optimize import linprog

G=prev.G;D=Path('/workspace/haic-response570-private');base=prev.base;d=prev.d;rd=d.rd;sha=d.sha
SCALE=np.tile([.003,.03],34)
CAPS=dict(local=dict(ticks=45000,force=190000,geometry=50000,CPU_s=1100,wall_s=1400),evaluation=dict(ticks=3000,force=13000,geometry=3500,CPU_s=80,wall_s=120),verification=dict(ticks=1200,force=5000,geometry=1300,CPU_s=35,wall_s=50))
TOTAL=dict(ticks=49200,force=208000,geometry=54800,CPU_s=1300,wall_s=1700)
base.D=D;base.CAPS=CAPS;base.TOTAL=TOTAL;prev.D=D

class Study(prev.Study):
    def __init__(self):
        D.mkdir(mode=0o700,exist_ok=False);self.tape,self.static,self.paths,self.ledger=map(rd,base.INPUTS[:4]);self.cpu=time.process_time();self.wall=time.perf_counter();self.phases=[];self.events=[];self.accepts=[];self.proposals=0;self.linears=0;self.fd_completed=0;self.calibrations=0
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};r=self.tape['rows'][527];visited=set(self.ledger['initial_visited'])
        for row in self.tape['rows'][:528]:
            for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**r['tracker']),elapsed=r['episode_after_s'],global_raw=528,progress=r['progress'],launch=r['launch_history_before'].copy(),tracking=r['proposed_history'].copy());self.s900=base.station_point(self.paths['candidate'],900.)
        self.start_id=digest(dict(root=r['root_without_roads'],tracker=r['tracker'],progress=r['progress'],tracking=self.start['tracking'],visited=sorted(visited)));assert self.start_id==rd(G/'retry/late567_baseline_result.json')['start_checkpoint_sha256']
        self.seed_x=np.array([v for i in range(133,167) for v in [float(self.commands[i][0]),float(self.commands[i][1]-self.commands[i][2])]]);assert len(self.seed_x)==68
        self.cache=rd(Path('/workspace/haic-response569-private/stored-model-private.json'));self.reused=40;self.evaluations=0
        assert np.array_equal(self.seed_x[:40],np.asarray(self.cache['seed']['x']))
        sources=['retry/tail570_model.py','retry/path569_model.py','retry/path569_design.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES]
        inputs=base.INPUTS[:4]+[Path('/workspace/haic-response569-private/stored-model-private.json'),G/'retry/path569_analysis.json']
        self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',chosen_method=2,reason='Remaining134raw source rollout is far cheaper than actualfeedback~5000modelticks. OptimizeALL34remainingholds133..166,68float32steer/signedpedal variables,including last partialhold. Derivative,calibration,objective and strictfinalexecution use the SAME complete command trajectory. Nofeedback method1calls or mixed policy at153.',scope='Proves only exact source-model safety/officialtracker finish of commandtape. No native/pixel/walllatency/disturbance guarantee and no switch/recovery tofeedback certificate. Nativecap0. This is a new source open-loop plan,not a real driving record.',start='Exact565raw528/root/visited/tracker/clock,launch55/384,tracking64/1728. Savedseed baseline reused without integration. Initial first40FD columns reuse568samefullcommandtape,28newtailcolumns;fresh68FD after accepted centers. First568calibrations not reused for expandedcontrolspace;two fixed opposite all68patterns percenter.',horizon='Fixed134raw diagnostic horizon529..662. ALL commands including153..166 variable. Any changed stored tail is integrated and checked at every raw. Strictcandidate stops only at actualunchangedtracker confirmation;must finish withinregistered134raw horizon. Diagnostic postfinish rows remain bodyguarded and never replace strictproof.',model='Preserve569finite-segment affine2Dcapsule,exactconvexmodel recheck/max8supportcutLPs. Same moving L*t empiricalerror budgets forphysical/force/prefix/pathvector,seedzero inclusion andupperbounds checked beforeLP;no coefficient clipping or physicalthresholdrelaxation. Existing551reference,exact ratio>1counts,prefixrank branch and initialhistory unchanged. Empirical two-pattern errors are not universal bounds;strict source decides safety.',bounds='Scales steer.003/pedal.03;percenter radius.05 then.025 only,max2proposals;totalnormalized displacement<=.2fromoriginalseed. Fouralgebraicfloat32repairs1,1-2^-12,1-2^-10,1-2^-8. Max4linearizations,reused40/new232FD,8calibrationpatterns,8proposals,8strictfullcandidatecases,4safeaccepts,4backtracks;two consecutive nonimprovements stop. No arbitrarytiny scalarpolls.',objective='Whole arrival interpolated at tracker hull-origin centerplane. Workingadoption requires exactglobalsafe strictfinish,>=1microsecond continuouswholegain,no laterofficialcandidate raw. Officialwholepromotion ONLY strictlyearlierofficialcandidate raw/time. Record confirmationraw separately. No localstationgain orlinear prediction used foradoption.',verification='Any new safe whole-improving accepted candidate:one independent fullsource initial-state commandtape replay,original565prefix528+allmodifiedremainingcommands,compare everyroot/force/history/tracker andfinalcheckpoint. If no acceptedcandidate,no oldwhole replay. Allrawforceinputs/verdicts/bodypathchecks durable;finallycostFIRST. Domain/IO/integrity/cap errors stop.',budgets=CAPS,aggregate=TOTAL,actual_cap=0,HOLDOUT=0,SEALED=0,new_seed_paid_other_environment=0,research_remaining=22758,reserve=84000,reserve_used=0,source_kernel_cap_unchanged=200000,source_sha256={p:sha(G/p) for p in sources},input_sha256={str(p):sha(p) for p in inputs})
        atomic_write(G/'retry/tail570_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/tail570_contract.json'),source_ticks=0));self.journal=Journal(D/'raw-journal-private.jsonl');self.localphase=base.Phase(self,'local')
    def cost(self):
        value=base.Study.cost(self);value.pop('prior567_separate',None);value['prior569_separate']=dict(ticks=11605,CPU_s=206.30458459);return value
    def save_cost(self):atomic_write(G/'retry/tail570_cost.json',self.cost(),True)
    def actions(self,x):
        assert len(x)==68
        return {133+j:np.asarray([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(34)}
    def local(self,x,label):
        state=copy.deepcopy(self.start);rows=[];tape=self.actions(x)
        with self.localphase.session(label) as phase:
            try:
                for offset in range(134):
                    i,k=divmod(528+offset,4);row,_=self.raw(state,tape[i+1],i+1,k+1,phase,True);rows.append(row)
                result=self.metric(rows);result.update(x=x.copy(),rows=rows,state=state,label=label);return result
            finally:
                payload=dict(x=x,label=label,rows=rows if not label.startswith('FD') else None,checkpoint=base.checkpoint(state),cost=self.cost())
                if 'result' in locals():payload.update({k:result[k] for k in ['g','labels','ratios','order','times','physical_safe','violation_counts']})
                atomic_write(D/(label+'-private.json'),payload)
    def linearize(self,center,first=False):
        self.linears+=1;assert self.linears<=4;cols={k:[] for k in ['J','R','O','T','P']};steps=[];unsafe=[]
        for j,v in enumerate(center['x']):
            if first and j<40:
                for k in cols:cols[k].append(np.asarray(self.cache['linear'][k])[...,j])
                steps.append(None);continue
            h=1e-5 if j%2==0 else 1e-4;hi=float(np.float32(.4)) if j%2==0 else 1.;x=center['x'].copy();x[j]=float(np.float32(v+(h if v+h<=hi else -h)));step=x[j]-v
            if step==0:raise RuntimeError('FLOAT32_ZERO_FD')
            ev=self.local(x,f'FD-{self.linears}-{j:02d}');self.fd_completed+=1
            if ev['times']['hull_finish'] is None:raise RuntimeError('FD_FINISH_UNBRACKETED')
            for k,field in [('J','g'),('R','ratios'),('O','order'),('P','P')]:cols[k].append((ev[field]-center[field])/step)
            cols['T'].append((ev['times']['hull_finish']-center['times']['hull_finish'])/step);steps.append(step)
            if not ev['physical_safe']:unsafe.append(j)
        linear={k:np.stack(v,axis=-1) for k,v in cols.items()};atomic_write(D/f'linear-{self.linears}-private.json',dict(linear=linear,steps=steps,reused_columns=40 if first else 0,unsafe_probe_columns=unsafe));patterns=[]
        for n,sign in enumerate([1.,-1.]):
            x=center['x'].copy()
            for j,v in enumerate(x):
                delta=sign*(1 if j%2==0 else -1)*.05*SCALE[j];lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.)
                if not lo<=v+delta<=hi:delta=-delta
                x[j]=float(np.float32(v+delta))
            patterns.append(self.local(x,f'cal-{self.linears}-{n}'));self.calibrations+=1
        env=envelopes(center,linear,patterns);atomic_write(D/f'envelope-{self.linears}-private.json',env);return linear,env
    def strict_finish(self,x,label):
        self.evaluations+=1;assert self.evaluations<=8;state=copy.deepcopy(self.start);phase=base.Phase(self,'evaluation');rows=[];commands=self.actions(x);failure=None
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
    def verify_plan(self,case):
        state=d.Study.initial(self);phase=base.Phase(self,'verification');commands={i:a for i,a in self.commands.items() if i<=132};commands.update(self.actions(case['x']));expected=self.tape['rows'][:528]+case['rows'];actual=[]
        with phase.session('final-independent-full-tape'):
            for index in sorted(commands):
                for k in range(1,5):
                    row,reason=self.raw(state,commands[index],index,k,phase);actual.append(row)
                    if reason:raise RuntimeError('REPLAY_SAFETY:'+reason)
                    if state['tracker'].finish_time_s is not None:break
                if state['tracker'].finish_time_s is not None:break
        same=len(expected)==len(actual) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(actual,expected));cp=d.canonical(base.checkpoint(state))==d.canonical(base.checkpoint(case['state']));atomic_write(D/'final-independent-tape-private.json',dict(rows=actual,commands=[dict(index=i,action=a.tolist()) for i,a in sorted(commands.items())],checkpoint=base.checkpoint(state),exact=same,checkpoint_exact=cp))
        if not same or not cp:raise RuntimeError('REPLAY_INTEGRITY')
        return dict(raw=len(actual),fullstate_force_history_tracker_exact=same,checkpoint_exact=cp,official_candidate_raw=round((state['tracker'].finish_time_s-1.02)/.02),confirmation_raw=state['global_raw'])
    def feedback(self,*a,**k):raise RuntimeError('METHOD1_DISABLED570')

    def solve(self,center,linear,env,rho,tag):
        N=len(center['x'])
        keep=np.asarray(center['labels'])!='path';J=linear['J']*SCALE;R=linear['R']*SCALE;P=linear['P']*SCALE;T=linear['T']*SCALE;lg=np.asarray(env['g']);lp=np.asarray(env['position']);cm={}
        for raw,m in enumerate(env['order']):
            n=4*(raw+1);k=(1728+n)//10-64;rank=np.argsort(-center['ratios'][:n],kind='stable')
            for i in rank[max(k,0):]:cm[int(i)]=max(cm.get(int(i),0),float(m))
        ids=np.array(sorted(cm),int);lr=np.array([max(cm[int(i)],env['ratio'][int(i)]) for i in ids]);A=[np.c_[-J[keep],lg[keep]],np.c_[R[ids],lr]];B=[center['g'][keep],1-center['ratios'][ids]]
        # Finite local-model attainable upper bounds for every scalar target.
        upper=center['g']+rho*np.sum(abs(J),axis=1);universal=np.array([1.059 if x=='force' else 100. if x=='body' else 84.85 if x=='reference' else np.inf for x in center['labels']]);cap=np.minimum(upper,universal)
        A.append(np.c_[np.zeros((sum(keep),N)),lg[keep]]);B.append(cap[keep]);A.append(np.c_[np.zeros((len(lp),N)),lp]);B.append(np.full(len(lp),3.));A.append(np.c_[np.zeros((len(lr),N)),lr]);B.append(np.ones(len(lr)))
        known=np.isfinite(universal);A.append(np.c_[J[known],np.zeros(sum(known))]);B.append(universal[known]-center['g'][known])
        I=np.eye(N);A.extend([np.c_[I,-np.ones(N)],np.c_[-I,-np.ones(N)]]);B.extend([np.zeros(N),np.zeros(N)])
        bounds=[]
        for j,v in enumerate(center['x']):
            lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(v-self.seed_x[j])/SCALE[j];bounds.append((max(-rho,-.2-offset,(lo-v)/SCALE[j]),min(rho,.2-offset,(hi-v)/SCALE[j])))
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
            z=sol.x[:N];t=sol.x[N];pred=center['P']+np.einsum('ijk,k->ij',P,z);dist,res,_,_=capsule(pred,self.segA,self.segB);bad=np.flatnonzero(dist+lp*t>3.+1e-9)
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
        result={};error=None;stop=None;working=None;whole=None;selected=None;verification=None;working_raw=661;backtracks=0;nonimproving=0;seen=set()
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP570')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP570')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s'])
        try:
            seed=self.metric(self.tape['rows'][528:]);seed.update(x=self.seed_x.copy(),rows=self.tape['rows'][528:],label='exact565fulltail');center=working=seed
            assert seed['physical_safe'] and all(v is not None for v in seed['times'].values())
            for n in range(4):
                if time.process_time()-self.cpu>=1150 or time.perf_counter()-self.wall>=1450:stop='OPTIMIZATION_TIME_RESERVE';break
                needed=(28 if n==0 else 68)*134+4*134
                if self.localphase.counter[0]+needed>CAPS['local']['ticks']:stop='LOCAL_RESERVE';break
                linear,env=self.linearize(center,first=n==0);self.frozen_segments(center);accepted=False;rho=.05
                for attempt in range(2):
                    label=f'proposal-{n}-{attempt}';x,meta=self.solve(center,linear,env,rho,label)
                    if x is None:self.events.append(dict(label=label,source_evaluated=False,model=meta));stop=meta['reason'];break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,label+'-diagnostic');case=self.strict_finish(x,label+'-strict-finish');event=dict(label=label,source_evaluated=True,model=meta,diagnostic_physical_safe=probe['physical_safe'],diagnostic_violations=probe['violation_counts'],strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],working_accept=False,official_promotion=False)
                    if case['safe_finish']:
                        exact=len(case['rows'])<=len(probe['rows']) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(case['rows'],probe['rows']))
                        actual=self.metric(case['rows']);objective_match=actual['times']['hull_finish']==probe['times']['hull_finish'];assert exact and objective_match
                        raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-actual['times']['hull_finish'];event.update(strict_and_diagnostic_prefix_exact=exact,objective_same_command_time_exact=objective_match,actual_times=actual['times'],diagnostic_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],official_finish_s=case['state']['tracker'].finish_time_s-1.02)
                        if actual['physical_safe'] and gain>=1e-6 and raw<=working_raw:
                            case['metrics']=actual;self.accepts.append(case);selected=case;working=actual;working_raw=raw;accepted=True;nonimproving=0;event['working_accept']=True
                            if raw<661 and (whole is None or raw<round((whole['state']['tracker'].finish_time_s-1.02)/.02) or (raw==round((whole['state']['tracker'].finish_time_s-1.02)/.02) and actual['times']['hull_finish']<whole['metrics']['times']['hull_finish'])):whole=case;event['official_promotion']=True
                            center=probe
                            if not center['physical_safe']:stop='POSTFINISH_DIAGNOSTIC_CENTER_UNSAFE'
                        else:nonimproving+=1
                    else:nonimproving+=1
                    self.events.append(event);atomic_write(D/(label+'-decision-private.json'),event)
                    if accepted or stop:break
                    backtracks+=1;rho*=.5
                    if nonimproving>=2:stop='TWO_FULL_OBJECTIVE_NONIMPROVEMENTS';break
                    if backtracks>=4:stop='BACKTRACK_LIMIT4';break
                if stop or not accepted:stop=stop or 'TWO_BOUNDED_PROPOSALS_WITHOUT_ACCEPT';break
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
            atomic_write(G/'retry/tail570_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/tail570_contract.json'),private_raw_uploaded=False,source_hashes_match=all(sha(G/p)==h for p,h in self.contract['source_sha256'].items())))
            promoted=whole is not None and verification is not None and error is None
            result.update(completed=error is None,error=error,stop_reason=stop,method=2,seed_times=seed['times'] if 'seed' in locals() else None,final_working_times=working['times'] if working is not None else None,safe_working_accepts=len(self.accepts),official_whole_promotion=promoted,official_incumbent_candidate_raw=round((whole['state']['tracker'].finish_time_s-1.02)/.02) if promoted else 661,official_incumbent_finish_s=whole['state']['tracker'].finish_time_s-1.02 if promoted else 13.219999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events,cost=self.cost(),linearizations=self.linears,reused_FD_columns=40,new_FD_columns=self.fd_completed,new_calibrations=self.calibrations,source_proposals=self.proposals,strict_full_finish_cases=self.evaluations,backtracks=backtracks,feedback_calls=0,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/tail570_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()

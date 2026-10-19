"""Observed-error signed primitive restoration with the same full68 command goal."""
import copy,datetime,json,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.tail570_model as parent
from retry.geometry571 import vertices,layout,active_component,component
from retry.geometry571_design import constraints
from retry.path569_design import capsule,envelopes
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect

G=parent.G;D=Path('/workspace/haic-response571-private');OLD=Path('/workspace/haic-response570-private');base=parent.base;d=parent.d;rd=d.rd;sha=d.sha;SCALE=parent.SCALE
CAPS=dict(local=dict(ticks=55000,force=230000,geometry=60000,CPU_s=1450,wall_s=1900),evaluation=dict(ticks=4000,force=17000,geometry=4500,CPU_s=100,wall_s=150),verification=dict(ticks=1200,force=5000,geometry=1300,CPU_s=35,wall_s=50))
TOTAL=dict(ticks=60200,force=252000,geometry=65800,CPU_s=1650,wall_s=2200)
base.D=D;base.CAPS=CAPS;base.TOTAL=TOTAL;parent.D=D;parent.CAPS=CAPS;parent.TOTAL=TOTAL

class Study(parent.Study):
    def __init__(self):
        assert D.is_dir() and rd(G/'retry/geometry571_design.json')['passed']
        if (D/'STARTED.json').exists():raise RuntimeError('571_ALREADY_STARTED')
        self.tape,self.static,self.paths,self.ledger=map(rd,base.INPUTS[:4]);self.cpu=time.process_time();self.wall=time.perf_counter();self.phases=[];self.events=[];self.accepts=[];self.proposals=0;self.linears=0;self.fd_completed=0;self.calibrations=0;self.evaluations=0;self.restorations=0;self.geometry_queries=0
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};r=self.tape['rows'][527];visited=set(self.ledger['initial_visited'])
        for row in self.tape['rows'][:528]:
            for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
        self.start=dict(root=d.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads'])),visited=visited,tracker=d.FinishLineTracker(**r['tracker']),elapsed=r['episode_after_s'],global_raw=528,progress=r['progress'],launch=r['launch_history_before'].copy(),tracking=r['proposed_history'].copy());self.s900=base.station_point(self.paths['candidate'],900.)
        self.incumbent=rd(OLD/'proposal-2-0-diagnostic-private.json');self.seed_x=np.asarray(self.incumbent['x']);self.start_id=digest(dict(root=r['root_without_roads'],tracker=r['tracker'],progress=r['progress'],tracking=self.start['tracking'],visited=sorted(visited)));assert self.start_id==rd(G/'retry/late567_baseline_result.json')['start_checkpoint_sha256']
        design=rd(D/'primitive-design-private.json');cache=np.load(D/'vertex-sensitivity-private.npz');self.initialV=cache['V'];self.initialJV=cache['JV'];self.initial_observations=[dict(x=x.copy(),V=v.copy()) for x,v in zip(cache['observation_controls'],cache['observation_vertices'])];self.vertex_layout=design['vertex_layout'];self.floor=dict(zip(design['keys'],design['coefficients']));self.design=rd(G/'retry/geometry571_design.json');self.initial_linear={k:np.asarray(v) for k,v in rd(OLD/'linear-4-private.json')['linear'].items()};self.initial_linear['V']=self.initialJV;self.initial_env=rd(OLD/'envelope-4-private.json');self.observations=[];self.features=[]
        sources=['retry/repair571_model.py','retry/geometry571.py','retry/geometry571_design.py','tests/test_geometry571.py','retry/tail570_model.py','retry/path569_model.py','retry/path569_design.py','retry/late568_model.py','retry/durable568.py',*d.SOURCES]
        inputs=base.INPUTS[:4]+[OLD/'proposal-2-0-diagnostic-private.json',OLD/'linear-4-private.json',OLD/'envelope-4-private.json',D/'vertex-sensitivity-private.npz',D/'primitive-design-private.json']
        self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',start='Preserve570third safe full68workingpoint,x fromproposal2-0. Same565raw528physicalroot/visited/tracker/clock,launch55/384/tracking64/1728. Originalofficialcandidate661/13.22unchanged;original565prefix528unchanged. Reuse saved570linear4all68FD and fullvertexFDcache;no seed replay.',geometry='Stored rejects both road segment250/polygon6 at577,exact positive margins. Add signed support for EVERY vertex of locally active polygon for raws573..580(failinghold145andpredecessor144). Roadsegment/circle supports frozen at each safe center. Separates only that component;not allcomponents/coverage. Originalexactwholevehiclevalidator byte-identical and authoritative.',error='Perfeature L*t,zero atzero displacement. L=2*(maxpositive signedvertex optimism/ACTUAL normalized displacement over currentcalibration+observedrejects + propagatedfloat32ULP/.05 + fourbinary64eps/.05). Initial uses savedcal2+savedreject2;historical perfeature measured coefficient floor retained,recomputed with new center normals. No universal bound,buffer grid,rounding violation,constantmargin clipping or tolerance relaxation. Four primitive/error unit tests passed before source.',method='Same68variables entiretail133..166,134rawdiagnostic;strictallcommands to unchangedofficialfinish. Capsulepath andallscalarphysical/rank L*t constraints retained;add signedvertex supportrows and finite localattainable upperbound checks beforeLP. Exactseed inclusion required. Initialall68FD reused;fresh68FD+twooppositefixed .05calpatterns after eachsafeaccept.',recovery='On unsafe source proposal,add its FULLdiagnostic vertex observation to currentcenter error set;recompute signed supportL by fixed maxrule andupdate scalar/ratio/prefix/position errorcoefficients upward by twice measuredoptimism/displacement+ULP. For positive footprint failure identify exactcomponent andadd samecomponent support recentered atSAFEincumbent ifnew. Never adopt failedstate. One model-informed repair atsame .05radius,then .025;atmost3attempts/center,4recoveriesglobal. Nonpositive coverage/intersection diagnostic terminates as unsupported,not silently modeled.',bounds='Percenter scales steer.003/pedal.03,rho.05 then same .05 aftermeasuredrepair,then.025. Totalnormalizeddisplacement<=.25 from570thirdworkingpoint. Fixed4float32algebraicrepairs and8capsulecutLPs. All body<100/domain/costalwaysenforced. Ordinary diagnostic safetyviolations recorded,strict policy never relaxed.',caps=dict(linearizations=5,reused_FD=68,new_FD=272,new_calibration_checks=8,source_proposals=12,strict_full_finish_cases=12,measured_error_recoveries=4,safe_working_accepts=5,attempts_per_center=3,LP_cut_rounds=8,quantization_repairs=4),stopping='Two safe wholetime nonimprovements;two successive repairs with<10%measurednormalizedviolation reduction;5linearizations/5accepts/12proposals/4recoveries/3attempts percenter;no>=1usmodeldescent;duplicate/quantizedzero;domain/IO/integrity/cap. OptimizationCPU>=1450 orwall>=1900 stops with finalverificationreserved. These are boundedrun/stagnation criteria,not convergence/infeasibility proofs.',admission='Every candidate unchangedexactglobal551reference,force<=1.059,footprint>=.5,path<=3,referenceoverspeed<=4.85,exactprefixcounts,trackerqualification/forward/width/confirmation. Wholehullinterpolantgain>=1us+no latercandidate raw permitsworkingaccept. Officialwholepromotion ONLY strictlyearlierofficialcandidate raw/time. Confirmationraw notscore. Diagnostic/strictsamefullcommandstate+timecheck. Anynewselectedsafeimprovingplan independentreset-source fulltape replay;none->no existingwhole replay.',scope='Source openloop only;Native,feedbacktransition/recovery,pixel/latency/disturbance robustness unproven. Actualcap0,method1disabled.',budgets=CAPS,aggregate=TOTAL,actual_cap=0,HOLDOUT=0,SEALED=0,new_seed_paid_other_environment=0,research_remaining=22758,reserve=84000,reserve_used=0,source_kernel_cap_unchanged=200000,source_sha256={p:sha(G/p) for p in sources},input_sha256={str(p):sha(p) for p in inputs})
        atomic_write(G/'retry/repair571_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/repair571_contract.json'),source_ticks=0));self.journal=Journal(D/'raw-journal-private.jsonl');self.localphase=base.Phase(self,'local')
    def cost(self):
        value=base.Study.cost(self);value.pop('prior567_separate',None);value['prior570_separate']=dict(ticks=33988,CPU_s=867.390746793);value['saved_only_design']=dict(ticks=0,CPU_s=self.design['CPU_s'],wall_s=self.design['wall_s']);value['primitive_geometry_queries']=self.geometry_queries;return value
    def geometry_query(self):
        self.geometry_queries+=1
        if self.geometry_queries>64:raise RuntimeError('PRIMITIVE_QUERY_CAP64')
    def save_cost(self):atomic_write(G/'retry/repair571_cost.json',self.cost(),True)
    def metric(self,rows):
        value=super().metric(rows);value['V']=np.stack([vertices(d.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads']))) for r in rows]);return value
    def prepare_features(self,center):
        self.features=[]
        for raw in range(573,581):
            i=raw-529;root=d.load_root(dict(center['rows'][i]['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();feature=active_component(root,self.static);assert abs(feature['gap']-center['rows'][i]['margin'])<1e-8;feature['raw']=i;self.features.append(feature)
    def linearize(self,center,first=False):
        self.linears+=1;assert self.linears<=5
        if first:
            self.observations=list(self.initial_observations);return dict(self.initial_linear),copy.deepcopy(self.initial_env)
        cols={k:[] for k in ['J','R','O','T','P','V']};steps=[];unsafe=[]
        for j,v in enumerate(center['x']):
            h=1e-5 if j%2==0 else 1e-4;hi=float(np.float32(.4)) if j%2==0 else 1.;x=center['x'].copy();x[j]=float(np.float32(v+(h if v+h<=hi else -h)));step=x[j]-v
            if step==0:raise RuntimeError('FLOAT32_ZERO_FD')
            ev=self.local(x,f'FD-{self.linears}-{j:02d}');self.fd_completed+=1
            if ev['times']['hull_finish'] is None:raise RuntimeError('FD_FINISH_UNBRACKETED')
            for key,field in [('J','g'),('R','ratios'),('O','order'),('P','P'),('V','V')]:cols[key].append((ev[field]-center[field])/step)
            cols['T'].append((ev['times']['hull_finish']-center['times']['hull_finish'])/step);steps.append(step)
            if not ev['physical_safe']:unsafe.append(j)
        linear={k:np.stack(v,axis=-1) for k,v in cols.items()};atomic_write(D/f'linear-{self.linears}-private.json',dict(linear=linear,steps=steps,unsafe_probe_columns=unsafe));patterns=[]
        for n,sign in enumerate([1.,-1.]):
            x=center['x'].copy()
            for j,v in enumerate(x):
                delta=sign*(1 if j%2==0 else -1)*.05*SCALE[j];lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.)
                if not lo<=v+delta<=hi:delta=-delta
                x[j]=float(np.float32(v+delta))
            patterns.append(self.local(x,f'cal-{self.linears}-{n}'));self.calibrations+=1
        self.observations=[dict(x=p['x'],V=p['V']) for p in patterns];env=envelopes(center,linear,patterns);atomic_write(D/f'envelope-{self.linears}-private.json',env);return linear,env
    def support_model(self,center,linear,rho,tag):
        q,J,L,keys=constraints(center['V'],linear['V'],center['x'],self.features,self.vertex_layout,self.observations,self.floor)
        for k,v in zip(keys,L):self.floor[k]=max(self.floor.get(k,0),float(v))
        atomic_write(D/(tag+'-support-private.json'),dict(features=self.features,keys=keys,seed_slacks=q,Jacobian=J,error_coefficients=L,local_model_attainable_upper=q+rho*np.sum(abs(J*SCALE),axis=1),observations=len(self.observations)))
        return q,J,L
    def recover(self,center,linear,env,probe,case):
        self.restorations+=1;assert self.restorations<=4;dx=probe['x']-center['x'];r=float(max(abs(dx/SCALE)));self.observations.append(dict(x=probe['x'],V=probe['V']));ulp=np.abs(np.spacing(center['x'].astype(np.float32))).astype(float);floor=4*np.finfo(float).eps/.05
        for key,field,sign in [('g','g',1),('order','order',1),('ratio','ratios',-1)]:
            derivative=linear['J' if key=='g' else 'O' if key=='order' else 'R'];optimism=np.maximum(0,sign*(center[field]+derivative@dx-probe[field]));new=2*(optimism/r+abs(derivative)@ulp/.05+floor);env[key]=np.maximum(np.asarray(env[key]),new)
        p_error=np.linalg.norm(center['P']+np.einsum('ijk,k->ij',linear['P'],dx)-probe['P'],axis=1);env['position']=np.maximum(np.asarray(env['position']),2*(p_error/r+np.linalg.norm(np.einsum('ijk,k->ij',abs(linear['P']),ulp),axis=1)/.05+floor))
        detail=dict(recovery=self.restorations,normalized_displacement=r,source_failure=case['failure'],added_component=False)
        if case['failure']=='FOOTPRINT':
            row=case['rows'][-1];i=row['global_raw_after']-529
            if row['margin']<=0:raise RuntimeError('UNSUPPORTED_NONPOSITIVE_COVERAGE_COMPONENT')
            failedroot=d.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();f=active_component(failedroot,self.static)
            if abs(f['gap']-row['margin'])>1e-8:raise RuntimeError('UNSUPPORTED_SIGNED_COMPONENT_MISMATCH')
            centerroot=d.load_root(dict(center['rows'][i]['root_without_roads'],roads=self.static['root']['roads']));self.geometry_query();new=component(centerroot,self.static,f['kind'],f['polygon'],f['feature']);new['raw']=i
            if not any(all(old[k]==new[k] for k in ['raw','kind','polygon','feature']) for old in self.features):self.features.append(new);detail['added_component']=True
            detail.update(raw=row['global_raw_after'],kind=f['kind'],polygon=f['polygon'],feature=f['feature'],exact_gap=row['margin'])
        atomic_write(D/f'recovery-{self.restorations}-private.json',dict(detail=detail,updated_error_envelope=env));return detail

    def strict_finish(self,x,label):
        self.evaluations+=1;assert self.evaluations<=12;state=copy.deepcopy(self.start);phase=base.Phase(self,'evaluation');rows=[];commands=self.actions(x);failure=None
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
            lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(v-self.seed_x[j])/SCALE[j];bounds.append((max(-rho,-.25-offset,(lo-v)/SCALE[j]),min(rho,.25-offset,(hi-v)/SCALE[j])))
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
                    gain=-float(T@zz);meta=dict(cut_round=cut+1,repair=repair,normalized_step=tt,predicted_gain_ms=1000*gain,linear_model_violation=linear_violation,capsule_model_violation=path_violation,bound_violation=bound_violation,precheck=pre)
                    return (x if gain>=1e-6 else None),dict(meta,reason=None if gain>=1e-6 else 'NO_MICROSECOND_MODEL_DESCENT')
            return None,dict(reason='NO_FLOAT32_MODEL_FEASIBLE_STEP',cut_round=cut+1,precheck=pre)
        return None,dict(reason='CAPSULE_CUT_LIMIT8',precheck=pre)
    def run(self):
        result={};error=None;stop=None;whole=None;selected=None;verification=None;working=None;working_raw=661;safe_stale=0;repair_stale=0;last_bad=None;seen=set()
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('CPU_CAP571')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('WALL_CAP571')));signal.setitimer(signal.ITIMER_PROF,TOTAL['CPU_s']);signal.setitimer(signal.ITIMER_REAL,TOTAL['wall_s'])
        try:
            seed=self.metric(self.incumbent['rows']);seed.update(x=self.seed_x.copy(),rows=self.incumbent['rows'],label='570third-safe-working');assert seed['physical_safe'] and np.array_equal(seed['V'],self.initialV);center=working=seed
            for n in range(5):
                if time.process_time()-self.cpu>=1450 or time.perf_counter()-self.wall>=1900:stop='OPTIMIZATION_TIME_RESERVE';break
                if n and self.localphase.counter[0]+68*134+4*134>CAPS['local']['ticks']:stop='LOCAL_RESERVE';break
                self.prepare_features(center);self.frozen_segments(center);linear,env=self.linearize(center,first=n==0);accepted=False;rho=.05
                for attempt in range(3):
                    if self.proposals>=12:stop='PROPOSAL_LIMIT12';break
                    label=f'proposal-{n}-{attempt}';x,meta=self.solve(center,linear,env,rho,label)
                    if x is None:self.events.append(dict(label=label,source_evaluated=False,model=meta));stop=meta['reason'];break
                    if x.tobytes() in seen or np.array_equal(x,center['x']):stop='DUPLICATE_OR_ZERO';break
                    seen.add(x.tobytes());self.proposals+=1;probe=self.local(x,label+'-diagnostic');case=self.strict_finish(x,label+'-strict-finish');event=dict(label=label,source_evaluated=True,model=meta,diagnostic_physical_safe=probe['physical_safe'],diagnostic_violations=probe['violation_counts'],strict_safe_finish=case['safe_finish'],strict_failure=case['failure'],working_accept=False,official_promotion=False);self.events.append(event)
                    if case['safe_finish']:
                        exact=len(case['rows'])<=len(probe['rows']) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) and a['proposed_history']==b['proposed_history'] and d.canonical(a['tracker'])==d.canonical(b['tracker']) for a,b in zip(case['rows'],probe['rows']));actual=self.metric(case['rows']);matched=actual['times']['hull_finish']==probe['times']['hull_finish'];assert exact and matched
                        raw=round((case['state']['tracker'].finish_time_s-1.02)/.02);gain=working['times']['hull_finish']-actual['times']['hull_finish'];event.update(strict_diagnostic_prefix_exact=exact,objective_same_command_time_exact=matched,actual_times=actual['times'],diagnostic_gain_ms=1000*gain,official_candidate_raw=raw,confirmation_raw=case['state']['global_raw'],official_finish_s=case['state']['tracker'].finish_time_s-1.02)
                        if actual['physical_safe'] and gain>=1e-6 and raw<=working_raw:
                            case['metrics']=actual;self.accepts.append(case);selected=case;working=actual;working_raw=raw;accepted=True;safe_stale=0;repair_stale=0;last_bad=None;event['working_accept']=True
                            if raw<661 and (whole is None or raw<round((whole['state']['tracker'].finish_time_s-1.02)/.02) or (raw==round((whole['state']['tracker'].finish_time_s-1.02)/.02) and actual['times']['hull_finish']<whole['metrics']['times']['hull_finish'])):whole=case;event['official_promotion']=True
                            center=probe
                            if not center['physical_safe']:stop='POSTFINISH_DIAGNOSTIC_CENTER_UNSAFE'
                        else:safe_stale+=1
                    else:
                        scales=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in probe['labels']]);bad=max(0.,float(max(-probe['g']/scales)),float(max(-probe['order']/.01)));event['measured_normalized_violation']=bad
                        if last_bad is not None:
                            repair_stale=repair_stale+1 if bad>=.9*last_bad else 0
                        last_bad=bad
                        if attempt<2 and self.restorations<4:event['measured_error_recovery']=self.recover(center,linear,env,probe,case)
                        else:stop='RECOVERY_ATTEMPT_OR_GLOBAL_LIMIT'
                    atomic_write(D/(label+'-decision-private.json'),event)
                    if accepted or stop:break
                    if safe_stale>=2:stop='TWO_SAFE_WHOLE_NONIMPROVEMENTS';break
                    if repair_stale>=2:stop='TWO_REPAIR_STAGNATIONS';break
                    if attempt>=1 or case['safe_finish']:rho*=.5
                if stop or not accepted:stop=stop or 'THREE_BOUNDED_ATTEMPTS_WITHOUT_ACCEPT';break
                if len(self.accepts)>=5:stop='ACCEPT_LIMIT5';break
            stop=stop or 'LINEARIZATION_LIMIT5'
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
            atomic_write(G/'retry/repair571_audit.json',dict(journal=audit,contract_sha256=sha(G/'retry/repair571_contract.json'),private_raw_uploaded=False,source_hashes_match=all(sha(G/p)==h for p,h in self.contract['source_sha256'].items()),primitive_unit_tests_passed=4))
            promoted=whole is not None and verification is not None and error is None
            result.update(completed=error is None,error=error,stop_reason=stop,scope='Same full68 source openloop plan;native/feedbacktransition/robustness unproven',seed_times=seed['times'] if 'seed' in locals() else None,final_working_times=working['times'] if working is not None else None,safe_working_accepts=len(self.accepts),official_whole_promotion=promoted,official_incumbent_candidate_raw=round((whole['state']['tracker'].finish_time_s-1.02)/.02) if promoted else 661,official_incumbent_finish_s=whole['state']['tracker'].finish_time_s-1.02 if promoted else 13.219999999999807,independent_verification=verification,existing_whole_replay_repeated=False,events=self.events,cost=self.cost(),linearizations=self.linears,reused_FD_columns=68,new_FD_columns=self.fd_completed,new_calibrations=self.calibrations,source_proposals=self.proposals,strict_full_finish_cases=self.evaluations,measured_error_recoveries=self.restorations,feedback_calls=0,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,journal_valid=audit['valid']);atomic_write(G/'retry/repair571_result.json',result);print(json.dumps(plain(result),indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    Study().run()

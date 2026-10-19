"""One frozen geometry/profile and phase-correct, fully metered s400 pilot."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import copy,datetime,hashlib,importlib.util,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry import retime590_math as m
import retry.beam579_model as b
from retry.beam579_math import immutable,clone,isolated
from retry.durable568 import Journal,digest,evaluate_force,inspect
from retry.clip561_core import atomic_write
import retry.structure537_control as policy

d=b.d;G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response590-private');C=G/'retry/retime590_contract.json'
INPUTS=dict(geometry=Path('/workspace/haic-response589-private/selected-geometry-private.json'),paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),proposal=G/'retry/corridor589_next_contract.json',result589=G/'retry/corridor589_result.json')
EXPECTED='1949cafe137cf06d16c25e354ed306bac393c40c838cc124d838b49a6e88f9b3'
CAPS=dict(actual_raw_attempts=1152,attempted_raw=60000,completed_model_ticks=60000,external_force=260000,internal_force=240000,geometry_checks=65000,profile_bound_evaluations=100000)
class BudgetStop(RuntimeError):pass
class ProfileGate(RuntimeError):pass
class SourceDomain(RuntimeError):pass

class Phase(b.Phase):
    def __init__(self,s,name):
        super().__init__(s,name);self.cost.update(forecast_calls=0,forecast_ticks=0,geometry_checks=0);self.lineage=None
    def seed(self,state):self.lineage=m.Lineage(state['root'].planar.linear,state['tracking']);self.base_raw=state['global_raw']
    def evaluate(self,*a,**k):
        if self.s.mode!='forecast':self.s.guard(actual=1);self.s.count('actual_raw_attempts',1)
        return super().evaluate(*a,**k)
    def force(self,root,action):
        history=self.lineage.history(root.planar.linear)
        return self.evaluate(root,action,history,dict(mode='forecast',base_global_raw=self.base_raw,forecast_raw=(history[1]-self.lineage.history(self.lineage.seed)[1])//4),1.059,.1,True)['forces']
    def tick(self,root,gas,brake,index,counter):
        p=self.pending
        if counter is not self.counter or p is None or p['root_id']!=digest(d.short(root)) or [gas,brake]!=p['action'][1:]:raise RuntimeError('EXACT_PENDING_FORCE_TICK')
        self.s.journal.append('BEFORE_TICK',force_event=p['event'],context=p['context'],**p['identity']);after=d.source_tick(root,gas,brake,index,counter);self.s.count('completed_model_ticks',1);body=b.base.body(after);self.s.journal.append('AFTER_TICK',force_event=p['event'],root=d.short(after),body=body,body_domain_pass=math.isfinite(body) and body<100,context=p['context']);self.pending=None;self.cost['body_checks']+=1;self.cost['max_body']=max(self.cost['max_body'],body)
        if not math.isfinite(body):raise RuntimeError('NONFINITE_MODEL_BODY')
        if body>=100:raise SourceDomain('BODY_GE100_IN_'+self.s.mode)
        if self.lineage is not None:self.lineage.successor(after.planar.linear,p['history'])
        return after
    def geometry(self,root,*unused):
        if self.s.mode=='forecast' and self.lineage is not None and root.planar.linear is self.lineage.seed:
            self.s.reserve(48+416,49+417,45,70);self.s.count('forecast_groups',1)
        self.s.guard(geometry=1);self.s.count('geometry_checks',1);event=self.s.journal.append('BEFORE_GEOMETRY',mode=self.s.mode,state_id=digest(d.short(root)));value=d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles']);self.s.journal.append('GEOMETRY_VERDICT',input_event=event,margin=value,mode=self.s.mode);return value

class Study:
    raw=b.base.Study.raw
    def __init__(self):
        self.counts=Counter();self.modes={};self.mode='preparation';self.stage='preparation';self.prior=10.;self.replay_remaining=416;self.result={};self.journal=None;self.current=None;self.deadline=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc);D.mkdir(mode=0o700,exist_ok=False);self.register();self.journal=Journal(D/'raw-journal-private.jsonl');self.orig_ext=b.wheel.wheel_response;self.orig_int=b.planar.wheel_response
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior,wall_s=time.perf_counter()-START_WALL+self.prior)
    def count(self,k,n):
        if k in CAPS and self.counts[k]+n>CAPS[k]:raise BudgetStop(k)
        self.counts[k]+=int(n);self.modes.setdefault(self.mode,Counter())[k]+=int(n)
    def guard(self,attempts=0,external=0,internal=0,geometry=0,actual=0):
        tail=self.replay_remaining if self.mode in ['forecast','candidate'] else 0
        for k,n in [('attempted_raw',attempts+tail),('completed_model_ticks',tail),('external_force',external+4*tail),('internal_force',internal+4*tail),('geometry_checks',geometry+tail),('actual_raw_attempts',actual+tail)]:
            if self.counts[k]+n>CAPS[k]:raise BudgetStop('RESERVED_'+k)
        if self.counts['external_force']+self.counts['internal_force']+external+internal+8*tail>500000:raise BudgetStop('TOTAL_FORCE')
        e=self.elapsed();ctail=45 if self.stage=='candidate' else 0;wtail=70 if self.stage=='candidate' else 0
        if e['CPU_s']+ctail>=898 or e['wall_s']+wtail>=1098:raise BudgetStop('TIME')
        if datetime.datetime.now(datetime.timezone.utc)>=self.deadline:raise BudgetStop('DEADLINE')
    def reserve(self,raw,geo,cpu,wall):
        self.guard()
        for k,n in [('attempted_raw',raw),('completed_model_ticks',raw),('external_force',4*raw),('internal_force',4*raw),('geometry_checks',geo)]:
            if self.counts[k]+n>CAPS[k]:raise BudgetStop('GROUP_RESERVE_'+k)
        if self.counts['external_force']+self.counts['internal_force']+8*raw>500000:raise BudgetStop('GROUP_TOTAL_FORCE')
        e=self.elapsed()
        if e['CPU_s']+cpu>=898 or e['wall_s']+wall>=1098:raise BudgetStop('GROUP_TIME')
    def cost(self):return dict(total=dict(self.counts,**self.elapsed()),modes={k:dict(v) for k,v in self.modes.items()})
    def wheel(self,kind,fn,*a,**k):self.guard(external=int(kind=='external_force'),internal=int(kind=='internal_force'));self.count(kind,1);return fn(*a,**k)
    def register(self):
        if (self.deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()<1130:raise BudgetStop('DEADLINE_START_RESERVE')
        files={str(Path(v.__file__).resolve().relative_to(G)):d.sha(Path(v.__file__).resolve()) for v in tuple(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).is_file() and Path(v.__file__).resolve().is_relative_to(G) and '.venv' not in Path(v.__file__).parts};files.update({f:d.sha(G/f) for f in ['retry/retime590_math.py','retry/retime590_model.py','tests/test_retime590.py','retry/corridor589_next_contract.json']})
        c=dict(study=590,status='FROZEN_BEFORE_TESTS_ASSOCIATION_PROFILE_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),deadline_utc=self.deadline.isoformat(),geometry_sha256=EXPECTED,input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=files,dependency_sha256=b.manifest(),caps=dict(CAPS,total_force=500000,CPU_s=900,wall_s=1100),prior_preparation_CPU_wall_charge_s=self.prior,spec=dict(profile='Exactlyone589geometry;verifyhash/nodenumber/oldstationlabels/oldprimaryandbackuppointsidentity/originaltracknormalassociation before profile. 549formula bodymass/axles distinctfromeffectiveMASS,cap90, .999*400nominal perwheel,onlynewgeometriccurvature;backwarddescendingthenforwardascending,40bisection,2npasscap. Boundpack chargedforcapvertex/acceleration/finalsegmentvalidation/backupminnodevalue,plus5syntheticunitminvalues.Nooldobservedcurvature.',association='Oldprimary/backuppoints mustbeexactlyequal,withsame283originaltracknodeorder;oldprimary minusoriginaltrackcenters mustbeorthogonaltooriginalcenteredtangentwithin1e-8m numericalidentity. Newoldstationlabelsequaloriginalprimaryarcs[:-1],newpointcountsame,589selectedhash/result/outsideguardsverified. Anyfail=>ASSOCIATION_GATE_FAILED_SOURCE0,noanothermapping.',backup='Same589newgeometry/ds/arcs;periodicQ_i=min(newQ_i,6400,oldbackupQ_i);launchQ_iinclclosing=min(newlaunchQ_i,6400,oldbackuplaunchQ_i). Nodeindexassociation,notabsoluteoldarcinterpolation. Freezeallarraysbeforeanysource;node-minnotdynamiccertificate.',prefix='Positiveoriginal577initialtos400crossingwholehold<=416raw;allfullrowsandcheckpoint exact. Raw96checkpointindependentclone,mutablevisited/history/trackerisolated. First96originalcontract;newplanonlyfrom97includingreplay. Reprojectnewprogressbefore90,onlyprogressmetadataallowedchange<=1e-10;physicalroot/history/tracker/clock/visitedunchanged.',candidate='Unchanged537choosecode withnewprimary/backupinputs fromactualraw96copy,holds25..104<=320actualraw. Force/tick/marginmeteringonlymonkeypatch;alltrialsandfreshFINAL counted. Eachforecastgetsactualhistorylineageindependently;forecastnevercommitsactualhistory. No-safe-action=>scientificpolicyfailure. Strictactualfailurestops.',safety='Originalphysicalactions/geometry/finitehull+wheels,sourcebody<100allforecasts,footprint>=.50,path<=3,referenceoverspeed<=4.85tracking,newprofileobjectonlyfrom97. Force1.059tracking,launch2.5/clip.15by24;trackingprefixclip.10;originalphysical1.25/uncertainty.19/buffer.001/clock/visited/tracker unchanged. Old551distance/refexcess diagnostic,notnewglobalveto.',planes='Fixedworldold551s200/300/400leftsegmentpoint+tangentbeforeprofile/source. Separateoldproject±10/corridor3 eligibility;firstforwardCOMcrosslocked,wholecrossingholdsafe. Continuouschordtimeandintegerbrackets+speed/yaw/force/clip/margin. No100/500msgate.',replay='Onlyfullstrictsafes400andcandidatecontinuousgain>32ULP=>oneinitialexactfrozencommandreplay<=416raw,raw1..96old/raw97+new. Nochooserreplay;compareallfullrows/CP/forces/history/tracker/visited/clockandcrossings. No whole/native/incumbentpromotion.',instrumentation='Hashchainedfsyncedcompletepreforceinputs/verdictsBEFOREanytick;exactactualwheel_responsecounts separateexternal/internal,attempted includespreforcefailures,completed incrementsafterreturn. Currentrootandposttickgeometryeachcounted.Allforecast/FINAL/rejectedworkincluded. Beforeeachchoose reserve1536forecast+4actual+416replayraw,geo1568+4+417;beforeeachcert reserve48+416raw/49+417geo andCPU45/wall70(includesaudit15/25andreplay).',exceptions='Budget/deadline=>BUDGET_CENSORED;finitebody>=100anyforecast/actual=>SOURCE_DOMAIN_STOP,firststopnotanotheraction;nonfinite/domainexpression/integrity/IO/rowidentity=>TECHNICAL_FAILURE. Profileassociation/gatefailurebeforephysics=>SOURCE0_PROFILE_GATE_FAILURE. Normalforecastforce/clip/geometry/reference rejectsremainunchanged537trials;actualstrictfail=>DYNAMIC_SAFETY_FAILURE;no-safe-action=>DYNAMIC_POLICY_FAILURE.',scope='Oneprofileandonepilotonly.No solver/newshape/offset/cap/referencefit/native/world/HOLDOUT/SEALED/learning/paidresources.'),incumbents=dict(actual_s=13.66,source_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0))
        atomic_write(C,c);atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C),source_ticks=0));self.contract=c
    def pins(self):
        for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
        for f,h in self.contract['implementation_sha256'].items():assert d.sha(G/f)==h,('CODE',f)
        for f,h in self.contract['dependency_sha256'].items():assert d.sha(G/f if not Path(f).is_absolute() else Path(f))==h,('DEPENDENCY',f)
    def tests(self):
        spec=importlib.util.spec_from_file_location('test_retime590',G/'tests/test_retime590.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);r=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(r);self.result['pure_tests']=dict(tests=r.testsRun,passed=r.wasSuccessful(),errors=len(r.errors),failures=len(r.failures));atomic_write(D/'pure-test-details-private.json',dict(errors=r.errors,failures=r.failures))
        self.count('synthetic_backup_minimum_evaluations',5);self.count('profile_bound_evaluations',5)
        if not r.wasSuccessful():raise RuntimeError('PURE_TESTS_FAILED')
    def profile(self):
        if d.sha(INPUTS['geometry'])!=EXPECTED:raise ProfileGate('GEOMETRY_HASH')
        self.static=d.rd(INPUTS['static']);self.old=d.rd(INPUTS['paths']);self.geom=d.rd(INPUTS['geometry']);path=self.geom['path'];op=self.old['candidate'];ob=self.old['backup'];n=len(path['points']);center=np.array([(q[2],q[3]) for q in self.static['track']]);t=np.roll(center,-1,axis=0)-np.roll(center,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];orthogonal=float(np.max(np.abs(np.sum((np.asarray(op['points'])-center)*t,axis=1))))
        checks=dict(geometry_hash=d.sha(INPUTS['geometry'])==EXPECTED,original_same_points=op['points']==ob['points'],node_counts_equal=n==len(center)==len(op['points'])==len(ob['points']),oldstation_labels_exact=self.geom['oldstation']==op['arcs'][:-1],old_roadnormal_association=orthogonal<=1e-8,result589_hash=d.rd(INPUTS['result589'])['selected']['private_geometry_sha256']==EXPECTED,not_seed=self.geom['seed_returned'] is False)
        self.result['association']=dict(checks=checks,maximum_original_tangent_offset_m=orthogonal,nodes=n)
        if not all(checks.values()):raise ProfileGate('ROAD_NODE_ASSOCIATION')
        self.mode='profile';self.count('profile_generations',1)
        try:primary,meta=m.retime(path,self.static,self.count,self.guard)
        except ValueError as exc:raise ProfileGate('PROFILE_GATE:'+str(exc)) from exc
        backup=m.backup_profile(path,primary,ob,self.count);self.new=dict(candidate=primary,backup=backup);self.planes=m.planes(op);atomic_write(D/'fixed-planes-private.json',self.planes);self.result['profile']=meta;atomic_write(D/'frozen-paths-private.json',self.new);self.source_pin=dict(profile_sha256=d.sha(D/'frozen-paths-private.json'),original_contract_sha256=d.sha(C),planes_sha256=d.sha(D/'fixed-planes-private.json'),geometry_sha256=EXPECTED,implementation_sha256=self.contract['implementation_sha256'],dependency_sha256=self.contract['dependency_sha256'],input_sha256=self.contract['input_sha256']);atomic_write(G/'retry/retime590_source_contract.json',self.source_pin);self.journal.append('PROFILE_FROZEN_BEFORE_SOURCE',profile_sha256=self.source_pin['profile_sha256'],source_contract_sha256=d.sha(G/'retry/retime590_source_contract.json'));self.result['profile_sha256']=self.source_pin['profile_sha256']
        self.tape=d.rd(INPUTS['tape']);self.commands={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands']};self.ledger=d.rd(INPUTS['ledger']);self.index=d.bounds(self.static['roads']);self.edge=d.boundary_index(self.static['boundary'])
    def initial(self):return d.Study.initial(self)
    def checkpoint(self,state):return d.Study.checkpoint(self,state)
    def expected_checkpoint(self,raw):
        r=self.tape['rows'][raw-1];visited=set(self.ledger['initial_visited'])
        for row in self.tape['rows'][:raw]:
            for ids in row['root_without_roads']['current_contacts']:visited.update(ids)
        return dict(root_without_roads=r['root_without_roads'],visited=sorted(visited),tracker=r['tracker'],elapsed=r['episode_after_s'],global_raw=raw,progress=r['progress'],launch=r['proposed_history'] if raw<=96 else self.tape['rows'][95]['proposed_history'],tracking=[0,0] if raw<=96 else r['proposed_history'])
    def positive(self):
        self.stage=self.mode='positive';self.paths=self.old;state=self.initial();rows=[];phase=Phase(self,'positive');g=m.Gates(self.planes);phase.geometry(state['root'])
        try:
            for i in range(1,105):
                hold=[]
                for k in range(1,5):
                    self.current=dict(stage='positive',hold=i,raw=k);self.guard();row,why=self.raw(state,self.commands[i],i,k,phase);rows.append(row);hold.append(row)
                    if why or d.canonical(row)!=self.tape['rows'][row['global_raw_before']]:raise RuntimeError('POSITIVE_FULL_ROW_IDENTITY_OR_SAFETY')
                    g.add(row)
                    if state['global_raw']==96:
                        self.start=clone(state);immutable(self.start['root']);isolated(self.start,[state])
                        if d.canonical(self.checkpoint(self.start))!=d.canonical(self.expected_checkpoint(96)):raise RuntimeError('POSITIVE_RAW96_FULL_CHECKPOINT')
                        atomic_write(D/'raw96-checkpoint-private.json',self.checkpoint(self.start))
                g.finish_hold(hold)
                if '400' in g.hits:break
        finally:atomic_write(D/'positive-observed-private.json',dict(rows=rows,checkpoint=self.checkpoint(state),crossings=g.hits,cost=self.cost()))
        if not g.passed('400'):raise RuntimeError('POSITIVE_S400_MISSING')
        if d.canonical(self.checkpoint(state))!=d.canonical(self.expected_checkpoint(state['global_raw'])):raise RuntimeError('POSITIVE_END_FULL_CHECKPOINT')
        self.positive_rows=rows;self.baseline=g;self.result['positive']=dict(raw=len(rows),all_full_rows_exact=True,raw96_complete_checkpoint_exact=True,end_complete_checkpoint_exact=True,checkpoint_reference='Reconstructedfromfrozen577fullrows+ledgerinitialvisited,includingfullvisitedsetandbothhistories.',crossings=g.hits,raw96_checkpoint_sha256=digest(self.checkpoint(self.start)));atomic_write(D/'positive-private.json',dict(rows=rows,checkpoint=self.checkpoint(state),crossings=g.hits))
    def activate(self,state):
        oldcp=self.checkpoint(state);q=d.project(state['root'].center,self.new['candidate'],state['progress']);delta=q['s']-state['progress']
        if state['global_raw']!=96 or abs(delta)>1e-10 or state['progress']>=90:raise RuntimeError('RAW96_MAPPING')
        state['progress']=q['s'];newcp=self.checkpoint(state);a=dict(oldcp);c=dict(newcp);a.pop('progress');c.pop('progress')
        if d.canonical(a)!=d.canonical(c):raise RuntimeError('RAW96_PHYSICAL_HISTORY_MOVED')
        self.paths=self.new;return dict(old_progress=oldcp['progress'],new_progress=q['s'],difference_m=delta,no_physical_history_change=True)
    def decorate_old(self,row,oldprogress):
        if 'root_without_roads' not in row:return oldprogress
        root=row['root_without_roads'];q=d.project(root['center'],self.old['candidate'],oldprogress);over=math.hypot(*root['planar']['linear']['velocity'])-d.reference(q['s'],self.old['candidate'])[0];row.update(old_progress=q['s'],old_path_error=q['distance'],old_reference_overspeed=over);return q['s']
    def summary(self,rows,state,g,reason):
        post=[r for r in rows if 'margin' in r];last=post[-1] if post else None
        return dict(safe_to_s400=reason is None and g.passed('400'),failure=reason,actual_attempt_rows=len(rows),completed_rows=len(post),global_raw=state['global_raw'],elapsed_s=state['elapsed'],new_progress=state['progress'],old_progress=last.get('old_progress',last['progress']) if last else self.start['progress'],COM_speed_m_s=math.hypot(*state['root'].planar.linear.velocity),yaw_rad_s=state['root'].planar.yaw,maximum_abs_joint_rad=max(abs(v) for v in state['root'].planar.joints),tracking_history=state['tracking'],launch_history=state['launch'],crossings=g.hits,minimum_margin_m=min((r['margin'] for r in post),default=None),maximum_new_path_error=max((r['path_error'] for r in post),default=None),maximum_new_reference_excess=max((r['reference_overspeed'] for r in post),default=None),maximum_old_path_error=max((r.get('old_path_error',r['path_error']) for r in post),default=None),maximum_old_reference_excess=max((r.get('old_reference_overspeed',r['reference_overspeed']) for r in post),default=None),maximum_force_ratio=max((f['ratio'] for r in rows for f in r['forces']),default=None),first_failure_raw=(rows[-1]['global_raw_before']+1 if rows and reason else None))
    def candidate(self):
        self.stage=self.mode='candidate';self.paths=self.old;state=clone(self.start);isolated(state,[self.start]);oldprogress=state['progress'];parent_id=digest(self.checkpoint(self.start));mapping=self.activate(state);phase=Phase(self,'candidate');phase.geometry(state['root']);rows=[];commands=[];details=[];g=m.Gates(self.planes);reason=None;ot,of,om=policy.tick,policy.force_rows,policy.margin
        try:
            for i in range(25,105):
                self.reserve(1536+4+416,1568+4+417,45,70);phase.seed(state);geometry=policy.geometry_context(self.static,65000);self.mode='forecast';policy.tick=phase.tick;policy.force_rows=phase.force;policy.margin=phase.geometry;self.count('chooser_calls',1)
                try:action,detail=policy.choose(state['root'],self.new['candidate'],self.new['backup'],state['progress'],phase.counter,phase.cost,60000,history=tuple(state['tracking']),geometry=geometry)
                finally:policy.tick,policy.force_rows,policy.margin=ot,of,om;self.mode='candidate'
                details.append(dict(hold=i,detail=detail));atomic_write(D/f'chooser-{i:03d}-private.json',details[-1])
                if action is None:reason='NO_SAFE_ACTION';break
                if not detail.get('final_recertified') or not any(q.get('mode')=='FINAL' and q.get('ok') for q in detail['reports']):raise RuntimeError('MISSING_FRESH_FINAL')
                commands.append(dict(index=i,action=action.tolist()));hold=[]
                for k in range(1,5):
                    self.current=dict(stage='candidate',hold=i,raw=k);row,why=self.raw(state,action,i,k,phase);oldprogress=self.decorate_old(row,oldprogress);rows.append(row);hold.append(row);g.add(row)
                    if why:reason=why;break
                g.finish_hold(hold);atomic_write(D/'candidate-progress-private.json',dict(rows=rows,commands=commands,checkpoint=self.checkpoint(state),cost=self.cost()),True)
                if reason or '400' in g.hits:break
            if reason is None and not g.passed('400'):reason='NO_ELIGIBLE_S400_BY320'
        except BaseException as exc:
            reason=type(exc).__name__+':'+str(exc);raise
        finally:
            policy.tick,policy.force_rows,policy.margin=ot,of,om
            self.result['candidate']=self.summary(rows,state,g,reason);self.result['candidate']['mapping']=mapping
            atomic_write(D/'candidate-private.json',dict(rows=rows,commands=commands,checkpoint=self.checkpoint(state),crossings=g.hits,reason=reason,cost=self.cost()))
        if digest(self.checkpoint(self.start))!=parent_id:raise RuntimeError('START_CHECKPOINT_MUTATED')
        out=self.summary(rows,state,g,reason);out['mapping']=mapping;self.result['candidate']=out;return rows,commands,state,g,out
    def replay(self,rows,commands,expected_state,hits):
        self.stage=self.mode='replay';self.paths=self.old;state=self.initial();phase=Phase(self,'replay');phase.geometry(state['root']);g=m.Gates(self.planes);allrows=[];oldprogress=state['progress'];tape={**{i:a for i,a in self.commands.items() if i<=24},**{r['index']:np.asarray(r['action'],np.float32) for r in commands}};expected=self.positive_rows[:96]+rows
        for i in range(1,25+len(commands)):
            if i==25:oldprogress=state['progress'];self.activate(state)
            hold=[]
            for k in range(1,5):
                row,why=self.raw(state,tape[i],i,k,phase);self.replay_remaining-=1
                if i>=25:oldprogress=self.decorate_old(row,oldprogress)
                allrows.append(row);hold.append(row);g.add(row)
                if why or d.canonical(row)!=d.canonical(expected[len(allrows)-1]):raise RuntimeError('EXACT_REPLAY_FULL_ROW')
            g.finish_hold(hold)
        if len(allrows)!=len(expected) or d.canonical(self.checkpoint(state))!=d.canonical(self.checkpoint(expected_state)) or g.hits!=hits:raise RuntimeError('EXACT_REPLAY_CHECKPOINT_OR_GATES')
        atomic_write(D/'independent-replay-private.json',dict(rows=allrows,checkpoint=self.checkpoint(state),crossings=g.hits));return dict(raw=len(allrows),all_full_rows_checkpoint_exact=True,crossings=g.hits)
    def run(self):
        status='TECHNICAL_FAILURE';error=None
        def timeout(*_):raise BudgetStop('SIGNAL_TIME')
        signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout);e=self.elapsed();signal.setitimer(signal.ITIMER_PROF,max(.01,898-e['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,1098-e['wall_s']))
        b.wheel.wheel_response=lambda *a,**k:self.wheel('external_force',self.orig_ext,*a,**k);b.planar.wheel_response=lambda *a,**k:self.wheel('internal_force',self.orig_int,*a,**k)
        try:
            self.guard();self.pins();self.tests();self.profile();self.pins();self.positive();rows,commands,state,g,out=self.candidate();baseline=self.baseline.hits['400'];candidate=g.hits.get('400');gain=baseline['time_s']-candidate['time_s'] if out['safe_to_s400'] else None;self.result['s400_continuous_gain_s']=gain
            if out['safe_to_s400'] and gain>32*max(math.ulp(baseline['time_s']),math.ulp(candidate['time_s'])):
                self.result['replay']=self.replay(rows,commands,state,g.hits);status='SAFE_EARLIER_S400_EXACT_REPLAY'
            else:status='DYNAMIC_POLICY_FAILURE' if out['failure']=='NO_SAFE_ACTION' else 'DYNAMIC_PLANE_GATE_FAILURE' if out['failure']=='NO_ELIGIBLE_S400_BY320' else 'DYNAMIC_SAFETY_FAILURE' if out['failure'] else 'SAFE_S400_NOT_IMPROVED'
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'SOURCE0_PROFILE_GATE_FAILURE' if isinstance(exc,ProfileGate) else 'SOURCE_DOMAIN_STOP' if isinstance(exc,SourceDomain) else 'TECHNICAL_FAILURE';atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),current=self.current,cost=self.cost()))
        finally:
            b.wheel.wheel_response=self.orig_ext;b.planar.wheel_response=self.orig_int;self.mode=self.stage='audit';atomic_write(D/'final-cost-before-audit-private.json',self.cost());self.journal.close()
            try:audit=inspect(D/'raw-journal-private.jsonl');self.pins();self.guard()
            except BaseException as exc:audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
            self.result.update(status=status,error=error,cost=self.cost(),journal=audit,replay=self.result.get('replay'),actual_incumbent_s=13.66,source_incumbent_s=13.20,incumbent_changed=False,research_remaining=22758,reserve=84000,reserve_used=0,native_actions=0,new_world=0,HOLDOUT=0,SEALED=0,new_FD=0,new_solver=0,learning=0,paid_compute=0);atomic_write(G/'retry/retime590_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
        return self.result
if __name__=='__main__':Study().run()

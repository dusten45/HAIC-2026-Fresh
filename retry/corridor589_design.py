"""One registered geometry-only solver; feasible seed and final body screening."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import copy,datetime,hashlib,importlib.util,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from retry import corridor589_math as m
from retry.smoother588_math import intersections
from retry.smoother588_design import static_pose
from retry.plan513_model import load_root,polygons
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response589-private');C=G/'retry/corridor589_contract.json'
INPUTS=dict(paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),problem533=G/'retry/joint533_problem.py',result533=G/'retry/joint533_result.md',failure588=G/'retry/smoother588_result.json')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    with p.open('x') as f:json.dump(value,f,indent=2,allow_nan=False)
    p.chmod(0o600 if p.is_relative_to(D) else 0o644)
class BudgetStop(RuntimeError):pass
class SeedMismatch(RuntimeError):pass

class Study:
    def __init__(self):
        self.cost=Counter();self.iterations=[];self.validations=[];self.result={};self.cache={};self.prior=10.;self.stage='preparation';self.deadline=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc);D.mkdir(mode=0o700,exist_ok=False);self.register();self.log=(D/'geometry-journal-private.jsonl').open('x');self.log_path=D/'geometry-journal-private.jsonl';self.log_path.chmod(0o600)
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior,wall_s=time.perf_counter()-START_WALL+self.prior)
    def guard(self):
        e=self.elapsed()
        if e['CPU_s']+(0 if self.stage=='audit' else 60)>=600 or e['wall_s']+(0 if self.stage=='audit' else 80)>=800:raise BudgetStop('TIME_RESERVING_AUDIT')
        if datetime.datetime.now(datetime.timezone.utc)>=self.deadline:raise BudgetStop('DEADLINE')
    def count(self,k,n=1):
        self.guard()
        if k=='geometry_checks' and self.cost[k]+n>15000:raise BudgetStop('GEOMETRY_PACK_CAP')
        if k in ['objective_evaluations','constraint_evaluations'] and self.cost['objective_evaluations']+self.cost['constraint_evaluations']+n>10000:raise BudgetStop('PURE_EVALUATION_CAP')
        self.cost[k]+=int(n)
    def register(self):
        if (self.deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()<830:raise BudgetStop('INSUFFICIENT_DEADLINE')
        files=['retry/corridor589_math.py','retry/corridor589_design.py','tests/test_corridor589.py','retry/smoother588_math.py','retry/smoother588_design.py','retry/plan513_model.py','retry/corner515_model.py','retry/brake506_geometry.py','retry/brake508_corridor.py','retry/brake510_common.py','retry/envelope500.py','core/vendor/car_dynamics.py']
        files=sorted(set(files)|{str(Path(module.__file__).resolve().relative_to(G)) for module in tuple(sys.modules.values()) if getattr(module,'__file__',None) and Path(module.__file__).is_file() and Path(module.__file__).resolve().is_relative_to(G) and '.venv' not in Path(module.__file__).parts})
        contract=dict(study=589,status='FROZEN_BEFORE_TESTS_SEED_SCREEN_AND_SOLVER',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),deadline_utc=self.deadline.isoformat(),input_sha256={k:sha(p) for k,p in INPUTS.items()},implementation_sha256={p:sha(G/p) for p in files},spec=dict(seed='Exact551candidatepoints,zero displacement;not533warm solver restart. No reparameterization/projection of seed points. First full-body seed screen failing =>technical mismatch, no repair/solver.',representation='Onlyoldnodeswith90<oldsigma<220,exceptfirstandlastinsidefrozen tokeepbothboundarysegments/endpoints/tangents. Eachfreepoint=exactseed+offset*seedcenteredunitnormal;othersbit-identical. Bounds±4m borrow533numericsearchscaleonly;533usedabsoluteoriginalroadnormaloffset,589usesrelative551seednormaloffsetandisNOTthesamefeasibleenvelopeorvalidateddynamicdomain.Linearroad/obstacleguides additionallyrestrict. No globalchord-forward condition.',geometry='Truepolyline ds/arcs recomputed. Signednodecurvature=atan2(adjacentcross,dot)/meanadjacentds. Oldstation labels retained bynodeidentity independentlyofnewtruearc. Zero/nonfinite ds technicalfailure. Roadorderguide=edge dot seedunitsegment>=0;finalstrictpositive andsampledclosedchainnonadjacentintersectioncheck. Notphysicalreverseclaim.',objective='J=.5*(L/Lseed+C/Cseed),seedJ1. LocalL usesfixedoverlapfractionofoldsegmentswith[90,220]. C=R²sum(kappa_i²*dual_ds_i) onendnodesofthoseoverlappingsegments +R⁴sum((kappa_next-kappa_i)²/ds_i) onoverlappingsegments;R3.24m=sourcewheelbase. dual_ds=(previous+nextds)/2. BothC terms dimensionlength;equalrelativebaselineweight is a fixedgeometricpolicy,not time/force law. RequireCseed>0;no weightsweep.',provenance='533normal searchscale4m andgeometricJacobianEPS1e-5m reused asdesignscales only. Unlike533839Dpath/speedNLP/trust-constr,589onecornergeometryonlySLSQP,no speedvariable/profile/clockobjective. R derives(80-(-82))*.02=3.24fromsourceWHEELPOS/SIZE. Relative normalization gives eachseedcomponent1/2.',guides='Fixedlinear supportplanes atfreeoriginalroadnodeindices. Roadnormal=centeredtracknormal,left/rightfromcorrespondingboundaryvertices. Freezeactual8fixtureverticesatseedcenteredtangent,joint0. Centeredtranslation projectedontoactualroadnormal mustkeepmin/maxsupport>=.50frombothroadsideplanes. For eachobstacle fixradialoutwardseedCOMnormal andminfinitebodysupport>=radius+.50. Costonegeometrysupportpackpernode;notfullroadsafety. Seedmustsatisfyallguides>=0elseTECHNICAL_SEED_GUIDE_MISMATCH,no epsilon/planeadjustment.',solver='Exactlyone scipy SLSQP minimize,initialzeros,maxiter20,ftol1e-9,dispFalse,bounds[-4,4]. Fixedlinearconstraintjacobian. ManualforwardgeometryobjectiveJacobianh1e-5m(minusifplusbeyond+4),actualsign denominator. AllgeometryobjectiveevalschargedincludingFDandcachequeries;constraintquerieschargedseparately,sum<=10000. No dynamicsFD,solverrestart,toysolve ormethodswitch.',iterations='Persistallcallbacks<=20withxprivate/objective/components/proxyresidual/cost. Resultx iffinite;onbudgetstoplastcompletedcallbackmajoriterate(notphysicalcertificate). No bestiteratesweep. Seedretainedindependently.',line_search='Atmost12 finalfull-bodyshapesalongonefinalsolverdirection,alpha=2^-k fork0..11. Cheapguide/objective/endpoint/order/selfintersection gatesfirst. RequireL<=Lseed+32ULPandC<=Cseed+32ULP,J<1-32ULP. Firstfull-body-safequalifyingalpha selected;otherwiseexactseedreturned. Thesearestaticdesignacceptance,notphysicalnecessity. No amplitude adaptation oranotheroptimizer.',static='Exactexistingplan513/corner515finitehull4+wheel4 roadunion/finiteboundary/obstacledisks,staticjoint0/bodyforward(-sin a,cos a). Eachsegmentceil(ds/.5)equalintervals inclbothendpoints,headingsegmenttangent,soverticescheckedbothadjacentheadings. Initialseedwholeloop;line_searchonlyaffectedsegmentsj-1/jforfreej,unchangedsegmentposesinheritseed. Selectedonefinalindependentwholeloopaudit. Sampledgap<=.5,notcontinuum/reachabilityproof. No5311.252buffer/nolegacymin1mds.',caps='max20iterations/12fullbodylinesearchshapes/15000fullbodypacks/10000objective+constraintqueries/CPU600wall800 includeimports,prep10charge,tests,failures,solver,screen,audit. Beforeeachscreenreserveremainingfinalfullauditpackscomputedfromcandidate+60CPU/80wall;signalsbeforeaggregatecap. Ifreserveunavailablebudgetcensored,keepseed. No budgetextension.',source_boundary='No actualsource/native/world/force/dynamicsFD/learning/newprofile/newfeedback. Staticpathidentitychangeonly;future549retiming+fixeds400trialseparateproposedcontract. Keeporiginalforce/clipping/body/path3/ref4.85numericlimitswithfutureprefrozennewreferenceobject;old551deviationsdiagnostic,notretroactive588success.',privacy='Offsets,points,fulliterations/journalandstaticposesprivate. Publictechnicalcode/contracts/aggregatesonly.'),caps=dict(iterations=20,line_search_fullbody_shapes=12,geometry_checks=15000,pure_objective_plus_constraint_evaluations=10000,CPU_s=600,wall_s=800),prior_preparation_CPU_wall_charge_s=self.prior,incumbents=dict(actual_s=13.66,source_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0))
        write(C,contract);write(D/'REGISTERED-private.json',dict(contract_sha256=sha(C),source_ticks=0));self.contract=contract
    def pins(self):
        for k,h in self.contract['input_sha256'].items():assert sha(INPUTS[k])==h,('INPUT',k)
        for f,h in self.contract['implementation_sha256'].items():assert sha(G/f)==h,('CODE',f)
    def event(self,name,**data):self.log.write(json.dumps(dict(event=name,**data),allow_nan=False)+'\n')
    def tests(self):
        spec=importlib.util.spec_from_file_location('test_corridor589',G/'tests/test_corridor589.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);r=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(r);self.result['tests']=dict(count=r.testsRun,passed=r.wasSuccessful(),failures=len(r.failures),errors=len(r.errors));write(D/'test-details-private.json',dict(failures=r.failures,errors=r.errors));self.count('pure_test_objective_evaluations',module.TEST_OBJECTIVES+module.TESTCOUNTS['test_geometric_component_evaluations'])
        self.count('objective_evaluations',module.TEST_OBJECTIVES+module.TESTCOUNTS['test_geometric_component_evaluations'])
        for key,n in module.TESTCOUNTS.items():self.count(key,n)
        if not r.wasSuccessful():raise RuntimeError('PURE_TEST_FAILURE')
    def sample_screen(self,p,ids,label,reserve_full=True):
        needed=m.sample_count(p,ids);reserve=m.sample_count(p,range(len(p))) if reserve_full else 0
        if self.cost['geometry_checks']+needed+reserve>15000:raise BudgetStop('SCREEN_RESERVE_GEOMETRY')
        ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);minimum=float('inf');below=0;poses=0;spacing=0.;self.event('SCREEN_STARTED',label=label,expected_packs=needed,remaining_audit_reserve=reserve)
        for i in ids:
            v=p[(i+1)%len(p)]-p[i];t=v/ds[i];n=int(math.ceil(ds[i]/.5));spacing=max(spacing,ds[i]/n)
            for k in range(n+1):
                self.count('geometry_checks');self.count('screen_'+label+'_packs');position=p[i]+(k/n)*v;root=static_pose(self.template,position,t);value=margin(root,self.static['roads'],self.roadindex,self.static['boundary'],self.edge,self.static['obstacles']);minimum=min(minimum,value);below+=int(value<.5);poses+=1;self.event('POSE_MARGIN',label=label,segment=int(i),fraction=k/n,center=position.tolist(),angle=root.planar.angle,margin=value)
        out=dict(label=label,minimum_m=minimum,below_floor=below,geometry_packs=poses,max_sample_spacing_m=spacing,safe=minimum>=.5);self.event('SCREEN_FINISHED',**out);self.log.flush();return out
    def evaluate(self,x):
        self.count('objective_evaluations');key=np.asarray(x,float).tobytes()
        if key in self.cache:self.count('objective_cache_hits');return self.cache[key]
        p=m.points(x,self.b);q=m.components(p,self.b);value=m.objective(q,self.seed_components);self.cache[key]=(value,q);return value,q
    def cons(self,x):self.count('constraint_evaluations');return self.A@x+self.c
    def jac(self,x):
        self.count('objective_gradient_calls');base=self.evaluate(x)[0];out=np.empty(len(x))
        for j in range(len(x)):
            h=-m.EPS if x[j]+m.EPS>4 else m.EPS;y=x.copy();y[j]+=h;out[j]=(self.evaluate(y)[0]-base)/h;self.count('geometry_FD_columns')
        return out
    def constraint_jac(self,x):self.count('constraint_jacobian_calls');return self.A
    def callback(self,x):
        self.count('solver_callback_iterations')
        if self.cost['solver_callback_iterations']>20:raise BudgetStop('ITERATION_CAP')
        self.saved=x.copy();f,q=self.evaluate(x);row=dict(iteration=len(self.iterations)+1,objective=f,components=q,minimum_proxy_residual=float(np.min(self.cons(x))),cost=dict(self.cost),CPU_wall=self.elapsed());self.iterations.append(row);self.event('ITERATION',x=x.tolist(),**row);self.log.flush()
    def strict_improvement(self,q,J):
        def tol(v):return 32*math.ulp(v)
        return J<1-tol(1.) and q['length_m']<=self.seed_components['length_m']+tol(self.seed_components['length_m']) and q['burden_m']<=self.seed_components['burden_m']+tol(self.seed_components['burden_m'])
    def run(self):
        status='TECHNICAL_FAILURE';error=None;self.saved=None;selected=None;optimizer=None;stop=None
        def timeout(*_):raise BudgetStop('AGGREGATE_TIME_SIGNAL')
        signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout);e=self.elapsed();signal.setitimer(signal.ITIMER_PROF,max(.01,600-e['CPU_s']-2));signal.setitimer(signal.ITIMER_REAL,max(.01,800-e['wall_s']-2))
        try:
            self.pins();self.tests();self.static=read(INPUTS['static']);self.old=read(INPUTS['paths'])['candidate'];self.b=m.basis(self.old);self.template=load_root(self.static['root']);self.roadindex=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);seed=self.b['seed'];self.seed_components=m.components(seed,self.b);self.count('objective_evaluations');self.result.update(variables=len(self.b['free']),seed_components=self.seed_components,seed_objective=1.,seed_points_byte_exact=np.array_equal(m.points(np.zeros(len(self.b['free'])),self.b),seed));self.stage='seed_screen';seed_screen=self.sample_screen(seed,range(len(seed)),'seed',True);self.result['seed_screen']=seed_screen
            if not seed_screen['safe']:raise SeedMismatch('STATIC_SEED_FAILED_NO_REPAIR')
            t,_=m.frames(seed)
            def fixture(j):return [np.asarray(v) for v in polygons(static_pose(self.template,seed[j],t[j]))]
            self.A,self.c,categories=m.guides(self.b,self.static,fixture,self.count);self.count('constraint_evaluations');self.result['seed_proxy']=dict(rows=len(self.c),minimum=float(self.c.min()),categories={k:float(self.c[np.asarray(categories)==k].min()) for k in sorted(set(categories))})
            if self.c.min()<0:raise SeedMismatch('SEED_GUIDE_MISMATCH_NO_REPAIR')
            self.saved=np.zeros(len(self.b['free']));self.stage='solver';self.count('solver_calls')
            try:
                r=minimize(lambda x:self.evaluate(x)[0],self.saved.copy(),jac=self.jac,method='SLSQP',bounds=[(-4.,4.)]*len(self.saved),constraints=[dict(type='ineq',fun=self.cons,jac=self.constraint_jac)],callback=self.callback,options=dict(maxiter=20,ftol=1e-9,disp=False));direction=np.asarray(r.x,float);optimizer=dict(success=bool(r.success),status=int(r.status),message=str(r.message),iterations=int(r.nit),returned_objective=float(r.fun))
            except BudgetStop as exc:stop=str(exc);direction=self.saved.copy()
            if not np.all(np.isfinite(direction)):raise RuntimeError('NONFINITE_SOLVER_RETURN')
            self.stage='line_search'
            for k in range(12):
                self.guard();alpha=2.**(-k);x=alpha*direction;J,q=self.evaluate(x);p=m.points(x,self.b);rec=dict(index=k+1,alpha=alpha,maximum_abs_offset_m=float(np.max(np.abs(x))),objective=J,components=q,minimum_proxy_residual=float(np.min(self.cons(x))),fullbody_checked=False)
                cheap=np.all(np.abs(x)<=4) and rec['minimum_proxy_residual']>=0 and self.strict_improvement(q,J) and np.all(m.projection_order(p,self.b)>0) and all(e['position_error_m']==0 and e['tangent_error_rad']==0 for e in m.endpoint_metrics(p,self.old,self.b))
                if cheap:
                    hits=intersections(p,self.count,self.guard);cheap=not hits;rec['self_intersections']=len(hits)
                if cheap:
                    self.count('line_search_fullbody_shapes');screen=self.sample_screen(p,self.b['affected'],'line'+str(k+1),True);rec.update(fullbody_checked=True,screen=screen)
                    if screen['safe']:selected=dict(x=x,p=p,J=J,components=q,screen=screen,alpha=alpha)
                self.validations.append(rec);self.event('FINAL_LINE_SEARCH',**rec)
                if selected is not None:break
            self.stage='audit';p=selected['p'] if selected else seed;final=self.sample_screen(p,range(len(p)),'final_audit',False);self.result['final_audit']=final
            if not final['safe']:raise RuntimeError('FINAL_STATIC_AUDIT_MISMATCH')
            status='STATIC_CORRIDOR_IMPROVEMENT_SELECTED' if selected else 'NO_STATIC_IMPROVEMENT_RETURN_EXACT_SEED'
            new=m.polyline(p);write(D/'selected-geometry-private.json',dict(path=new,oldstation=self.b['sigma'].tolist(),offsets=(selected['x'].tolist() if selected else np.zeros(len(self.b['free'])).tolist()),seed_returned=selected is None));delta=np.linalg.norm(p-seed,axis=1);self.result['selected']=dict(seed_returned=selected is None,objective=selected['J'] if selected else 1.,components=selected['components'] if selected else self.seed_components,full_static_minimum_m=final['minimum_m'],max_point_displacement_m=float(delta.max()),changed_nodes=int(np.sum(delta>0)),endpoint_metrics=m.endpoint_metrics(p,self.old,self.b),outside_and_guards_exact=np.array_equal(p[np.setdiff1d(np.arange(len(p)),self.b['free'])],seed[np.setdiff1d(np.arange(len(p)),self.b['free'])]),true_length_m=new['length'],alpha=selected['alpha'] if selected else 0.,private_geometry_sha256=sha(D/'selected-geometry-private.json'))
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED_SEED_RETAINED' if isinstance(exc,BudgetStop) else 'TECHNICAL_SEED_MISMATCH' if isinstance(exc,SeedMismatch) else 'TECHNICAL_FAILURE';write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc()));self.result['feasible_original_input_preserved']=True;self.result['returned_original_geometry_locator']=dict(input_sha256=self.contract['input_sha256']['paths'],selector='candidate')
        finally:
            self.stage='audit';self.pins();self.log.flush();self.log.close();write(D/'iterations-private.json',self.iterations);write(D/'line-search-private.json',self.validations);self.result.update(status=status,error=error,optimizer=optimizer,optimizer_budget_stop=stop,counts=dict(self.cost),CPU_wall=self.elapsed(),contract_sha256=sha(C),private_journal_sha256=sha(self.log_path),iterations=self.iterations,line_search=self.validations,source_ticks=0,force_evaluations=0,native_actions=0,worlds=0,dynamics_FD=0,new_profiles=0,learning=0,HOLDOUT=0,SEALED=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0);write(G/'retry/corridor589_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
        return self.result
if __name__=='__main__':Study().run()

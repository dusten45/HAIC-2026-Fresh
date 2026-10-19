"""Register first, run pure tests then one sampled static design. No source entry."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import ast,copy,datetime,hashlib,json,math,signal,subprocess,sys,traceback
from collections import Counter
from dataclasses import replace
from pathlib import Path
import numpy as np
from retry import smoother588_math as m
from retry.plan513_model import load_root,polygons
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response588-private');C=G/'retry/smoother588_contract.json'
INPUTS=dict(paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),proposal=G/'retry/reselect587_next_contract.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
    p.chmod(0o600 if p.is_relative_to(D) else 0o644)
class BudgetStop(RuntimeError):pass

def static_pose(template,center,tangent):
    a=math.atan2(-tangent[0],tangent[1]);delta=a-template.planar.angle;c,s=math.cos(delta),math.sin(delta);p=template.planar
    levers=tuple((c*x-s*y,s*x+c*y) for x,y in p.levers);wheels=tuple(replace(w,heading=a,offset=(0.,0.)) for w in p.linear.wheels)
    # Rigid static placement about template COM. No integration/history change.
    return replace(template,center=tuple(center),planar=replace(p,angle=a,levers=levers,joints=(0.,)*4,rates=(0.,)*4,yaw=0.,angular_momentum=0.,linear=replace(p.linear,wheels=wheels,velocity=(0.,0.))))

class Design:
    def __init__(self):
        self.counts=Counter();self.events=[];self.result={};self.prior=10.;self.deadline=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc);D.mkdir(mode=0o700,exist_ok=False);self.register()
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior,wall_s=time.perf_counter()-START_WALL+self.prior)
    def guard(self):
        e=self.elapsed()
        if e['CPU_s']+15>=900 or e['wall_s']+25>=1100:raise BudgetStop('AGGREGATE_TIME_RESERVING_AUDIT')
        if datetime.datetime.now(datetime.timezone.utc)>=self.deadline:raise BudgetStop('DEADLINE')
    def count(self,k,n=1):
        self.guard();cap={'geometry_checks':65000,'analytic_profile_bound_evaluations':100000}.get(k)
        if cap is not None and self.counts[k]+n>cap:raise BudgetStop(k)
        self.counts[k]+=int(n)
    def event(self,name,**data):self.events.append(dict(event=name,**data))
    def register(self):
        if (self.deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()<1130:raise BudgetStop('INSUFFICIENT_DEADLINE_RESERVE')
        files=[G/'retry/smoother588_math.py',Path(__file__),G/'tests/test_smoother588.py',G/'retry/plan513_model.py',G/'retry/corner515_model.py',G/'retry/brake506_geometry.py',G/'retry/brake508_corridor.py',G/'retry/brake510_common.py',G/'core/vendor/car_dynamics.py',G/'retry/envelope500.py',G/'retry/structure537_control.py',G/'retry/launch540_control.py',G/'retry/drive519_control.py',G/'retry/lap518_control.py',G/'retry/retime549_design.py']
        files=sorted(set(files)|{Path(module.__file__).resolve() for module in tuple(sys.modules.values()) if getattr(module,'__file__',None) and Path(module.__file__).is_file() and Path(module.__file__).resolve().is_relative_to(G/'retry')})
        contract=dict(study=588,status='FROZEN_BEFORE_PURE_TESTS_AND_SINGLE_STATIC_DESIGN',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),deadline_utc=self.deadline.isoformat(),proposal_sha256=sha(INPUTS['proposal']),scope='Exactly587singleline/profile. All gates run once for static diagnostics; if any static gate fails, no profile/source/positive/candidate/replay. If all pass, frozen profile generation then source registration required with these unchanged scientific settings. No automatic shape/numeric/endpoint/sample/profile/backup retry.',specification=dict(frame='Worldxy,CCWsignedcurvature;leftnormal=(-ty,tx),sourcebodyforward=(-sin(a),cos(a));bodyangle=atan2(-tx,ty).',endpoints='At90/220 choosefirstsegmentwhoseend_arc>=s(bisect_left),linearposition and signedstorednodecurvature interpolation,segmentunit tangent. No closedpathwrap for these firstlap endpoints.',hermite='L=Euclideanchord. pprime=L*t,psecond=L²*k*n;fixedclosedformcoefficients in pinnedmath;u=k/512 exactly513samples. Exact endpoint positions assigned from original interpolation,interiorHornerbinary64.',joins='Preserveoutsideoldvertices strictoldarc<90/>220,insert513once. Recomputeactualpositivepolyline ds,truearcs and signedatan2turn/meanadjacentds forwholeloop,includingjoinneighbours. Oldpolyline is not a C2curve.',peak='new=max(absanalytic513curvature,absdiscretenodesreplacedandoneoutsideeachjoin));old=max(absrecomputedoldnodecurvature in[90,220]andoneoutsideeachjoin).Requirestrictnew<old. This is a design gate,notphysicalnecessity.',reverse='Requireall513derivativenorms>0 and pprime dot unitendchord>0 (chord-monotone). oldstation sigma90+130u strictlyincreasing separately. Sampled tests notcontinuumcertificates.',intersection='Allnonadjacentclosedpolylinepairs includingnew-oldoutside. Excludeadjacent and first-last seam sharedendpoint. Exactbinary64orientation/collinearbounding;AABBbroadphasecountseparate,notepsilonrelaxed.',staticbody='Everycandidatepathvertex inclunchangedoutsideonce.513newvertexheading usesanalyticd1;outsideheadingleftoutgoingsegment. RotateoriginalsourceCOM-relativeleversrigidlyfromtemplateangle;bodyoriginshiftderivedbyunchangedplan513polygons/HULL1..4*SIZE. Wheelsrectangles(+/-.28,+/-.54),alljoint0 andwheelheading=bodyangle. No futurepose/jointreachability claim.',staticmargin='Exactexistingcorner515.margin/plan513.margin:everyfinitehull/wheelpolygonboundarydistance signedbyallverticescoveredbysavedconvexroadunion;obstaclecirclepolygonclearance. No centerline-only substitute,no531filters/extra1.252floor/min1mds. Requiremargin>=.50 atallvertices;all513evaluatedevenafterfirstbadforregisteredstaticdiagnostics.',curvature_profile='Onlynewdiscretegeometricnodecurvature;segmentmaxadjacent,capmaxadjacentsegments.No oldobservedcurvature.',retiming='549formula:four400N,wheellimit.999*400,rootmass/lever-derivedaxleweights,effectiveMASS/REAR fromenvelope500. cap90. Forpass0..2n-1:descendingbackwardthenascendingforward;restrictreturnsifcurrent<=other,thenoneaccboundtest,else40binarymidpointupdates. Stopwhenlistsidenticalelsefail. Launchforwardfrom0once. Validatebothperiodicandlaunchallsegmentsinorder. Chargecapvertex/accpack/finalsegmentpackeachoneanalyticboundevaluation;fourwheeloutputsperpack,notphysicalforcekernel.',backup='Samenewgeometry/arcs;periodic/launchQ=min(newcandidateQ,80²,oldbackupQinterpolatedatsigma),firstlaplaunchclamp,periodicmodulo;leftsegmenttie. Sigmaofclosingnode=oldlength. Noactualspeedfitting.',projection='Pinnedm.project matcheslap518:allsegments,float64clippedprojection,firstsegmentmin-distance ties,Pythonroundbankerswrapnearestprevious;admitprevious-5..previous+30;initials>L/2subtractL. Newdynamicprogress separateold551projectionforcommonplanes. No state movement at raw96;switchgeometryonlyafteroriginalfirst96raw.',dynamic='Original577positiveinitialtos400wholehold<=416rawandfullidentity. Candidateonlyfromfullraw96throughnewplan<=320raw;commonold551fixeds300/s400plane+oldprojection±10/corridor3/firstforwardcross/fullholdsafe. Alloriginalprefixcontractthrough96;newcontractfrom97includingreplay. Strictpath3/reference4.85numericunchanged,newreferenceobjectexplicit. Old551deviationsdiagnostic. no-safe-actionstops. Successfullwindows400>32ULPthenoneexactinitialfixedtapereplay<=416;no100/500msgate/whole/native.',budget='Allpuretests/design/profile/imports/failures/auditandfuturephysicsaggregate;reserve416replay+auditCPU15/wall25beforeeveryforecastgroup. Executedraw<=1152/allforecastsattemptandcompleted<=60000/ext260000/int240000/total500000/geometry65000/analyticprofile100000/CPU900/wall1100. Native/world/HOLDOUT/SEALED0.'),input_sha256={k:sha(p) for k,p in INPUTS.items()},implementation_sha256={str(p.relative_to(G)):sha(p) for p in files},preparation_prior_CPU_wall_charge_s=self.prior,prior_meaning='Conservative10s for source0 preliminary file reads/metadata/registration scaffolding; measured process imports/tests/design/profile/audit additionally included. Conversation/editing idle not scientific runtime.',counts_semantics='geometry_checks=onefullfinitebodypose/staticorforecast/currentrootcheck;bbox/exactsegmenttestsandfixture/polygonqueriesseparatecounters.Nophysicalforce/tickcountforpuregeometry.',incumbents=dict(actual_s=13.66,source_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0),privacy='Rawgeometry/state/staticevents/coefficients/paths/privateevidenceoutsideGit;publictechnicalcode/contracts/aggregatesonly.')
        write(C,contract);write(D/'REGISTERED-private.json',dict(contract_sha256=sha(C),source_ticks=0));self.contract=contract
    def verify_pins(self):
        for k,h in self.contract['input_sha256'].items():assert sha(INPUTS[k])==h,('INPUT_HASH',k)
        for f,h in self.contract['implementation_sha256'].items():assert sha(G/f)==h,('CODE_HASH',f)
    def pure_tests(self):
        import importlib.util,unittest
        spec=importlib.util.spec_from_file_location('test_smoother588',G/'tests/test_smoother588.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);suite=unittest.defaultTestLoader.loadTestsFromModule(module);result=unittest.TestResult();suite.run(result)
        self.result['pure_tests']=dict(tests=result.testsRun,passed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors));write(D/'pure-test-details-private.json',dict(failures=result.failures,errors=result.errors));self.event('PURE_TESTS',**self.result['pure_tests'])
        for key,n in module.TESTCOUNTS.items():self.count(key,n)
        if not result.wasSuccessful():raise RuntimeError('PURE_TESTS_FAILED')
    def run(self):
        status='TECHNICAL_FAILURE';error=None;start=time.process_time()
        def timed_stop(*_):raise BudgetStop('AGGREGATE_SIGNAL_RESERVING_AUDIT')
        signal.signal(signal.SIGPROF,timed_stop);signal.signal(signal.SIGALRM,timed_stop);e=self.elapsed();signal.setitimer(signal.ITIMER_PROF,max(.01,900-e['CPU_s']-15));signal.setitimer(signal.ITIMER_REAL,max(.01,1100-e['wall_s']-25))
        try:
            self.guard();self.verify_pins();self.pure_tests();self.guard();paths=read(INPUTS['paths']);static=read(INPUTS['static']);old=paths['candidate'];self.event('STATIC_DESIGN_STARTED',contract_sha256=sha(C));z=m.construct(old);self.count('curve_position_samples',513);self.count('curve_derivative_samples',1026);write(D/'geometry-private.json',z);self.result['geometry']=z['diagnostics'];hits=m.intersections(z['path']['points'],self.count,self.guard);self.result['self_intersections']=len(hits);self.event('SELF_INTERSECTION_VERDICT',pairs=hits)
            template=load_root(static['root']);idx=bounds(static['roads']);edge=boundary_index(static['boundary']);margins=[];newmargins=[];outside=[];pts=np.asarray(z['path']['points']);d1=np.asarray(z['d1']);new_start=z['new_start'];new_end=z['new_end']
            for i,p in enumerate(pts):
                self.guard();t=d1[i-new_start] if new_start<=i<=new_end else pts[(i+1)%len(pts)]-p
                if np.linalg.norm(t)==0:raise ValueError('ZERO_STATIC_HEADING')
                t=t/np.linalg.norm(t);root=static_pose(template,p,t);self.count('geometry_checks');self.count('static_fullbody_geometry_checks');self.count('static_fixture_polygons',8);value=margin(root,static['roads'],idx,static['boundary'],edge,static['obstacles']);margins.append(float(value));(newmargins if new_start<=i<=new_end else outside).append(float(value));self.event('STATIC_POSE',vertex=i,oldstation=z['oldstation'][i],center=p.tolist(),angle=root.planar.angle,margin=float(value),polygons=polygons(root))
            self.result['static_margin']=dict(minimum_m=min(margins),new513_minimum_m=min(newmargins),outside_minimum_m=min(outside),below_floor=sum(v<.5 for v in margins),new513_below_floor=sum(v<.5 for v in newmargins),minimum_vertex=int(np.argmin(margins)),minimum_new_sample=int(np.argmin(newmargins)),poses=len(margins),model_floor_m=.5)
            g=z['diagnostics'];gates=dict(derivative_positive=g['minimum_derivative_norm']>0,chord_forward=g['minimum_forward_chord_derivative']>0,oldstation_monotone=all(a<b for a,b in zip(z['oldstation'],z['oldstation'][1:])),no_self_intersection=not hits,peak_curvature_reduced=g['new_peak_abs_curvature']<g['old_peak_abs_curvature'],finite_body_static_margin=min(margins)>=.5);self.result['static_gates']=gates;self.event('STATIC_GATES',**gates)
            if not all(gates.values()):status='STATIC_DESIGN_GATE_FAILED_SOURCE0';self.result['first_failed_gate']=next(k for k,v in gates.items() if not v)
            else:
                high,low,pinfo=m.retime(z['path'],paths['backup'],z['oldstation'],static,self.count,self.guard);self.result['profile']=pinfo;write(D/'frozen-paths-private.json',dict(candidate=high,backup=low));self.result['frozen_plan_sha256']=sha(D/'frozen-paths-private.json');status='STATIC_AND_PROFILE_PASS_READY_FOR_SOURCE_REGISTRATION'
        except BaseException as exc:
            status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'TECHNICAL_FAILURE';error=type(exc).__name__+':'+str(exc);write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc()))
        finally:
            # Source entry is absent from this stage; only a passing gate can authorize its construction.
            self.verify_pins();write(D/'static-events-private.json',self.events);self.result.update(status=status,error=error,counts=dict(self.counts),CPU_wall=self.elapsed(),source_ticks=0,attempted_raw=0,completed_model_ticks=0,external_force=0,internal_force=0,actual_raw=0,native_actions=0,new_world=0,HOLDOUT=0,SEALED=0,new_FD=0,new_solver=0,positive_control_runs=0,candidate_runs=0,replay_runs=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0,contract_sha256=sha(C),private_events_sha256=sha(D/'static-events-private.json'),private_geometry_sha256=sha(D/'geometry-private.json') if (D/'geometry-private.json').exists() else None)
            write(G/'retry/smoother588_result.json',self.result);print(json.dumps(self.result,indent=2))
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        return self.result

if __name__=='__main__':
    study=Design();study.run()

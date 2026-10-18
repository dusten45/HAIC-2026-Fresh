"""Bounded pure scalar adversarial verification; never creates physics objects."""
import time
START=time.perf_counter(); CPU=time.process_time()
import ast, hashlib, importlib.abc, json, math, os, signal, sys
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path=None,target=None):
        if name.startswith(('Box2D','core.vendor')) or name in ('retry.terminal410_model','retry.source_vehicle_transition','retry.diagnose','retry.pilot420_backend','retry.observer435','retry.law473'):
            raise RuntimeError('500_FORBIDDEN_IMPORT:'+name)
        return None
sys.meta_path.insert(0,NoPhysics())
import numpy as np
from retry import envelope500 as law
G=Path(__file__).resolve().parents[1]; R=Path('/workspace/haic-private-retry-20261009');D=R/'stage500';W=D/'verification-final'

def guard(*args):
    if time.process_time()-CPU+10>=180 or time.perf_counter()-START+20>=240: raise RuntimeError('500_RESOURCE_STOP')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def independent(s,v,sigma,arcs,speeds,a):
    # Independent direct trajectory/crossing evaluation, Decimal400 sqrt. Does
    # not call law.context, residuals, _bound or use the eliminated crossing law.
    with localcontext() as dc:
        dc.prec=400
        cv=lambda x: Decimal.from_float(float(x))
        s,v,sig,a=map(cv,(s,v,sigma,a));B=cv(law.BRAKE);tau=Decimal('0.08')
        if a < -B or v+a*tau < 0 or sig+a*tau < 0:return False
        if a>min(cv(law.REAR),Decimal(80000)/(cv(law.MASS)*cv(float(v)+2.7))):return False
        for xx,rr in zip(arcs[1:],speeds[1:]):
            d=cv(xx)-s;r=cv(rr)
            if d<0:continue
            if d==0:
                if v>r:return False
                continue
            travel=sig*tau+a*tau*tau/2
            if travel>=d:
                disc=sig*sig+2*a*d
                if disc<0:return False
                den=sig+disc.sqrt()
                if den<=0:return False
                tc=2*d/den
                if v+a*tc-r>Decimal('1e-370'):return False
            for t in map(Decimal,('0.02','0.04','0.06','0.08')):
                dx=sig*t+a*t*t/2
                if dx<d and (v+a*t)**2-r*r-2*B*(d-dx)>Decimal('1e-370'):return False
        return True


def run():
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('500_CPU')))
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('500_WALL')))
    signal.setitimer(signal.ITIMER_PROF,max(.001,170-(time.process_time()-CPU)))
    signal.setitimer(signal.ITIMER_REAL,max(.001,220-(time.perf_counter()-START)))
    plan=json.loads((D/'plan-private.json').read_text()); assert plan['registered_before_numerics']
    assert not W.exists(); W.mkdir(mode=0o700)
    pin={'code':sha(G/'retry/envelope500.py'),'verify':sha(__file__)}
    (W/'executed-code-pins-private.json').write_text(json.dumps(pin,indent=2)+'\n')
    budget=R/'project-effective-budget-v495.json'; assert sha(budget)==plan['budget_sha256']
    fixedpath=R/'stage269/N1-plan-private.json'; fixed=json.loads(fixedpath.read_text()); model=fixed['model']
    assert model['effective_mass']==law.MASS and model['rear_traction_accel']==law.REAR and model['brake_accel']==law.BRAKE
    source=ast.parse((G/'retry/scalar392_audit.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='pedals')
    ns={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),'pinned_pedals','exec'),ns)
    source_checks=0
    for a in [-1000.,-law.BRAKE,-1.,-0.,0.,1.,law.REAR,1000.]:
        for v in [0.,1e-8,10.,100.,1000.]:
            got=ns['pedals'](a,v,model);g,b=law.source_pedals(a,v)
            assert (g,b)==(got['gas'],got['brake']);source_checks+=1
    fixtures=[
      ('far',1.,20.,20.,[0.,1000.],[0.,100.]),
      ('crossed',1.,10.,10.,[0.,1.1,100.],[0.,9.9,100.]),
      ('switch_root',1.,10.,10.,[0.,1.8,100.],[0.,10.,100.]),
      ('brake',1.,30.,30.,[0.,21.,100.],[0.,10.,100.]),
      ('current_equal',1.,10.,10.,[0.,1.,100.],[0.,10.,100.]),
      ('current_empty',1.,11.,11.,[0.,1.,100.],[0.,10.,100.]),
      ('stationary',1.,0.,0.,[0.,2.,100.],[0.,10.,100.]),
      ('sigma_zero_empty',1.,30.,0.,[0.,1.01,100.],[0.,1.,100.]),
      ('zero_accel',1.,10.,10.,[0.,1.1,100.],[0.,10.,100.]),
      ('stop_at_end',1.,.01,.01,[0.,1.001,100.],[0.,.001,100.]),
      ('terminal_cross',99.9,10.,10.,[0.,100.],[0.,12.]),
      ('sigma_unequal',1.,30.,12.,[0.,2.,10.,100.],[0.,25.,15.,100.]),
    ]
    # Deterministic input coverage, never a gain/profile/parameter search.
    for i in range(48):
        v=float(1+(i*37)%130);sig=v*[0.,.25,.75,1.][i%4]
        d=[.001,.02,.1,1.,10.,100.,1000.,10000.][i%8]
        r=float(1+(i*23)%120)
        fixtures.append(('matrix_'+str(i),1.,v,sig,[0.,1+d,1+d+37,20001.],[0.,r,1.+(i*11)%130,150.]))
    counts={'fixtures':0,'feasible':0,'empty':0,'grid_points':0,'mapped':0,'mapping_stop':0,'independent_checks':0};rows=[];max_error=0.; max_adjust=0
    for name,s,v,sig,arcs,speeds in fixtures:
        guard();counts['fixtures']+=1;c=law.context(s,v,sig,arcs,speeds)
        try:
            sol,c=law.solve(s,v,sig,arcs,speeds);counts['feasible']+=1
        except law.EnvelopeStop as e:
            assert str(e)=='EMPTY_SET',(name,e)
            assert not independent(s,v,sig,arcs,speeds,float(c['low'])) or law.residuals(c,c['low'])
            counts['empty']+=1;sol=None
        # Long range grid across entire domain, including endpoints and boundary
        # neighbours, independently evaluates direct trajectory residuals.
        lo,hi=float(c['low']),float(c['high'])
        points=[lo+(hi-lo)*j/256 for j in range(257)]
        if sol:points += [sol['accel'],math.nextafter(sol['accel'],-math.inf),sol['next_float']]
        for a in points:
            guard();ok=independent(s,v,sig,arcs,speeds,a);counts['grid_points']+=1
            exact=not law.residuals(c,a)
            assert ok==exact,(name,a,'ORACLE_DISAGREE')
            if ok:assert sol is not None and a<=sol['accel'],(name,a,'GRID_COUNTEREXAMPLE')
        if sol:
            assert independent(s,v,sig,arcs,speeds,sol['accel'])
            assert not independent(s,v,sig,arcs,speeds,sol['next_float'])
            counts['independent_checks']+=2
            try:
                mapped=law.command(sol,c,.125);counts['mapped']+=1
                assert independent(s,v,sig,arcs,speeds,mapped['scalar_mapped_accel'])
                assert mapped['action'][0]==.125
                max_error=max(max_error,abs(mapped['scalar_mapping_error']));max_adjust=max(max_adjust,mapped['float32_ulp_adjustments'])
            except law.EnvelopeStop as e:
                assert str(e)=='FLOAT32_MAPPING_EMPTY_OR_UNCERTIFIED';counts['mapping_stop']+=1
        rows.append({'fixture':name,'status':'FEASIBLE' if sol else 'EMPTY','selected_accel':None if sol is None else sol['accel']})
    # Explicit unsupported inputs and closed-domain ownership.
    negatives=[('terminal',(100.,10.,10.,[0.,100.],[0.,10.])),('reverse',(1.,10.,-.001,[0.,100.],[0.,10.])),('negative_speed',(1.,-1.,0.,[0.,100.],[0.,10.])),('nan',(1.,math.nan,0.,[0.,100.],[0.,10.])),('infinity',(1.,10.,0.,[0.,math.inf],[0.,10.])),('duplicates',(1.,10.,0.,[0.,2.,2.],[0.,10.,10.])),('zero_node_speed',(1.,10.,0.,[0.,100.],[0.,0.])),('start_no_launch',(0.,0.,0.,[0.,100.],[0.,10.])),('past_terminal',(101.,10.,0.,[0.,100.],[0.,10.]))]
    reasons={}
    for name,args in negatives:
        try:law.solve(*args)
        except law.EnvelopeStop as e:reasons[name]=str(e)
        else:raise AssertionError('UNSUPPORTED_ACCEPTED:'+name)
    # Source rows are exposed DEV diagnostics, not a counterfactual rollout.
    tracepath=R/'stage472-native/actual_Projected4ReferenceCommonPulse/trace-private.jsonl'
    trace=[json.loads(x) for x in tracepath.read_text().splitlines()]
    profilepath=R/'stage466-numeric-recovery1/projection-and-segments-private.json';nodes=json.loads(profilepath.read_text())['projected_nodes']
    arcs=[0.];
    for dx in fixed['free_profile']['ds']:arcs.append(arcs[-1]+dx)
    # Existing417 projection supplies sigma from raw hull COM velocity and line
    # tangent. Use its already saved499 canonical progress/index, no model import.
    from retry.signed417_executor import canonical_projection
    saved=[]
    indices=sorted(set([22,125,170]+[22+int((170-22)*j/15) for j in range(16)]))
    for i in indices:
        guard();row=trace[i];pre=row['pre'];q=canonical_projection(fixed['line'],pre['pos'],pre['vel'],row['memory_before']['C']['phase']);v=math.hypot(*pre['vel']);sig=q['sigma'];s=q['arc']
        try:
            z=law.act(row['nominal'],'FIRST_LAP',s,v,sig,arcs,nodes)
            assert independent(s,v,sig,arcs,nodes,z['selection']['accel'])
            assert not independent(s,v,sig,arcs,nodes,z['selection']['next_float'])
            assert independent(s,v,sig,arcs,nodes,z['scalar_mapped_accel'])
            saved.append({'global_hold':i+1,'status':'SCALAR_FEASIBLE','selected_accel':z['selection']['accel'],'mapped_error':z['scalar_mapping_error']})
        except law.EnvelopeStop as e:saved.append({'global_hold':i+1,'status':str(e)})
    # Ensure sources/pinned exact model and budget still match, no evolution.
    assert sha(budget)==plan['budget_sha256'];guard()
    result={'stage':500,'status':'PURE_SCALAR_VALIDATION_PASS','counts':counts,'source_pedal_exact_checks':source_checks,'negative_domains':reasons,'max_float32_scalar_mapping_error_m_s2':max_error,'max_float32_ulp_adjustments':max_adjust,'saved_contexts':saved,'saved_contexts_scope':'Fixed evenly spaced prior472 holds plus23/126/171. Off-policy scalar diagnostics only, no dynamics or actual promotion.','source_pins':pin,'exact_model':model,'times':'Exact rationals k/50 k1..4, not exact binary64 .02.','continuous_time_envelope_claimed':False,'maximality':'Monotone admissible set + algebraic partition + independent Fraction feasible and nextafter infeasible. Decimal80 seeds only; grid is counterexample search, not continuum proof.','no_physics_world_reset_integration_seed_HOLDOUT_SEALED':0,'research_remaining':26027,'reserve':84000,'reserve_used':0,'CPU_s':time.process_time()-CPU,'wall_s':time.perf_counter()-START,'CPU_cap_s':180,'wall_cap_s':240}
    private=dict(result,synthetic_fixture_rows=rows,input_pins={str(p):sha(p) for p in [tracepath,fixedpath,profilepath,R/'project-effective-budget-v495.json']})
    data=json.dumps(private,ensure_ascii=False,indent=2)+'\n';assert len(data)<4*1024**2
    (W/'numeric-result-private.json').write_text(data);(W/'numeric-result-private.json').chmod(0o600)
    public=dict(result);public['saved_contexts']={'count':len(saved),'scalar_feasible':sum(x['status']=='SCALAR_FEASIBLE' for x in saved),'statuses':sorted(set(x['status'] for x in saved)),'per_context_results_private':True}
    (G/'retry/envelope500_result.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':run()

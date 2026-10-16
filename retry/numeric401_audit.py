"""Independent 90-digit residual audit with operation-derived binary64 bounds."""
import datetime,hashlib,json,math,sys,time
from decimal import Decimal,localcontext
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def D(x):return Decimal.from_float(float(x))
def gamma(n):
 u=Decimal(2)**-53;return n*u/(1-n*u)
def classify(left,right,n):
 residual=left-right;bound=gamma(n)*right
 return dict(residual=str(residual),bound=str(bound),classification='CERTIFIED_VIOLATION' if residual>bound else 'ROUNDING_COMPATIBLE_POSITIVE' if residual>0 else 'NONPOSITIVE')
def prepare(root):
 d=root/'stage401';assert not d.exists();d.mkdir(mode=0o700);p398=read(root/'stage398/plan.json');fixed=Path(p398['fixed_plans']['N1']);v=read(root/'project-effective-budget-v420.json');assert v['research_remaining']==32072 and v['final_reserved_actions']==84000
 p=dict(stage=401,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],fixed_plan=str(fixed),numeric_method='90digitDecimal exactbinary64inputs; u=2^-53,gamma_n=nu/(1-nu). Driveboundgamma8*(v_i²+2A_i ds);brakegamma6*(v_next²+2Bds);uppergamma4*C. No observedresidualchosen tolerance. Normalfinitepositive arithmetic only. Positiveexactresidualwithinbound isroundingcompatible,notexactrealfeasibility.',operation_derivation='DriveA:add+2divisions<=gamma3;vi²1op;2*A*ds2ops;positive sum1op =>gamma6rhs; correctlyroundedsqrt plus storedspeed squared contributes2u=>gamma8. Braketermneeds2ops notA3;rhs<=gamma4, sqrtandsquare2=>gamma6. Lateraldivision1+sqrt/square2 roundedupper <=gamma4;100cap exact. Mincannotenlarge bound. 2multiplication countedconservatively although exactwhen normal.',controls='Beforeprofileclassification runexact-nonpositive,roundedsqrt-positive and >4bound-positive scalarcontrols acrossscales. No changesoriginalprofile. Detectabovederivedbandviolations;subbandtruepositivesindeterminate,notcertifiedphysicalfeasible.',numeric_gate='Controlsallpass;allprofilevaluesnormalfiniteorallowedinitial0; nonnegativeinitial0terminalpositive;no highprecisionresidual>independentoperationbound. Positivewithinboundreported,notzeroed. Any actualviolation/technicalfailuregloballystopsdependentstages.',numeric_CPU_cap_s=10,model_tick_cap=12288,CPU_cap_s=180,wall_cap_s=300,max_parallel=2,native_cap=0,actor_cap=0,learning_cap=0,SEALED_cap=0,reserve_use=0,conditional='Afternewnumericgateonly, snapshotbranch/independencequalification,thenunchanged400/3996candidatelexicographic2x2,firstactualqualificationfailurestops. Prior400remainsunqualified.',sources={str(f):sha(f) for f in [Path(__file__),fixed,root/'project-effective-budget-v420.json',root/'stage400/plan.json',root/'stage400/profile-result.json',root/'stage400/result.json',root/'research-deadline-current.json',G/'retry/source_vehicle_transition.py',G/'retry/replay400_run.py',G/'retry/envelope399_result.md',G/'retry/executor397.py',G/'retry/racing258_plan.py']},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');print('401 rounding-aware gate preregistered before controls/profile evaluation')
def run(root):
 d=root/'stage401';p=read(d/'plan.json');assert not(d/'numeric-result.json').exists()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 start,cpu=time.perf_counter(),time.process_time();rows=[];controls=[]
 with localcontext() as ctx:
  ctx.prec=90
  for n in [4,6,8]:
   for scale in [Decimal('0.001'),Decimal(2),Decimal(10000)]:
    below=scale-gamma(n)*scale;far=scale+4*gamma(n)*scale
    good=classify(below,scale,n);bad=classify(far,scale,n);assert good['classification']=='NONPOSITIVE' and bad['classification']=='CERTIFIED_VIOLATION';controls.append(dict(n=n,scale=str(scale),negative=good,positive=bad,passed=True))
  sr=D(math.sqrt(2.))**2-Decimal(2);roundtest=classify(D(math.sqrt(2.))**2,Decimal(2),8);assert sr>0 and roundtest['classification']=='ROUNDING_COMPATIBLE_POSITIVE';controls.append(dict(kind='binary64sqrt2squared_exactpositive',result=roundtest,passed=True))
  f=read(Path(p['fixed_plan']));v=[D(x) for x in f['free_profile']['speed']];ds=[D(x) for x in f['free_profile']['ds']];k=[abs(D(x)) for x in f['free_profile']['curvature']];m={n:D(x) for n,x in f['model'].items()};W=[a*a for a in v]
  for i in range(len(ds)):
   A=min(m['rear_traction_accel'],Decimal(80000)/(v[i]+D(2.7))/m['effective_mass']);drive=classify(W[i+1],W[i]+2*A*ds[i],8);brake=classify(W[i],W[i+1]+2*m['brake_accel']*ds[i],6);C=min(Decimal(10000),m['lateral_accel']/max(k[i],D(1e-6)));upper=classify(W[i],C,4);rows.append(dict(index=i,drive=drive,brake=brake,upper=upper))
  terminal=classify(W[-1],min(Decimal(10000),m['lateral_accel']/max(k[0],D(1e-6))),4);rows.append(dict(index=len(ds),upper=terminal))
  summary={}
  for name in ['drive','brake','upper']:
   rr=[r[name] for r in rows if name in r];summary[name]=dict(rows=len(rr),nonpositive=sum(r['classification']=='NONPOSITIVE' for r in rr),rounding_compatible_positive=sum(r['classification']=='ROUNDING_COMPATIBLE_POSITIVE' for r in rr),certified_violation=sum(r['classification']=='CERTIFIED_VIOLATION' for r in rr),max_exact_residual=str(max(Decimal(r['residual']) for r in rr)),max_bound=str(max(Decimal(r['bound']) for r in rr)),max_positive_ratio_to_bound=str(max([Decimal(r['residual'])/Decimal(r['bound']) for r in rr if Decimal(r['residual'])>0] or [Decimal(0)])))
  boundary=all(x>=0 for x in W) and W[0]==0 and W[-1]>0 and all(x>0 for x in ds) and all(math.isfinite(float(x)) and (x==0 or abs(x)>=D(sys.float_info.min)) for x in [*v,*ds,*m.values()])
  passed=boundary and all(s['certified_violation']==0 for s in summary.values())
 save(d/'numeric-rows-private.json',rows);save(d/'numeric-controls.json',controls);result=dict(stage=401,numeric_passed=passed,status='ROUNDING_AWARE_QUALIFIED' if passed else 'NUMERIC_UNQUALIFIED',controls_passed=True,summary=summary,boundary_passed=boundary,original400_unchanged=True,exact_real_inequalities_all_satisfied=False,source_feasibility_certified=False,model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,scope='Numericalbackwardconsistencyonly;positiveexactstoredinputresidualswithinoperationboundarenotdeclarednonpositive. Subboundphysicalviolationsnotresolved.')
 assert result['CPU_s']<10;save(d/'numeric-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)

"""Frozen pace1.0 squared-speed residual gate; no dynamics or profile repair."""
import datetime,hashlib,json,sys,time
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def prepare(root):
    d=root/'stage400';assert read(d/'result.json')['status']=='QUALIFIED';p398=read(root/'stage398/plan.json');fixed=Path(p398['fixed_plans']['N1'])
    p=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),case='N1',pace=1.,prior_gate='274commands1096ticksqualified',model_tick_cap=0,CPU_cap_s=10,sources={str(f):sha(f) for f in [Path(__file__),fixed,d/'plan.json',d/'result.json',G/'retry/racing258_plan.py']},fixed_plan=str(fixed),definition='Float64W=v_nodes**2;C=min100sqrt(lateral/maxabskappa1e-6)**2 asoriginal258, terminalC=firstcurvatureC butinitialW0=0notperiodic. DriveA=minreartraction,power(v_i);brakeBconstantoriginal. DirectWnext-W-2Ads andW-Wnext-2Bds residuals,anypositiveisstaticunqualified without epsilon/repair. Allnonnegative,initial0,terminalpositive;notphysicalfeasibilitycertificate. Preserveeveryresidualprivateandmax/countpublic.',stop='Anypositive/nonfinite/boundaryresidual ->no branch/factorial. Numericroundingresidual reportedasnumericqualificationgap,notphysicalfailure. No posthoc tolerance.')
    save(d/'profile-plan.json',p);print('Profile static gate registered, no physics.')
def run(root):
    d=root/'stage400';p=read(d/'profile-plan.json');assert not(d/'profile-result.json').exists()
    for f,h in p['sources'].items():assert sha(f)==h
    start,cpu=time.perf_counter(),time.process_time();f=read(Path(p['fixed_plan']));v=np.asarray(f['free_profile']['speed'],np.float64);k=np.abs(np.asarray(f['free_profile']['curvature']));ds=np.asarray(f['free_profile']['ds']);m=f['model'];W=v*v;C0=np.minimum(100.,np.sqrt(m['lateral_accel']/np.maximum(k,1e-6)))**2;C=np.r_[C0,C0[0]];A=np.minimum(m['rear_traction_accel'],80000/(v[:-1]+2.7)/m['effective_mass']);res=dict(nonnegative=-W,upper=W-C,drive=W[1:]-W[:-1]-2*A*ds,brake=W[:-1]-W[1:]-2*m['brake_accel']*ds)
    summary={n:dict(count_positive=int(sum(a>0)),max_residual=float(max(a)),positive_min=float(min(a[a>0])) if any(a>0) else None) for n,a in res.items()};boundary=dict(initial_zero=bool(W[0]==0),terminal_positive=bool(W[-1]>0),all_finite=bool(all(np.isfinite(a).all() for a in [W,C,A,ds])),all_ds_positive=bool(all(ds>0)));passed=all(z['count_positive']==0 for z in summary.values()) and all(boundary.values())
    x=dict(case='N1',passed=passed,status='STATIC_QUALIFIED' if passed else 'STATIC_UNQUALIFIED',residuals=summary,boundary=boundary,source_feasible_envelope_certified=False,new_model_ticks=0,new_native=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,scope='Existingapproximateprofileonly,norepair/fit,strictregisteredfloat64inequalities. Positive smallresidualsarequalificationgaps,notphysicalimpossibility.')
    assert x['CPU_s']<10;save(d/'profile-residuals-private.json',{n:a.tolist() for n,a in res.items()});save(d/'profile-result.json',x);print(json.dumps(x,ensure_ascii=False))
if __name__=='__main__':
    root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)

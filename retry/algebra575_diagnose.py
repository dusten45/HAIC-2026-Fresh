"""575 source0 reconstruction and bounded algebra diagnostics."""
import hashlib,json,signal,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.optimize import linprog
from retry.rounding573 import rounding_box
from retry.causal574_rounding import check
from retry.wide574_math import metric,matrix,SCALE
from retry.wide574_model import load_checkpoint
from retry.geometry571 import component,layout
from retry.path569_design import project_all
import retry.handoff562_model as d

ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/workspace/haic-response574-private')
PRIVATE=Path('/workspace/haic-response575-private')
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Budget:
    def __init__(self):
        self.path=ROOT/'retry/algebra575_cost.json';self.c=read(self.path) if self.path.exists() else dict(CPU_s=5.,wall_s=5.,LP_solves=0,source_ticks=0,actual_actions=0,HOLDOUT=0,SEALED=0)
        self.cpu=time.process_time();self.wall=time.perf_counter();self.records=[]
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(RuntimeError('575_CPU_CAP')))
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('575_WALL_CAP')))
        signal.setitimer(signal.ITIMER_PROF,max(.01,240-self.c['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,360-self.c['wall_s']))
    def solve(self,label,A,b,bounds,objective=None):
        assert self.c['LP_solves']<24
        self.c['LP_solves']+=1;self.save()
        a=time.process_time();w=time.perf_counter();v=linprog(np.zeros(A.shape[1]) if objective is None else objective,A_ub=A,b_ub=b,bounds=bounds,method='highs',options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9,time_limit=10.))
        item=dict(label=label,status=int(v.status),success=bool(v.success),message=v.message,CPU_s=time.process_time()-a,wall_s=time.perf_counter()-w)
        if v.success:item.update(objective=float(v.fun),max_residual=float(max(A@v.x-b)))
        self.records.append(item);self.save();return v
    def save(self):
        out=dict(self.c,CPU_s=self.c['CPU_s']+time.process_time()-self.cpu,wall_s=self.c['wall_s']+time.perf_counter()-self.wall)
        write(self.path,out)
    def close(self):self.save();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)

def reconstruct():
    def forbidden(*a,**k):raise RuntimeError('SOURCE_FORBIDDEN575')
    d.source_tick=d.force_rows=forbidden
    from core.vendor.car_racing import CarRacing
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    owner=SimpleNamespace(static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json')),paths=read(Path('/workspace/haic-response551-private/frozen-paths-private.json')))
    saved=read(OLD/'initial-center-private.json');owner.start=load_checkpoint(read(OLD/'initial-checkpoints-private.json')['35'],owner.static);owner.seed_x=np.asarray(saved['x'])
    center=metric(owner,saved['rows']);center.update(x=owner.seed_x,rows=saved['rows'])
    linear=dict(np.load(OLD/'linear-1-private.npz'));env=read(OLD/'envelope-1-private.json');obs=[]
    for n in range(2):
        v=read(OLD/f'cal-1-{n}-private.json');m=metric(owner,v['rows']);m.update(x=np.asarray(v['x']),rows=v['rows']);obs.append(m)
    summary=read(OLD/'center-1-conditional-matrix-summary-private.json');features=[];seen=set()
    for key in summary['support_keys']:
        i,kind,poly,feature,_=key.split(':');t=(int(i),kind,int(poly),int(feature))
        if t in seen:continue
        seen.add(t);root=d.load_root(dict(center['rows'][t[0]]['root_without_roads'],roads=owner.static['root']['roads']));f=component(root,owner.static,*t[1:]);f['raw']=t[0];features.append(f)
    vl=layout(d.load_root(dict(center['rows'][0]['root_without_roads'],roads=owner.static['root']['roads'])))
    previous=np.asarray([owner.start['progress']]+[v['progress'] for v in center['rows'][:-1]]);idx,*_=project_all(center['P'],previous,owner.paths['candidate']);pts=np.asarray(owner.paths['candidate']['points']);owner.segA=pts[idx];owner.segB=np.roll(pts,-1,axis=0)[idx]
    p,detail=matrix(owner,center,linear,env,features,vl,obs,.05)
    assert detail==summary
    np.savez(PRIVATE/'model-private.npz',A=p['A'],b=p['b'],bounds=p['bounds'],objective=p['objective'],x0=p['x0'],scale=p['scale'],ratio_rows=p['ratio_rows'],**{'path_'+k:v for k,v in p['path'].items()})
    return p,dict(exact_summary_reconstructed=True,rows=len(p['b']),columns=p['A'].shape[1],inputs={str(x):sha(x) for x in [OLD/'initial-center-private.json',OLD/'linear-1-private.npz',OLD/'envelope-1-private.json',OLD/'cal-1-0-private.json',OLD/'cal-1-1-private.json',OLD/'center-1-conditional-matrix-summary-private.json']})

def tube(p,fix_mag=False,rounding=True,numerical=True):
    N=len(p['x0']);G=len(p['groups']);bounds=p['bounds'];q=rounding_box(p['x0'],p['scale'],np.vstack([bounds[:N],bounds[-1:]]));fixed=(bounds[:N,0]==0)&(bounds[:N,1]==0);q[fixed]=0
    inward=bounds.copy();inward[:N,0]+=q;inward[:N,1]-=q
    for k,end in enumerate(p['groups']):
        if np.all(fixed[:end]):inward[N+k]=[0.,0.]
    mag=np.max(abs(inward if fix_mag else bounds),axis=1);eps=np.finfo(float).eps;gamma=(N+G+4)*eps/(1-(N+G+4)*eps)
    margin=abs(p['A'][:,:N])@q if rounding else np.zeros(len(p['b']));numeric=gamma*(abs(p['A'])@mag+abs(p['b'])) if numerical else np.zeros(len(p['b']))
    return dict(A=p['A'],b=p['b']-margin-numeric,bounds=inward,q=q,margin=margin,numerical=numeric)

def static_checks(p,t):
    A,b,bounds=t['A'],t['b'],t['bounds'];fixed=bounds[:,0]==bounds[:,1];free=~fixed;constant=np.all(A[:,free]==0,axis=1);value=A[:,fixed]@bounds[fixed,0];bad=np.flatnonzero(constant&(value>b));lower=np.sum(np.where(A>=0,A*bounds[:,0],A*bounds[:,1]),axis=1);boxbad=np.flatnonzero(lower>b+1e-12)
    N=len(p['x0']);G=len(p['groups']);norm_start=len(p['b'])-4*526-(G-1)-2*N
    return dict(seed=check(p,p['x0']),zero_direction_max_original=float(max(-p['b'])),zero_direction_max_tube=float(max(-b)),constant_rows=int(sum(constant)),negative_constant_rows=[dict(row=int(i),violation=float(value[i]-b[i]),original_rhs=float(p['b'][i]),rounding=float(t['margin'][i]),numerical=float(t['numerical'][i])) for i in bad],single_row_box_contradictions=[dict(row=int(i),gap=float(lower[i]-b[i])) for i in boxbad],norm_start=norm_start,inward_empty=bool(np.any(bounds[:,0]>bounds[:,1])),rounding_max=float(max(t['q'])))

def main():
    PRIVATE.mkdir(exist_ok=True);budget=Budget();out={}
    try:
        p,provenance=reconstruct();out['reconstruction']=provenance;out['branches']={}
        for name,fixed in [('tail',196),('expanded',0)]:
            branch=dict(p,bounds=p['bounds'].copy());branch['bounds'][:fixed]=0.;t=tube(branch);diag=static_checks(branch,t);out['branches'][name]=diag
            c=np.r_[p['objective'],np.full(132,1e-8/132)]
            budget.solve(name+'-original-tube',t['A'],t['b'],t['bounds'],c)
            budget.solve(name+'-original-algebra',p['A'],p['b'],branch['bounds'])
            for label,options in [('no-numerical',dict(numerical=False)),('no-rounding',dict(rounding=False))]:
                u=tube(branch,**options);budget.solve(name+'-'+label,u['A'],u['b'],u['bounds'])
            np.savez(PRIVATE/(name+'-tube-private.npz'),**t)
        out['solves']=budget.records
    finally:
        budget.close();write(ROOT/'retry/algebra575_diagnosis.json',out)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()

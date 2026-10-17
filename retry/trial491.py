"""One registered finite saved-pose regression, zero integration or profiling."""
import time
START=time.perf_counter()
import datetime,hashlib,io,json,os,resource,signal,sys,traceback
from pathlib import Path
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[_v]='1'
import numpy as np
from retry.projection491 import canonical_projection as fixed
from retry.signed417_executor import canonical_projection as original,ExecutorDomainError
from retry.synthetic491 import run as synthetic,plain
from retry.quota489 import Quota

G=Path(__file__).resolve().parents[1];RAW=Path('/tmp/haic-retry-stage491-private');MIB=1024**2
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def ah(x):return hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
def pack(rows):
    s=io.BytesIO();np.savez(s,rows=np.asarray(rows,dtype=np.float64));return s.getvalue()

def run(root):
    root=Path(root);assert not RAW.exists(),'491_ONCE';RAW.mkdir(mode=0o700)
    q=Quota(RAW);q.MAX_FILES=20;q.MAX_BYTES=8*MIB-256*1024;q.FILE_BYTES=MIB;q.TEMP_BYTES=MIB
    resource.setrlimit(resource.RLIMIT_AS,(256*MIB,256*MIB));resource.setrlimit(resource.RLIMIT_CPU,(45,45))
    reg=read(G/'retry/projection491_registration.json');caps=reg['work_caps'];counts={k:0 for k in caps};results=[];gate=None;error=None;status='PREPARING'
    def usage():return dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-START,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    def remaining():return (datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00')-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    def guard(closing=False):
        m=usage()
        if m['CPU_s']>=(44 if closing else 39) or m['wall_s']>=(59 if closing else 52) or m['RSS_bytes']>256*MIB or remaining()<=0:raise RuntimeError('491_RESOURCE_DEADLINE')
        q.diskpreflight()
    def save(name,value,**kwargs):return q.write_json(name,plain(value),**kwargs)
    def charge(k,n=1):
        guard();assert type(n) is int and n>=0 and counts[k]+n<=caps[k],('491_WORK_CAP',k)
        counts[k]+=n;save('stop.json',dict(state='PRECHARGED',counts=counts,resource=usage()),control=True)
    def alarm(*args):raise RuntimeError('491_INTERRUPT')
    for sig in (signal.SIGPROF,signal.SIGALRM,signal.SIGTERM):signal.signal(sig,alarm)
    signal.setitimer(signal.ITIMER_PROF,max(.001,42-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,min(56-(time.perf_counter()-START),remaining())))
    try:
        # Serialization gate precedes every map read/projection and applies to
        # every JSON record, including exception and final-control paths.
        import json as _j
        assert not any(n.startswith(('Box2D','env_wrapper','core.vendor.car_racing')) for n in sys.modules)
        assert _j.loads(_j.dumps(plain(dict(n=np.int64(3),b=np.bool_(True),x=np.array([1.,-0.]))),allow_nan=False))['n']==3
        for rel,h in reg['source_sha256'].items():assert sha(G/rel)==h
        pins_path=root/'stage491-input-pins-private.json';assert sha(pins_path)==reg['input_pins_sha256'];pins=read(pins_path)
        for path,h in pins['files'].items():assert sha(path)==h
        q.diskpreflight(9*MIB);save('plan-private.json',dict(registration_sha256=sha(G/'retry/projection491_registration.json'),source_pins=reg['source_sha256'],caps=caps),exclusive=True)
        gate=synthetic(charge);save('synthetic-private.json',gate,exclusive=True)
        # Original cursor AST prefix through arc, no steering/action/world code.
        import ast
        tree=ast.parse((G/'retry/pace269_run.py').read_text());loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step')
        start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='raw' for t in n.targets));end=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='arc' for t in n.targets));code=compile(ast.Module(body=loop.body[start:end+1],type_ignores=[]),'pace269#491cursor','exec')
        from types import SimpleNamespace
        def call(fn,line,pos,vel,phase):
            try:return fn(line,pos,vel,phase),None
            except ExecutorDomainError as e:return None,str(e)
        def old_terms(line,pos):
            charge('term_audits');edges=np.roll(line,-1,axis=0)-line;ds=np.linalg.norm(edges,axis=1);u=np.clip(np.sum((pos-line)*edges,axis=1)/(ds*ds),0,1);feet=line+u[:,None]*edges
            feet[u==0]=line[u==0];feet[u==1]=np.roll(line,-1,axis=0)[u==1];d=np.sum((pos-feet)**2,axis=1);ix=np.flatnonzero(d==d.min())
            return feet,ix
        for case in pins['cases']:
            if case['format']=='npz':
                with np.load(case['path'],allow_pickle=False) as z:line=z['line']
            else:line=np.asarray(read(case['path'])['line'],dtype=np.float64)
            line.setflags(write=False);linehash=ah(line);n=len(line);assert n==case['stations'] and n<=512
            ds=np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1);edges=np.roll(line,-1,axis=0)-line;sarc=np.r_[0,np.cumsum(ds)];L=float(sarc[-1]);charge('term_audits')
            dot=np.sum(edges*edges,axis=1);denom=ds*ds
            stats=dict(label=case['label'],stations=n,samples=0,old_errors=0,fixed_errors=0,repaired_old_errors=0,remaining_ambiguities=0,old_accepted_fixed_rejected=0,policy_outputs_changed_by_exact_endpoint_identity=0,tie_metadata_only_changes=0,cursor_mismatches_fixed=0,maximum_cursor_arc_gap_m=0.,stale18_cursor_mismatches=0,normsquare_dot_differences=int(np.sum(denom!=dot)),endpoint_quotient_below1=int(np.sum(dot/denom<1)),endpoint_quotient_above1=int(np.sum(dot/denom>1)),seam_phase_checks=0)
            poses=[]
            for i in range(n):
                tangent=edges[i]/ds[i];normal=np.array([tangent[1],-tangent[0]])
                for phase in ('LAUNCH','FIRST_LAP','FINISH_CONFIRM'):poses.append((i,0.,0.,phase))
                for shift in (0.,-3.,-1.,-.25,.25,1.,3.):poses.append((i,.5,shift,'FIRST_LAP'))
            rows=[]
            for offset in range(0,len(poses),32):
                batch=poses[offset:offset+32];charge('original_calls',len(batch));charge('fixed_calls',len(batch))
                cursor_need=sum(1 for _,f,_,phase in batch if f!=0 or phase=='FIRST_LAP');charge('cursor_calls',cursor_need)
                for i,f,shift,phase in batch:
                    tangent=edges[i]/ds[i];normal=np.array([tangent[1],-tangent[0]]);pos=line[i]+f*edges[i]+shift*normal
                    old,oe=call(original,line,pos,tangent,phase);new,ne=call(fixed,line,pos,tangent,phase)
                    stats['samples']+=1;stats['old_errors']+=oe is not None;stats['fixed_errors']+=ne is not None
                    if ne is not None:
                        if oe is None:stats['old_accepted_fixed_rejected']+=1;raise RuntimeError('491_UNEXPECTED_SOURCE_DOMAIN_NARROWING')
                        assert ne==oe=='Distinct_or_nonadjacent_projection_ambiguity';stats['remaining_ambiguities']+=1
                    elif oe is not None:
                        assert oe=='Distinct_or_nonadjacent_projection_ambiguity' and new['u'] in (0.,1.)
                        node=new['index'] if new['u']==0 else (new['index']+1)%n;feet,ix=old_terms(line,pos)
                        assert all(np.array_equal(feet[j],line[node]) for j in ix) and set(ix)<={(node-1)%n,node},'491_TRUE_BRANCH_MERGED'
                        stats['repaired_old_errors']+=1
                    elif old!=new:
                        if {k:v for k,v in old.items() if k!='ties'}=={k:v for k,v in new.items() if k!='ties'}:stats['tie_metadata_only_changes']+=1
                        else:
                            assert new['u'] in (0.,1.);node=new['index'] if new['u']==0 else (new['index']+1)%n
                            feet,ix=old_terms(line,pos);assert all(np.array_equal(feet[j],line[node]) for j in ix) and set(ix)<={(node-1)%n,node},'491_NONENDPOINT_OUTPUT_CHANGED'
                            stats['policy_outputs_changed_by_exact_endpoint_identity']+=1
                    if i==0 and f==0:
                        assert ne is None and new['index']==(0 if phase=='LAUNCH' else n-1) and new['u']==(0 if phase=='LAUNCH' else 1) and new['arc']==(0 if phase=='LAUNCH' else L);stats['seam_phase_checks']+=1
                    cj=-1;gap=0.
                    if f!=0 or phase=='FIRST_LAP':
                        env=SimpleNamespace(unwrapped=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=pos,linearVelocity=tangent))))
                        local=dict(env=env,line=line,ds=ds,sarc=sarc,L=L,index=i);exec(code,dict(np=np),local);cj=int(local['i'])
                        if new is not None:
                            gap=abs((float(local['arc'])-new['arc']+L/2)%L-L/2);stats['cursor_mismatches_fixed']+=cj!=new['index'] or gap>1e-8;stats['maximum_cursor_arc_gap_m']=max(stats['maximum_cursor_arc_gap_m'],gap)
                    rows.append([i,f,shift,('LAUNCH','FIRST_LAP','FINISH_CONFIRM').index(phase),int(oe is not None),int(ne is not None),-1 if old is None else old['index'],-1 if new is None else new['index'],0 if old is None else old['u'],0 if new is None else new['u'],0 if old is None else old['arc'],0 if new is None else new['arc'],cj,gap])
                q.write_bytes(case['label']+'-poses-private.npz',pack(rows));save(case['label']+'-checkpoint-private.json',stats)
            # Stale cursor is a separate diagnostic, not repaired/replaced.
            charge('cursor_calls',n);charge('fixed_calls',n)
            for i in range(n):
                pos=line[i]+.5*edges[i];tangent=edges[i]/ds[i];new,ne=call(fixed,line,pos,tangent,'FIRST_LAP')
                env=SimpleNamespace(unwrapped=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=pos,linearVelocity=tangent))));local=dict(env=env,line=line,ds=ds,sarc=sarc,L=L,index=max(0,i-18));exec(code,dict(np=np),local)
                if new is not None:stats['stale18_cursor_mismatches']+=int(local['i'])!=new['index'] or abs((float(local['arc'])-new['arc']+L/2)%L-L/2)>1e-8
            assert ah(line)==linehash and stats['seam_phase_checks']==3
            save(case['label']+'-result-private.json',stats,exclusive=True);results.append(stats)
        status='FINITE_SOURCE_ENDPOINT_REGRESSION_PASSED'
    except BaseException as e:
        status='TECHNICAL_INCONCLUSIVE';error=type(e).__name__+': '+str(e);save('stop.json',dict(state='STOPPED',error=error,traceback=traceback.format_exc(),counts=counts),control=True)
    finally:
        signal.setitimer(signal.ITIMER_PROF,max(.001,44-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,min(59-(time.perf_counter()-START),remaining())))
        result=dict(stage=491,status=status,error=error,synthetic=gate,cases=results,counts=counts,resource=usage(),closure_receipt_required=True,new_world_reset_step_profile_P4_path_transform_seed=0,known_conditions_only=True,research_remaining=26175,reserve=84000,reserve_used=0,no_followup=True)
        save('result.json',result,control=True);closed=False
        try:
            entries=q.inventory()['files']
            for rec in entries:
                b=Path(rec['path']).read_bytes();assert b==Path(rec['path']).read_bytes() and hashlib.sha256(b).hexdigest()==rec['sha256']
                if rec['path'].endswith('.json'):json.loads(b)
                elif rec['path'].endswith('.npz'):
                    with np.load(io.BytesIO(b),allow_pickle=False) as z:assert np.isfinite(z['rows']).all()
                rec['full_readbacks']=2
            save('retention-private.json',dict(stage=491,files=entries),exclusive=True);guard(closing=True);closed=True
        except BaseException as e:
            status='TECHNICAL_INCONCLUSIVE';error='491_CLOSURE:'+str(e);result.update(status=status,error=error);save('result.json',result,control=True);save('stop.json',dict(error=error,counts=counts),control=True)
        inv=q.inventory();final=usage();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        print(json.dumps(plain(dict(stage=491,status=status,error=error,closure_complete=closed,resource=final,retained_bytes=inv['bytes'],raw_files=inv['file_count'],cases=results,synthetic_passed=gate is not None and gate['passed']))),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]))

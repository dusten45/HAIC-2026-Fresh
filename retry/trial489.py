"""One registered fixed lattice attempt. No simulator/profile/seed API."""
import time
START=time.perf_counter()
import datetime,hashlib,io,json,os,resource,signal,sys,traceback
from pathlib import Path
for _thread_var in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_thread_var]='1'
import numpy as np
from retry.quota489 import Quota
from retry import lattice489 as p,audit489 as a
from retry.synthetic489 import run as synthetic

G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage489-private')
DEADLINE='2026-10-20T10:01:55Z'
OUTSIDE_FILES=12
OUTSIDE_BYTES=256*1024
MIB=1024**2
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def ah(x):return hashlib.sha256(np.asarray(x).tobytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc)
def npbytes(**arrays):
    stream=io.BytesIO();np.savez(stream,**arrays);return stream.getvalue()

class Stop(RuntimeError):pass

def run(root):
    root=Path(root);assert not RAW.exists(),'489_NO_RETRY'
    RAW.mkdir(mode=0o700)
    q=Quota(RAW);q.MAX_FILES=40-OUTSIDE_FILES;q.MAX_BYTES=16*MIB-OUTSIDE_BYTES
    # Stronger virtual-memory limit also prevents crossing RSS256MiB.
    resource.setrlimit(resource.RLIMIT_AS,(256*MIB,256*MIB))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    contract=read(G/'retry/corridor488_contract.json');caps=contract['hard_caps']
    counts={k:0 for k in ('producer_node_checks','producer_edge_checks','producer_triple_checks','independent_audit_node_checks','independent_audit_edge_checks','independent_audit_triple_checks','max_source_full_path_checks','max_nonadjacent_segment_pairs')}
    searches=0;status='PREPARING';error=None;gate=None;geometry=None;compat=None;outcome={};plan=None
    def snapshot():return dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-START,max_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    def check(closing=False):
        x=snapshot()
        if x['CPU_s']>=(59 if closing else 55) or x['wall_s']>=(89 if closing else 82):raise Stop('489_RESOURCE_TIME')
        if x['max_RSS_bytes']>256*MIB:raise Stop('489_RSS')
        if now()>=datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')):raise Stop('489_DEADLINE')
        q.diskpreflight()
    def journal():
        q.write_json('stop.json',dict(stage=489,state='PRECHARGED_OR_LAST_CHECKPOINT',counts=counts.copy(),map_searches=searches,resource=snapshot(),no_retry=True),control=True)
    def charge(key,amount):
        check();assert type(amount) is int and amount>=0
        if counts[key]+amount>caps[key]:raise Stop('489_WORK_CAP:'+key)
        counts[key]+=amount;journal()
    def timeout(*args):raise Stop('489_INTERRUPT_CPU_WALL')
    signal.signal(signal.SIGALRM,timeout);signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGTERM,timeout)
    remaining=lambda:(datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))-now()).total_seconds()
    signal.setitimer(signal.ITIMER_REAL,max(.001,min(86-(time.perf_counter()-START),remaining())))
    signal.setitimer(signal.ITIMER_PROF,max(.001,57-time.process_time()))
    try:
        check();q.diskpreflight(530*MIB-512*MIB)
        assert contract['status']=='DESIGN_ONLY_NO_SEARCH_OR_CONSTRUCTION_AUTHORIZED'
        old=read(root/'stage485/plan-private.json')
        for group in ('sources','protected','original408_preserve'):
            for path,digest in old[group].items():assert sha(path)==digest,path
        assert sha(old['ledger_path'])==old['ledger_sha256']
        ledger=root/'project-effective-budget-v485.json';budget=read(ledger)
        assert budget['research_remaining']==26175 and budget['final_reserved_actions']==84000 and budget['final_reserve_used']==0
        for path,digest in contract['source_sha256'].items():assert sha(G/path)==digest
        snap=Path('/tmp/haic-retry-stage485-private/native/D485-A/initial-full-private.json')
        base=snap.with_name('unsupported-geometry-private.json')
        assert sha(snap)==contract['input']['snapshot_sha256'] and sha(base)==contract['input']['baseline_sha256']
        sources=['trial489.py','lattice489.py','audit489.py','synthetic489.py','quota489.py']
        plan=dict(stage=489,authorization='EXPLICIT_SINGLE_FIXED488_LATTICE_SYNTHETIC_GATE_THEN_ONE_MAP_SEARCH',registered_utc=now().isoformat(),contract_sha256=sha(G/'retry/corridor488_contract.json'),source_pins={str(G/'retry'/n):sha(G/'retry'/n) for n in sources},input_pins={str(snap):sha(snap),str(base):sha(base)},prior_ledger_sha256=sha(ledger),caps=caps,synthetic_cost_in_same_caps=True,stopping_CPU_s=55,stopping_wall_s=82,hard_CPU_s=60,hard_wall_s=90,virtual_memory_cap_bytes=256*MIB,outside_reserved_files=OUTSIDE_FILES,outside_reserved_bytes=OUTSIDE_BYTES,python=sys.version,numpy=np.__version__,deadline_utc=DEADLINE,no_auto_rescue=True)
        q.write_json('plan-private.json',plan,exclusive=True);journal()
        import retry.racing258_plan as original
        def forbidden(*args,**kwargs):raise Stop('489_PROFILE_SOLVER_FORBIDDEN')
        original.profile=forbidden;original.solve=forbidden
        assert not any(v.startswith(('Box2D','env_wrapper','core.vendor.car_racing')) for v in sys.modules)
        # No saved geometry is constructed before this synthetic gate passes.
        gate=synthetic(charge);q.write_json('synthetic-private.json',dict(**gate,resource=snapshot()),exclusive=True)
        if gate['representative_321_layers_CPU_s']>55-time.process_time():raise Stop('489_SYNTHETIC_COST_CANNOT_FIT_REMAINING_CAP')
        q.write_bytes('binary-fixture-private.bin',b'489\x00\xff',exclusive=True)
        assert (RAW/'binary-fixture-private.bin').read_bytes()==b'489\x00\xff'
        check()
        # Hard-bounded operations, in vectorized per-layer batches. Synthetic
        # timings plus a strict stop leave no authority to enlarge any cap.
        q.write_json('map-opening-private.json',dict(before_map_construction=True,synthetic=gate,counts=counts.copy(),resource=snapshot(),projected_full_node_checks=321*21,projected_edge_checks=321*21**2,projected_triple_checks=321*21**3,actual_cost_unknown_hard_stop=True),exclusive=True)
        charge('producer_node_checks',321*21)
        source=read(snap)['physical'];center,normal,s,L,obs,radii,t=p.source_geometry(source)
        n=len(center);k=21;assert n==321 and len(obs)==6 and n<=512
        assert np.all(np.isfinite(center)) and np.all(np.diff(s)>0) and s[-1]<L
        qs,nodes,unique=p.points(center,normal,s,L,t);tube=p.tube(center,nodes,s,L);eligible=unique&tube
        charge('independent_audit_node_checks',n*k)
        independent=a.reconstruct(source)
        for x,y in zip((center,normal,s,L,obs,radii,t),independent):assert np.asarray(x).tobytes()==np.asarray(y).tobytes(),'489_SOURCE_GEOMETRY_DISAGREEMENT'
        # Recreate point arithmetic, canonical aliases and original offsets
        # without calling producer construction or consuming its masks.
        aq=np.asarray([0.,.5,-.5,1.,-1.,1.5,-1.5,2.,-2.,2.5,-2.5,3.,-3.,3.5,-3.5,4.,-4.,4.5,-4.5,p.B,-p.B])
        ap=center[:,None,:]+normal[:,None,:]*(t[:,None]*aq[None,:])[:,:,None]
        for i in (0,1,n-1):ap[i,:,:]=center[i]
        assert np.array_equal(aq,qs) and ap.tobytes()==nodes.tobytes(),'489_POINT_BYTES_DISAGREEMENT'
        au=np.zeros((n,k),bool)
        for i in range(n):
            for j in range(k):au[i,j]=not any(ap[i,j].tobytes()==ap[i,h].tobytes() for h in range(j))
        at=a.tube_eligible(independent[0],ap,independent[2],independent[3],p.B)
        assert np.array_equal(au,unique) and np.array_equal(at,tube),'489_NODE_CERTIFICATE_DISAGREEMENT'
        ae=au&at
        q.write_bytes('nodes-private.npz',npbytes(center=center,normal=normal,arc=s,L=np.asarray(L),obstacles=obs,radii=radii,taper=t,q=qs,points=nodes,unique=unique,tube=tube,eligible=eligible),exclusive=True)
        labels=[p.F.from_float(float(v)) for v in s]+[p.F.from_float(float(L))]
        taus=[p.taper(v,labels[-1]) for v in labels]
        minima=[min(taus[i],taus[i+1]) for i in range(n)]
        bounds=[(p.F.from_float(float(p.B))*min(minima[(i-1)%n],minima[i]))**2 for i in range(n)]
        q.write_json('rational-witness-private.json',dict(bound_squared_num_den=[[str(v.numerator),str(v.denominator)] for v in bounds],displacement_witness='Exact stored float64 points and centers in nodes-private.npz. Convert each coordinate separately via Fraction.from_float before subtraction; eligibility mask records every squared-norm comparison.',nodes_sha256=sha(RAW/'nodes-private.npz')),exclusive=True)
        edges=np.zeros((n,k,k),bool);margins=np.zeros((n,k,k),np.float64)
        for j in range(n):
            charge('producer_edge_checks',k*k)
            valid,margin=p.edge(nodes[j],nodes[(j+1)%n],obs,radii)
            edges[j]=valid&eligible[j,:,None]&eligible[(j+1)%n,None,:];margins[j]=margin
        q.write_bytes('edges-private.npz',npbytes(valid=edges,min_margin=margins),exclusive=True)
        # Charge the one map invocation before any DP state is advanced.
        check();searches=1;journal()
        parents=np.full((n,k,k),255,np.uint8);reach=np.zeros((n,k,k),bool)
        reach[1,0,0]=edges[0,0,0]
        blocks=[];carry=np.empty(0,np.uint8);root_triple=None;last_triple=None
        for j in range(n):
            charge('producer_triple_checks',k**3)
            z=p.triple(nodes[(j-1)%n],nodes[j],nodes[(j+1)%n])
            z &= eligible[(j-1)%n,:,None,None]&eligible[j,None,:,None]&eligible[(j+1)%n,None,None,:]
            bits=np.concatenate((carry,z.ravel().astype(np.uint8)));full=len(bits)//8*8
            blocks.append(np.packbits(bits[:full]).tobytes());carry=bits[full:]
            if j==0:root_triple=z.copy()
            elif j==n-1:last_triple=z.copy()
            else:reach[j+1],parents[j+1]=p.advance(reach[j],z,edges[j])
        if len(carry):blocks.append(np.packbits(carry).tobytes())
        packed=b''.join(blocks);assert len(packed)==(n*k**3+7)//8
        q.write_bytes('triples-private.bin',packed,exclusive=True)
        goal=p.choose(reach[-1],edges[-1],last_triple,root_triple)
        q.write_bytes('dp-private.npz',npbytes(reachable=reach,parents=parents,goal=np.array([] if goal is None else goal,dtype=np.uint8)),exclusive=True)
        # Checker recomputes every local predicate, and its own DP parents and
        # canonical terminal choice. It never selects a second candidate.
        ar=np.zeros((k,k),bool);ar[0,0]=edges[0,0,0];audit_root=None;audit_last=None
        for j in range(n):
            charge('independent_audit_edge_checks',k*k)
            ev,em=a.edges(ap[j],ap[(j+1)%n],obs,radii);ev &= ae[j,:,None]&ae[(j+1)%n,None,:]
            assert np.array_equal(ev,edges[j]) and np.array_equal(em,margins[j]),'489_EDGE_SOURCE_DISAGREEMENT'
            charge('independent_audit_triple_checks',k**3)
            av=a.triples(ap[(j-1)%n],ap[j],ap[(j+1)%n],p.TARGET)
            av &= ae[(j-1)%n,:,None,None]&ae[j,None,:,None]&ae[(j+1)%n,None,None,:]
            start=j*k**3;stop=(j+1)*k**3
            stored=np.unpackbits(np.frombuffer(packed[start//8:(stop+7)//8],dtype=np.uint8))[start%8:start%8+k**3].reshape(k,k,k).astype(bool)
            assert np.array_equal(av,stored),'489_TRIPLE_SOURCE_DISAGREEMENT'
            if j==0:audit_root=av.copy()
            elif j==n-1:audit_last=av.copy()
            else:
                next_reach=np.zeros((k,k),bool);next_parents=np.full((k,k),255,np.uint8)
                for b in range(k):
                    options=ar[:,b,None]&av[:,b,:]&ev[b,None,:]
                    for c in np.flatnonzero(options.any(axis=0)):
                        next_reach[b,c]=True;next_parents[b,c]=np.flatnonzero(options[:,c])[0]
                ar=next_reach
                assert np.array_equal(ar,reach[j+1]) and np.array_equal(next_parents,parents[j+1]),'489_DP_DISAGREEMENT'
        goals=[]
        for b,c in np.argwhere(ar):
            if edges[-1,c,0] and audit_last[b,c,0] and audit_root[c,0,0]:goals.append((int(b),int(c)))
        ag=None if not goals else min(goals);assert ag==goal,'489_TERMINAL_DISAGREEMENT'
        audit=dict(passed=True,all_nodes_edges_triples_and_DP_checked=True,goal_present=goal is not None,counts=counts.copy(),packed_sha256=hashlib.sha256(packed).hexdigest(),resource=snapshot())
        q.write_json('audit-private.json',audit,exclusive=True)
        if goal is None:
            status='FIXED_CONSERVATIVE_LATTICE_NO_GOAL'
        else:
            ranks=p.reconstruct(parents,goal);line=nodes[np.arange(n),ranks];offset=t*qs[ranks]
            assert np.array_equal(ranks[:2],[0,0]) and ranks[-1]==0
            q.write_bytes('candidate-private.npz',npbytes(ranks=ranks,line=line,offset=offset),exclusive=True)
            charge('max_source_full_path_checks',1)
            from retry.racing258_plan import obstacle_clearance,curvature
            clear=obstacle_clearance(line,obs,radii);curv=curvature(line)
            V=float(np.sum(np.maximum(-clear,0)**2)+100*np.sum(np.maximum(abs(curv)-p.TARGET,0)**2)+np.sum(np.maximum(abs(offset)-p.B,0)**2))
            assert clear.min()>=-1e-6 and V<=1e-8 and np.all(tube[np.arange(n),ranks]),'489_FINAL_SOURCE_GATE_DISAGREEMENT'
            geometry=dict(qualified=True,min_clearance_m=float(clear.min()),violation=V,max_abs_curvature=float(abs(curv).max()),source_target=float(p.TARGET),path_sha256=ah(line),tube_certificate=True,original_proxy_only=True)
            charge('max_nonadjacent_segment_pairs',n*(n-1)//2)
            compat=p.compatibility(line)
            q.write_json('certificate-private.json',dict(geometry=geometry,compatibility=compat,clearance=clear.tolist(),curvature=curv.tolist()),exclusive=True)
            status='GEOMETRY_CANDIDATE_ONLY' if compat['schema'] else 'GEOMETRY_CANDIDATE_EXECUTOR_SCHEMA_UNQUALIFIED'
        check()
    except BaseException as e:
        status='TECHNICAL_INCONCLUSIVE';error=type(e).__name__+': '+str(e)
        q.write_json('stop.json',dict(stage=489,state='STOPPED',error=error,traceback=traceback.format_exc(),counts=counts,map_searches=searches,no_retry=True,resource=snapshot()),control=True)
    finally:
        # Remaining hard-limit margin is reserved for stop/result/readback.
        signal.setitimer(signal.ITIMER_PROF,max(.001,59-time.process_time()))
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(89-(time.perf_counter()-START),remaining())))
        result=dict(stage=489,status=status,error=error,synthetic=gate,map_searches=searches,counts=counts,geometry=geometry,executor_compatibility=compat,resource=snapshot(),new_profiles=0,new_P4=0,new_actual=0,new_resets=0,new_steps=0,new_worlds=0,new_seed=0,second_condition_used=False,research_remaining=26175,reserve=84000,reserve_used=0,no_followup=True,finite_failure_scope='Only fixed conservative488 local-predicate lattice on exposed first485; no continuous/original-tolerance/physical impossibility claim.')
        q.write_json('result.json',result,control=True)
        inventory=q.inventory()
        for rec in inventory['files']:
            path=Path(rec['path']);data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==rec['sha256'] and data==path.read_bytes()
            if path.suffix=='.json':json.loads(data)
            elif path.suffix=='.npz':
                with np.load(io.BytesIO(data),allow_pickle=False) as z:
                    for key in z.files:assert np.isfinite(z[key]).all()
            rec['full_readbacks']=2
        q.write_json('retention-private.json',dict(stage=489,files=inventory['files'],resource=snapshot()),exclusive=True)
        check(closing=True)
        retained=q.inventory()['bytes']
        final=snapshot();assert final['CPU_s']<60 and final['wall_s']<90
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        print(json.dumps(dict(stage=489,status=status,error=error,map_searches=searches,synthetic_passed=gate is not None and gate['passed'],geometry=geometry,executor_compatibility=compat,resource=final,retained_bytes=retained)),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]))

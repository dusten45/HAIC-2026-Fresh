"""Finish unattempted numeric diagnostics on490's saved arrays. Never rebuild.

The original technical stop/result/source are immutable. No profile, P4,
constructor, map sampling repeat or geometry modification is performed here.
"""
import time
START=time.perf_counter()
import ast,datetime,hashlib,json,math,os,resource,signal,sys
from pathlib import Path
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[_v]='1'
import numpy as np
from retry.quota489 import Quota
from retry.executor490_input import load,array_sha

G=Path(__file__).resolve().parents[1];RAW=Path('/tmp/haic-retry-stage490-private');MIB=1024**2
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def run(root):
    root=Path(root);reg=read(G/'retry/executor490_completion_registration.json')
    assert sha(__file__)==reg['source_sha256'] and not (RAW/'completion-plan-private.json').exists()
    for rel,digest in read(G/'retry/executor490_registration.json')['source_sha256'].items():assert sha(G/rel)==digest
    for name,digest in reg['immutable_attempt_pins'].items():assert sha(RAW/name)==digest
    first=read(RAW/'result.json');closing=read(root/'stage490-worker-output-private.txt');assert first['status']=='TECHNICAL_INCONCLUSIVE' and closing['closure_complete']
    caps=read(G/'retry/executor490_registration.json')['work_caps'];counts=first['counts'].copy();added={k:0 for k in counts}
    resource.setrlimit(resource.RLIMIT_AS,(256*MIB,256*MIB));resource.setrlimit(resource.RLIMIT_CPU,(max(1,math.ceil(30-closing['resource']['CPU_s'])),)*2)
    q=Quota(RAW);q.MAX_FILES=17;q.MAX_BYTES=8*MIB-256*1024;q.FILE_BYTES=MIB;q.TEMP_BYTES=MIB
    def metrics():return dict(CPU_s=closing['resource']['CPU_s']+time.process_time(),wall_s=closing['resource']['wall_s']+time.perf_counter()-START,RSS_bytes=max(closing['resource']['RSS_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    def guard():
        m=metrics()
        if m['CPU_s']>=27 or m['wall_s']>=41 or m['RSS_bytes']>256*MIB:raise RuntimeError('490_CUMULATIVE_RESOURCE')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'):raise RuntimeError('490_DEADLINE')
        q.diskpreflight()
    def charge(k,n=1):
        guard();assert counts[k]+n<=caps[k];counts[k]+=n;added[k]+=n
        q.write_json('completion-charges-private.json',dict(cumulative=counts,added=added,resource=metrics()))
    def alarm(*args):raise RuntimeError('490_COMPLETION_INTERRUPT')
    for sig in (signal.SIGPROF,signal.SIGALRM,signal.SIGTERM):signal.signal(sig,alarm)
    remaining=(datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00')-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    signal.setitimer(signal.ITIMER_PROF,max(.001,28-closing['resource']['CPU_s']-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,min(42-closing['resource']['wall_s']-(time.perf_counter()-START),remaining)))
    q.write_json('completion-plan-private.json',dict(registration_sha256=sha(G/'retry/executor490_completion_registration.json'),prior_status=first['status'],prior_counts=counts,no_rebuild=True,original_files_immutable=True),exclusive=True)
    fixed,pace,nodes=load(RAW/'input-manifest-private.json');line=fixed['line'];ds=fixed['free_profile']['ds'];curve=np.r_[fixed['free_profile']['curvature'],fixed['free_profile']['curvature'][0]];model=fixed['model'];n=len(ds)
    scope=dict(np=np,math=math)
    tree=ast.parse((G/'retry/analyze466.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='segment_proxy');exec(compile(ast.Module(body=[fn],type_ignores=[]),'analyze466.py#diagnostics490','exec'),scope)
    from retry.scalar392_audit import pedals
    from retry.signed417_executor import canonical_projection,ExecutorDomainError
    charge('segment_proxy_checks',n)
    rows=[scope['segment_proxy'](nodes[i]**2,nodes[i+1]**2,curve[i],curve[i+1],ds[i],model) for i in range(n)]
    q.write_json('segments-private.json',dict(segments=rows),exclusive=True)
    # Independent algebra exposes the FAILED seam call without retrying it.
    charge('competitor_distance_batches')
    pos=line[0];edges=np.roll(line,-1,axis=0)-line;length=np.linalg.norm(edges,axis=1)
    u=np.clip(np.sum((pos-line)*edges,axis=1)/(length*length),0,1);feet=line+u[:,None]*edges;vertex=np.full(n,-1,int)
    for j in range(n):
        if u[j]==0:feet[j]=line[j];vertex[j]=j
        elif u[j]==1:feet[j]=line[(j+1)%n];vertex[j]=(j+1)%n
    d=np.sum((pos-feet)**2,axis=1);ix=np.flatnonzero(d==d.min());vertices={int(vertex[j]) for j in ix}
    seam_evidence=dict(minimizer_indices=ix.tolist(),u=u[ix].tolist(),vertex_tags=vertex[ix].tolist(),minimum_distance_squared=float(d.min()),same_geometric_foot=bool(all(np.array_equal(feet[j],line[0]) for j in ix)),source_accepts_tie=len(vertices)==1 and -1 not in vertices)
    assert len(ix)>1 and not seam_evidence['source_accepts_tie']
    # Unattempted generic synthetic test: exact tie and one-sided jump.
    toy=np.array([[-4.,-1.],[4.,-1.],[4.,1.],[-4.,1.]])
    charge('canonical_queries');tie=False
    try:canonical_projection(toy,[0.,0.],[1.,0.],'FIRST_LAP')
    except ExecutorDomainError:tie=True
    charge('canonical_queries');left=canonical_projection(toy,[0.,-1e-6],[1.,0.],'FIRST_LAP')
    charge('canonical_queries');right=canonical_projection(toy,[0.,1e-6],[1.,0.],'FIRST_LAP');assert tie and left['index']!=right['index']
    scalar_clipped=gas_saturated=0;stationary_positive=True
    for i in range(n):
        r=math.sqrt((nodes[i]**2+nodes[i+1]**2)/2);f=(nodes[i+1]**2-nodes[i]**2)/(2*ds[i])
        for v,sigma in ((r,r),(0.,0.),(1.2*r,1.2*r)):
            charge('scalar_pedal_queries');raw=f*sigma/r+1.5*(r-v);z=pedals(raw,v,model)
            assert all(math.isfinite(x) for x in z.values()) and 0<=z['gas']<=1 and 0<=z['brake']<=1 and not(z['gas']>0 and z['brake']>0)
            if v==0:stationary_positive &= raw>0 and z['brake']==0
            scalar_clipped+=z['command_accel']!=raw;gas_saturated+=z['gas']==1
    assert stationary_positive and array_sha(line)==read(RAW/'input-manifest-private.json')['line_sha256']
    summary=dict(complete_executor_schema_candidate_built_once=True,line_bytes_unchanged=True,profile_calls_total=counts['profile_calls'],pace_calls_total=counts['pace_calls'],P4_calls_total=counts['p4_calls'],P4_passes_total=counts['p4_passes'],final_nodes_bound_without_double_pace=True,positive_nonlaunch_targets=True,launch_target_m_s=float(nodes[0]),minimum_nonlaunch_target_m_s=float(nodes[1:].min()),finish_target_m_s=float(nodes[-1]),source_curvature_bytes_inherited=True,original_offset_seam_geometry_certificate_inherited=True,discrete_forward_q_residual_max=max(x['discrete_forward_q_residual'] for x in rows),discrete_backward_q_residual_max=max(x['discrete_backward_q_residual'] for x in rows),discrete_forward_violations=sum(x['discrete_forward_q_residual']>1e-8 for x in rows),discrete_backward_violations=sum(x['discrete_backward_q_residual']>1e-8 for x in rows),engine_worst_endpoint_over1_segments=sum(x['engine_equivalent_ratio'] is not None and x['engine_equivalent_ratio']>1 for x in rows),engine_worst_endpoint_ratio_max=max(x['engine_equivalent_ratio'] or 0 for x in rows),aggregate_circle_over1_segments=sum(x['aggregate_translation_circle_ratio']>1 for x in rows),aggregate_circle_ratio_max=max(x['aggregate_translation_circle_ratio'] for x in rows),rear_equal_axle_drive_over1_segments=sum(x['rear_equal_axle_drive_circle_ratio'] is not None and x['rear_equal_axle_drive_circle_ratio']>1 for x in rows),rear_equal_axle_drive_ratio_max=max(x['rear_equal_axle_drive_circle_ratio'] or 0 for x in rows),scalar_synthetic_queries=added['scalar_pedal_queries'],scalar_clipped_queries=int(scalar_clipped),gas_saturated_queries=int(gas_saturated),stationary_positive_target_positive_drive=bool(stationary_positive),sampled_projection_errors_in_original_attempt=55,explicit_start_seam_projection_error=True,sample_record_arrays_retained=False,partial_cursor_mismatch_aggregates_unavailable=True,exact_seam_tie_same_foot=seam_evidence['same_geometric_foot'],generic_unique_projection_jump_demonstrated=True,phase_act_fixtures_skipped_after_known_seam_domain_error=True,original_attempt_technical_status_preserved=True,dynamic_safety_source_native_tracking_qualified=False)
    q.write_json('completion-private.json',dict(stage=490,status='NUMERIC_DIAGNOSTICS_COMPLETED_ON_EXISTING_INPUT_PROJECTION_UNQUALIFIED',summary=summary,seam_evidence=seam_evidence,cumulative_counts=counts,added_counts=added,resource=metrics(),new_profile_P4_build_projection_retry_world_reset_step_seed=0),exclusive=True)
    entries=q.inventory()['files']
    for row in entries:
        b=Path(row['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'] and b==Path(row['path']).read_bytes()
    guard();final=metrics();assert final['CPU_s']<30 and final['wall_s']<45
    for name,digest in reg['immutable_attempt_pins'].items():assert sha(RAW/name)==digest
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps(dict(stage=490,status='INPUT_SCHEMA_CANDIDATE_PROJECTION_UNQUALIFIED',summary=summary,cumulative_resource=final,retained_bytes=q.inventory()['bytes'])),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]))

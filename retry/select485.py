"""One-use, two-slot identity-only selector. Run in a physics-free process."""
import time
START=time.perf_counter()
import datetime,hashlib,importlib.util,json,os,sys,signal
from pathlib import Path
import numpy as np
from retry.identity_only_split import EXCLUSION_KEYS,array_sha,source_only_guard
from retry.quota485 import RunQuota

HELPER_SHA='4dcfc76d824ab8340e838e944f086c879ed0d0eb7630701fa9f7e069be393368'
PREFIX_SHA='fc986d73d303969458aa3e26872e6adf655eafc10109826d1c15b8eb468714ae'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())

def verify_live_identity(case,env):
    raw=env.env.unwrapped
    road=array_sha(np.asarray(raw.track,dtype='<f8'))
    physical=array_sha([[*b.position,b.fixtures[0].shape.radius] for b in raw.obstacles])
    if road!=case['road_geometry_sha256'] or physical!=case['expected_physical_obstacles_sha256']:
        raise RuntimeError('485_NATIVE_IDENTITY_NOT_REGISTERED')
    return dict(road_geometry_sha256=road,physical_obstacles_sha256=physical)

def select(root):
    cpu=0.;wall=START;root=Path(root);d=root/'stage485'
    p=read(d/'plan-private.json');source_only_guard()
    assert p['static_passed'] and p['authorized_to_select'] and p['contract_sha256']==sha(p['contract_path'])
    assert sha(p['identity_audit_path'])==p['identity_audit_sha256']
    assert sha(p['exclusions_path'])==p['exclusions_sha256']
    audit=read(p['identity_audit_path']);assert audit['passed'] is True and audit['status']=='RECORDED_IDENTITY_COMPLETENESS_PASS'
    artifact=audit['artifacts']['exclusions-private.json']
    assert artifact['path']==p['exclusions_path'] and artifact['sha256']==p['exclusions_sha256']
    sources_artifact=audit['artifacts']['sources-private.json'];assert sha(sources_artifact['path'])==sources_artifact['sha256']
    for path,h in read(sources_artifact['path']).items():assert sha(path)==h

    for path,h in p['sources'].items():assert sha(path)==h
    deadline=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
    def guard():
        assert datetime.datetime.now(datetime.timezone.utc)<deadline
        assert time.process_time()-cpu<30 and time.perf_counter()-wall<60
    guard()
    def timeout(*_):raise RuntimeError('485_SELECTION_CPU30_WALL60')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout)
    signal.setitimer(signal.ITIMER_PROF,max(.001,30-(time.process_time()-cpu)))
    signal.setitimer(signal.ITIMER_REAL,max(.001,min(60-(time.perf_counter()-wall),(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
    helper=root/'stage16/source_only_geometry.py';assert sha(helper)==HELPER_SHA
    spec=importlib.util.spec_from_file_location('geometry485_identity',helper);geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
    assert geometry.EXTRACTED_PREFIX_AST_SHA256==PREFIX_SHA
    from core.track_variables import _place_obstacles,OBSTACLE_RNG_STREAM
    source_only_guard()
    q=RunQuota(p['model_dir'],p['native_dir'],workspace_paths=[*[f for f in d.rglob('*') if f.is_file()],*p.get('workspace_existing_paths',[])])
    paths=[d/n for n in ('draw-private.json','split-private.json','selection-private.json')]
    for path in paths:assert not path.exists();q.register_workspace(path)
    exclusion=read(p['exclusions_path']);excluded={k:{tuple(v) if isinstance(v,list) else v for v in exclusion[k]} for k in EXCLUSION_KEYS}
    words={s for v in excluded['excluded_parent_entropy_vectors'] for s in v}
    # No rejection or retry of the parent entropy draw. Each slot can replace
    # only an identity collision and every attempted seed remains recorded.
    raw=os.urandom(8);seeds=[int.from_bytes(raw[i:i+4],'little') for i in (0,4)]
    q.save_receipt(paths[0],dict(stage=485,entropy_hex=raw.hex(),parent_entropy_vector=seeds,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    cases=[];collisions=[]
    for i,label in enumerate((1,2)):
        seed=seeds[i]
        for attempt in range(17):
            guard();reasons=[]
            if seed in excluded['excluded_seeds'] or seed in words:reasons=['seed_or_parent_word_identity']
            if not reasons:
                track,tries=geometry.track_for_seed(seed);road=geometry.geometry_hash(track)
                obs=_place_obstacles(label,seed,track,40/6)
                values=np.asarray([[*o.position,o.radius] for o in obs],dtype='<f8');assert values.shape==(6,3) and np.isfinite(values).all()
                spec_hash=array_sha(values);physical=array_sha(values.astype(np.float32).astype(float));lineage=(label,seed,int(OBSTACLE_RNG_STREAM))
                for key,value in [('excluded_road_geometry_sha256',road),('excluded_obstacle_spec_sha256',spec_hash),('excluded_physical_obstacles_sha256',physical),('excluded_obstacle_rng_entropy',lineage)]:
                    if value in excluded[key]:reasons.append(key)
            if not reasons:break
            collisions.append(dict(slot=i,rejected_seed=seed,reasons=reasons,attempt=attempt))
            q.save(paths[2],dict(status='IDENTITY_COLLISION',collisions=collisions))
            assert attempt<16,'485_COLLISION_CAP'
            seed=int.from_bytes(os.urandom(4),'little')
        case=dict(slot='D485-'+('A' if i==0 else 'B'),design_slot='D484-'+('A' if i==0 else 'B'),split='DEV',seed=seed,track_id=label,road_geometry_sha256=road,obstacle_spec_sha256=spec_hash,expected_physical_obstacles_sha256=physical,obstacle_rng_entropy=list(lineage),track_attempts=tries,arm_order=['control','variant'] if i==0 else ['variant','control'])
        case['case_identity_digest']=hashlib.sha256(json.dumps(case,sort_keys=True,separators=(',',':')).encode()).hexdigest();cases.append(case)
        for key,value in [('excluded_seeds',seed),('excluded_road_geometry_sha256',road),('excluded_obstacle_spec_sha256',spec_hash),('excluded_physical_obstacles_sha256',physical),('excluded_obstacle_rng_entropy',lineage)]:excluded[key].add(value)
    guard();source_only_guard()
    q.save_receipt(paths[1],dict(stage=485,cases=cases,draw_sha256=sha(paths[0]),exclusions_sha256=p['exclusions_sha256'],no_performance_filter=True,protected_performance_reads=0))
    q.save(paths[2],dict(stage=485,status='TWO_DEV_FROZEN_NOT_EXECUTED',cases=2,collisions=collisions,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_worlds=0,new_native=0,new_resets=0))
    print(json.dumps(dict(stage=485,phase='IDENTITIES_FROZEN',cases=2,new_worlds=0,new_native=0,new_resets=0)),flush=True)

if __name__=='__main__':select(sys.argv[1])

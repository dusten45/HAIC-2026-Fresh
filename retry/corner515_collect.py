"""One approved DEV reset, no wrapper action; exact static map/current inputs."""
import datetime,hashlib,json,math,time,signal
from dataclasses import asdict
from pathlib import Path
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake510_common import native_roads,track_boundary
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response515-private')

def run():
    t=time.perf_counter();cpu=time.process_time();c=json.loads((G/'retry/corner515_collection_contract.json').read_text());case=json.loads((D/'approved-case-private.json').read_text())
    if (D/'COLLECTION_STARTED.json').exists():raise RuntimeError('NO_COLLECTION_RETRY')
    def save(path,x):
        data=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
        if sum(p.stat().st_size for p in D.iterdir())+len(data)>64*1024**2:raise RuntimeError('STORAGE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
    def guard(*a):
        if time.process_time()-cpu>10 or time.perf_counter()-t>15:raise RuntimeError('COLLECTION_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,15)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==c['case_private_sha256']
    from core.vendor.car_racing import CarRacing,TRACK_WIDTH
    from Box2D.b2 import polygonRadius
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from retry.corner515_control import make_path
    save(D/'COLLECTION_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/corner515_collection_contract.json').read_bytes()).hexdigest()))
    raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper']);step=raw.step;reset=raw.reset;counts=dict(worlds=1,resets=0,actions=0,raw_ticks=0,closed=0)
    def limited_reset(**kw):
        guard()
        if counts['resets']>=1:raise RuntimeError('RESET_CAP')
        counts['resets']+=1;save(D/'collection-reset-charge.json',dict(counts));return reset(**kw)
    def limited_step(a):
        guard()
        if counts['raw_ticks']>=51:raise RuntimeError('COLLECTION_RAW_CAP')
        counts['raw_ticks']+=1
        return step(a)
    raw.reset=limited_reset;raw.step=limited_step;identity=False;status='COLLECTION_FAILED'
    try:
        obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});guard();assert counts['raw_ticks']==51
        geometry=sha(raw.track);obstacles=[[list(o.position),o.radius] for o in raw.track_variables.obstacles]
        assert geometry==case['old_episode']['geometry_sha256_diagnostic_only'] and sha(obstacles)==case['old_episode']['obstacles_sha256_diagnostic_only']
        partial=sha(dict(geometry=geometry,obstacles=sha(obstacles),obs=hashlib.sha256(obs.tobytes()).hexdigest(),body=asdict(observed_state(raw.car)),position=com(raw.car,True),angle=raw.car.hull.angle,time=raw.t,RNG=raw.np_random.bit_generator.state))
        assert partial==json.loads(Path('/workspace/haic-response510-private/native-initial-reference.json').read_text())['identity']
        identity=True;roads=native_roads(raw.road);edge=track_boundary(raw.track,TRACK_WIDTH);root=context(raw.car,raw.road,[0,0,0],skin=2*float(polygonRadius))
        path=make_path(edge,root.center)
        full=sha(dict(root=asdict(root),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
        save(D/'collected-map-state-private.json',dict(root=asdict(root),track=raw.track,roads=roads,boundary=edge,obstacles=obstacles,path=path,identity=partial,full_identity=full,RNG=raw.np_random.bit_generator.state,observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest()))
        status='COLLECTION_IDENTITY_PASS'
    finally:
        env.close();assert raw.world.bodyCount==raw.world.jointCount==0;counts['closed']=1
        save(D/'collection-close-private.json',dict(counts))
    result=dict(status=status,identity_verified=identity,counts=counts,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,research_remaining=25804,reserve=84000,reserve_used=0,scope='Same verified DEV reset only; exact static obstacles/track and initial model input. No wrapper action or new seed.')
    guard();save(G/'retry/corner515_collection_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()

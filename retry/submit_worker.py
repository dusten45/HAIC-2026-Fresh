"""External evaluation worker; never included in the participant ZIP."""
import time
START=time.perf_counter()
import importlib.util
import json
import resource
import sys

# A conservative local address-space bound in addition to reported peak RSS.
resource.setrlimit(resource.RLIMIT_AS,(1024*1024**2,1024*1024**2))
import numpy as np
sys.path.insert(0,sys.argv[1].rsplit('/',1)[0])
spec=importlib.util.spec_from_file_location('agent',sys.argv[1])
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
agent=module.Agent()
research_model_limit=None
research_model_ticks=0
if len(sys.argv)>2 and hasattr(agent,'counter'):
    research_model_limit=min(200000,max(0,int(sys.argv[2])))
    agent.counter.limit=research_model_limit
recorder=None
if len(sys.argv)>3:
    from runtime598_diagnostic import Recorder
    snapshot_calls=tuple(int(v) for v in sys.argv[5].split(',') if v) if len(sys.argv)>5 else ()
    recorder=Recorder(agent,sys.argv[3],target=None if len(sys.argv)>4 and sys.argv[4]=='all' else 36,
        snapshot_calls=snapshot_calls,save_observations=len(sys.argv)>6 and sys.argv[6]=='observations')


def send(value):
    sys.stdout.write(json.dumps(value,allow_nan=False)+'\n')
    sys.stdout.flush()


send(dict(ready=True,startup_wall_s=time.perf_counter()-START,
          max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
while True:
    command=sys.stdin.buffer.read(1)
    if not command or command==b'Q':break
    needed=4*84*84*4;data=b''
    while len(data)<needed:
        part=sys.stdin.buffer.read(needed-len(data))
        if not part:raise EOFError('incomplete observation')
        data+=part
    observation=np.frombuffer(data,dtype=np.float32).reshape(4,84,84)
    begin=time.perf_counter();cpu=time.process_time()
    episode_before=getattr(agent,'counter',[0])[0]
    try:
        if command==b'R':
            agent.reset(observation)
            if research_model_limit is not None:
                remaining=max(0,research_model_limit-research_model_ticks)
                agent.counter.limit=min(200000,agent.counter[0]+remaining)
            result=dict(reset=True)
        elif command==b'A':
            prediction_before=getattr(agent,'predicted_hull_speed',None)
            if recorder is not None:recorder.before_action(observation)
            action=np.asarray(agent.act(observation),dtype=np.float32)
            if action.shape!=(3,) or not np.isfinite(action).all():raise ValueError('ACTION_SHAPE_OR_FINITE')
            if not (-1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1):raise ValueError('ACTION_RANGE')
            if observation.tobytes()!=data:raise ValueError('OBSERVATION_MUTATED')
            result=dict(action=action.tolist(),diagnostics=getattr(agent,'diagnostics',{}))
            if recorder is not None:
                result['external_estimator_transition']=dict(predicted_speed_before=prediction_before,
                    observed_speed=getattr(agent,'speed',None),grip_prior=getattr(agent,'grip_prior',None),
                    engine_prior=getattr(agent,'engine_prior',None),steering_prior=getattr(agent,'steering_prior',None))
        else:raise ValueError('BAD_PROTOCOL')
        result.update(wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,
                      max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except BaseException as exc:
        result=dict(error=type(exc).__name__+':'+str(exc),
                    diagnostics=getattr(agent,'diagnostics',{}),
                    wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,
                    max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    episode_after=getattr(agent,'counter',[0])[0]
    if command==b'A':research_model_ticks+=max(0,episode_after-episode_before)
    result['episode_model_ticks']=episode_after
    result['resource_model_ticks']=research_model_ticks
    send(result)

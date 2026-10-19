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
spec.loader.exec_module(module)
agent=module.Agent()
if len(sys.argv)>2 and hasattr(agent,'counter'):
    agent.counter.limit=min(50000,max(0,int(sys.argv[2])))


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
    try:
        if command==b'R':
            agent.reset(observation);result=dict(reset=True)
        elif command==b'A':
            action=np.asarray(agent.act(observation),dtype=np.float32)
            if action.shape!=(3,) or not np.isfinite(action).all():raise ValueError('ACTION_SHAPE_OR_FINITE')
            if not (-1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1):raise ValueError('ACTION_RANGE')
            if observation.tobytes()!=data:raise ValueError('OBSERVATION_MUTATED')
            result=dict(action=action.tolist(),diagnostics=getattr(agent,'diagnostics',{}))
        else:raise ValueError('BAD_PROTOCOL')
        result.update(wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,
                      max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      resource_model_ticks=getattr(agent,'counter',[0])[0])
    except BaseException as exc:
        result=dict(error=type(exc).__name__+':'+str(exc),
                    diagnostics=getattr(agent,'diagnostics',{}),
                    wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,
                    max_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result['resource_model_ticks']=getattr(agent,'counter',[0])[0]
    send(result)

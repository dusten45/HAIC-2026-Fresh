"""One bounded candidate repair on saved official pixels and own memory only."""
import argparse
import importlib.util
import json
import pickle
from pathlib import Path
import signal
import sys
import time

import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('checkpoint',type=Path)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--model-cap',type=int,default=10000)
    parser.add_argument('--observation-guard',action='store_true')
    args=parser.parse_args();args.output.mkdir(exist_ok=False)
    from retry.submit_dev import package
    from retry.runtime598_diagnostic import Recorder,dump,plain
    source,source_hash=package(args.output,args.source,args.source.parent/'runtime598.py')
    sys.path.insert(0,str(source.parent))
    spec=importlib.util.spec_from_file_location('agent',source)
    module=importlib.util.module_from_spec(spec);sys.modules['agent']=module;spec.loader.exec_module(module)
    agent=module.Agent()
    agent.__dict__=pickle.loads((args.checkpoint/'agent-before-private.pkl').read_bytes())
    before=agent.counter[0];agent.counter.limit=before+args.model_cap
    recorder=Recorder(agent,args.output,target=1)
    observation=np.load(args.checkpoint/'input-private.npy');observation.flags.writeable=False
    recorder.before_action(observation)
    def timeout(*_):raise TimeoutError('CACHED_WHOLE_ACT_5S')
    signal.signal(signal.SIGALRM,timeout)
    cpu=time.process_time();wall=time.perf_counter();action=None;error=None
    signal.setitimer(signal.ITIMER_REAL,5.)
    try:action=agent.act(observation)
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
    expected=json.loads((args.checkpoint/'checkpoint-private.json').read_text())
    actual=json.loads((args.output/'checkpoint-private.json').read_text())
    guard=actual['high'].pop('observation_fallback',None) if args.observation_guard else None
    previous_guard=expected['high'].pop('observation_fallback',None) if args.observation_guard else None
    invariants={name:actual[name]==expected[name] for name in
        ('root','high','low','progress','roads','boundary','obstacles','running_history')}
    result=dict(action=plain(action),error=error,model_ticks=agent.counter[0]-before,
        CPU_s=time.process_time()-cpu,whole_act_wall_s=time.perf_counter()-wall,
        native_actions=0,source_sha256=source_hash,unchanged_inputs=invariants,
        observation_guard_metadata_added=guard is not None and previous_guard is None,
        observation_guard_present=guard is not None,
        observation_guard_equal_to_checkpoint=guard==previous_guard,
        diagnostics=agent.diagnostics,
        inputs='Official saved pixels and exact pre-action reset-local own memory; no external truth read.')
    dump(args.output/'result-private.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='diagnostics'}))
    assert all(invariants.values()),'NONCANDIDATE_INPUT_CHANGED'
    assert result['model_ticks']<=args.model_cap and result['whole_act_wall_s']<5.


if __name__=='__main__':main()

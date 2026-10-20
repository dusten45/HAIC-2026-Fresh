"""Replay a second frozen pixel Agent on an identical observed action prefix.

This is external offline diagnosis. The participant sees only official saved
observations and its own reset-local memory. Abort if commands diverge before
the predeclared comparison call; no mismatched actions drive an environment.
"""
import argparse,hashlib,importlib.util,json,shutil,sys,time
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('trace');parser.add_argument('source');parser.add_argument('output');parser.add_argument('--call',type=int,required=True);parser.add_argument('--model-cap',type=int,default=65000)
    args=parser.parse_args();trace=Path(args.trace);out=Path(args.output);out.mkdir(exist_ok=False)
    assert 1<=args.call<=400 and 0<args.model_cap<=100000
    source=Path(args.source);shutil.copytree(source.parent,out/'package')
    sys.path.insert(0,str(out/'package'));spec=importlib.util.spec_from_file_location('agent',out/'package'/source.name);module=importlib.util.module_from_spec(spec);sys.modules['agent']=module;spec.loader.exec_module(module)
    from retry.runtime598_diagnostic import Recorder,dump
    agent=module.Agent();agent.counter.limit=args.model_cap
    first=np.load(trace/'observation-prefix-private/0001.npy');agent.reset(first);agent.counter.limit=args.model_cap
    for name in ('external-truth-private.json','initial-private.png'):
        origin=trace/f'call-{args.call:04d}'/name
        if origin.exists():shutil.copy2(origin,out/name)
    recorder=Recorder(agent,out,target=args.call)
    expected=[json.loads(row) for row in (trace/'decisions-private.jsonl').read_text().splitlines()]
    cpu=time.process_time();wall=time.perf_counter();rows=[]
    for number in range(1,args.call+1):
        observation=np.load(trace/f'observation-prefix-private/{number:04d}.npy');observation.flags.writeable=False
        recorder.before_action(observation);begin=time.perf_counter();action=agent.act(observation)
        elapsed=time.perf_counter()-begin;assert elapsed<5.,'OFFLINE_WHOLE_ACT_LIMIT'
        same=action.tolist()==expected[number-1]['action'];rows.append(dict(call=number,action=action,matching_trace_command=same,wall_s=elapsed))
        if number<args.call:assert same,'PREFIX_COMMAND_DIVERGED'
        assert agent.counter[0]<=args.model_cap and time.process_time()-cpu<300. and time.perf_counter()-wall<600.
    dump(out/'result-private.json',dict(status='PAIRED_FIRST_DIVERGENCE_CAPTURED',comparison_call=args.call,
        identical_observation_prefix=True,matching_commands_before=args.call-1,last_command_equal=same,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),decisions=rows,
        model_ticks=agent.counter[0],native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,
        limits='One frozen old Agent on the already collected official prefix; no hidden state input or physical action dispatch.'))
    print(json.dumps(dict(comparison_call=args.call,last_command_equal=same,model_ticks=agent.counter[0],CPU_s=time.process_time()-cpu)))


if __name__=='__main__':main()

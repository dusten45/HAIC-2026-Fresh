"""Public-renderer equivalence and cost regression for object classification.

Compare every retained full center cell and returned diagnostic against a
specified repository revision. No simulator or saved evaluation image is used.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from retry.object_occlusion_check import a, scene


def check(revision):
    source=subprocess.run(['git','show',revision+':submit_core/observation_agent.py'],
        check=True,capture_output=True,text=True).stdout
    fn=next(n for n in ast.parse(source).body
        if isinstance(n,ast.FunctionDef) and n.name=='compatible_object_envelope')
    namespace=a.__dict__.copy()
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<baseline object classifier>','exec'),namespace)
    original=namespace['compatible_object_envelope'];candidate=a.compatible_object_envelope
    rng=np.random.default_rng(20261020);cases=[];cpu=time.process_time()
    accepted=0;old_time=0.;new_time=0.
    for i in range(24):
        shade=int(rng.choice([102,104,107]));phase=float(rng.uniform(0,1))
        angle=float(rng.uniform(0,np.pi/8));offset=float(rng.uniform(-2,2))
        image,_,_=scene(shade,phase,angle,offset=offset)
        observed,_=a.detect_observed_obstacles(image)
        if len(observed)!=1:
            cases.append(dict(detected=False));continue
        results=[];times=[]
        try:
            for classifier in (original,candidate):
                a.compatible_object_envelope=classifier;begin=time.perf_counter()
                results.append(a.observed_object_road_patch(image,observed[0][0],0.))
                times.append(time.perf_counter()-begin)
        finally:a.compatible_object_envelope=candidate
        assert repr(results[0])==repr(results[1]),'OBJECT_OUTPUT_CHANGED'
        accepted+=int(results[0] is not None);old_time+=times[0];new_time+=times[1]
        cases.append(dict(detected=True,accepted=results[0] is not None,
            exact_output_equal=True,baseline_wall_s=times[0],candidate_wall_s=times[1]))
    assert accepted>=16,'INSUFFICIENT_ACCEPTED_PUBLIC_CASES'
    return dict(status='PASS',cases=cases,accepted=accepted,
        baseline_wall_s=old_time,candidate_wall_s=new_time,
        speedup=old_time/new_time,CPU_s=time.process_time()-cpu,
        baseline_revision=revision,model_ticks=0,native_actions=0,
        candidate_sha256=hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),
        scope='Exact complete public-renderer output equivalence, including all full center cells. Finite regression; unchanged physical/quantization assumptions.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baseline-revision',required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    result=check(args.baseline_revision)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))

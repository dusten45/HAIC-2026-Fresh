"""Native0 regression check for the diagnostic serialization failure."""
import argparse
import ast
import dataclasses
import json
import time
from pathlib import Path
import numpy as np
from damage import calculate_damage_effects
from retry.path271_run import read,save,sha
from retry.episode336_run import json_default


def run(R):
    D=R/'stage336';G=Path(__file__).resolve().parent.parent;original=D/'executed-source/episode336_run.py';fixed=G/'retry/episode336_run.py';p=read(D/'plan.json');assert sha(original)==p['source_hashes'][str(fixed)];start,cpu=time.perf_counter(),time.process_time()
    for damage in [0.,.2,1.]:
        effects=calculate_damage_effects(damage);info=dict(collision=bool(damage),damage=damage,damage_effects=effects,finish_time_s=None,finished=False)
        failed=False
        try:json.dumps(info,allow_nan=False)
        except TypeError:failed=True
        assert failed
        restored=json.loads(json.dumps(info,allow_nan=False,default=json_default));assert restored['damage_effects']==dataclasses.asdict(effects) and restored['damage']==damage
    nested=dict(info=info,array=np.array([1.,2.]),scalar=np.int64(3));assert json.loads(json.dumps(nested,default=json_default))['scalar']==3
    old=next(x for x in ast.parse(original.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='run');new=next(x for x in ast.parse(fixed.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='run')
    for node in ast.walk(new):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='dumps':node.keywords=[k for k in node.keywords if k.arg!='default']
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
    receipt=dict(passed=True,original_failure_reproduced_without_env=True,damage_dataclass_levels_tested=3,numpy_nested_supported=True,run_AST_same_except_json_default_keyword=True,policy_control_physics_timing_unchanged=True,new_native_actions=0,new_actor_calls=0,new_source_physics_ticks=0,new_learning_fits=0,original_executed_source=str(original),original_executed_source_sha256=sha(original),fixed_public_source=str(fixed),fixed_public_source_sha256=sha(fixed),fixed_source_not_executed_native=True,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)
    save(D/'serializer-repair-verification.json',receipt);print(json.dumps({k:receipt[k] for k in ['passed','original_failure_reproduced_without_env','run_AST_same_except_json_default_keyword','new_native_actions','fixed_source_not_executed_native']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)

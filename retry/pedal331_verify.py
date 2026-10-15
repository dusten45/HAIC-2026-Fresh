"""Independent checks on saved331 traces; no simulator step or policy call."""
import json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import digest,verify


def inspect(R):
    D=R/'stage331';p=verify(R);old=np.load(R/'stage330/evaluation/N2/raw-pixels-actions-private.npz');a=np.load(D/'A/raw-pixels-actions-private.npz');b=np.load(D/'B/raw-pixels-actions-private.npz')
    assert np.array_equal(old['observations'],a['observations']) and np.array_equal(old['actions'],a['actions'])
    assert np.array_equal(a['observations'][:65],b['observations'][:65]) and np.array_equal(a['actions'][:64],b['actions'][:64])
    assert np.array_equal(a['actions'][64:,0],b['actions'][64:,0])
    boundary_a=read(D/'A/boundary-private.json');boundary_b=read(D/'B/boundary-private.json');assert boundary_a==boundary_b
    for key in ['physical','policy','RNG']:assert digest(boundary_a[key])==boundary_a[key+'_sha256']
    changed_pedals=int(np.any(a['actions'][64:,1:]!=b['actions'][64:,1:],axis=1).sum());different_nominal_steers=0
    for label in ['A','B']:
        rows=[json.loads(s) for s in (D/label/'trace-private.jsonl').read_text().splitlines()]
        for row in rows:
            assert np.float32(row['nominal_memory'])==np.float32(row['calculated296'][0])
            assert row['nominal_memory']==row['policy']['previous_steer']
        if label=='B':
            for row in rows[64:]:
                assert row['executed'][1:]==row['calculated296'][1:]
                different_nominal_steers+=row['calculated_steering']!=row['executed_steering']
    v=read(R/'project-effective-budget-v338.json');assert v['research_remaining']==71 and v['actual_cumulative_wrapper_actions']==1282055 and v['final_reserve_used']==0
    assert sum(json.loads(s).get('stage')==331 for s in (R/'experiment-cost-lines.jsonl').read_text().splitlines())==1
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    r=dict(passed=True,native_actions=0,new_policy_calls=0,A_original330_all_pixels_actions_exact=True,
        common_prefix_observation_stacks_exact=65,common_prefix_actions_exact=64,steering_fixed_branch_actions=8,
        branch_pedal_commands_different=changed_pedals,B_calculated_vs_executed_steering_different=different_nominal_steers,
        nominal_memory_calculated_steering_preserved_all144=True,boundary_full_captured_dict_exact=True,cost_ledger_stage331_entries=1,champion296_preserved=True,splits_unopened=True)
    save(D/'independent-verification.json',r);print(json.dumps(r))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);inspect(p.parse_args().private_root)

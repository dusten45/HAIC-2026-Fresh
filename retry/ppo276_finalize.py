"""Export only finalcheckpoint64 and verify small pixel-only inference parity."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def finalize(R):
    import torch
    from retry.ppo275_model import create,vector,apply
    from retry.ppo275_build import build
    from retry.frozen_composite_runtime import prepare
    G=Path(__file__).resolve().parent.parent;D=R/'stage276';p=read(D/'training-plan.json');out=read(D/'training-outcome-private.json')
    state=read(D/'state.json');assert state['last_committed_batch']==64 and state['valid_training_total']==65536 and out['technical_error'] is None
    assert not (D/'candidate-private.json').exists()
    actor,_=create();cp=torch.load(D/'checkpoint64.pt');actor.load_state_dict(cp['actor']);normal=np.load(p['normalization'])
    assert cp['completed_batch']==64 and len(cp['updates'])==64
    config=build(Path(p['base']['archive_path']),D/'final-actor-private.npz',D/'submission276-final.zip')
    config.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'));save(D/'candidate-private.json',config)
    a=b=None;pairs=calls=0;start=time.perf_counter()
    try:
        a=prepare(p['base'],D/'final-parity-torch',p['sandbox_path']);b=prepare(config,D/'final-parity-numpy',p['sandbox_path'])
        for road in ['O0','N0']:
            z=np.load(R/'stage251/training'/road/'cache-private.npz');a.call('reset',z['observations'][0]);b.call('reset',z['observations'][0]);calls+=2
            for obs in z['observations'][:8]:
                ra,_=a.call('act',obs);rb,_=b.call('act',obs);calls+=2
                with torch.no_grad():mu=actor(torch.as_tensor(vector(ra,normal['mean'],normal['std']),dtype=torch.float64)).numpy()
                action=apply(ra['action'],mu);committed,_=a.call('commit',action);calls+=1
                assert np.array_equal(action,np.array(rb['action'],np.float32)) and ra['features']==rb['features']
                assert all(committed['state'][k]==rb['nominal_state'][k] for k in ['previous_steer','hazards_sha256','previous_image_sha256','lateral_acceleration']);pairs+=1
    finally:
        if a:assert a.close()['process_reaped']
        if b:assert b.close()['process_reaped']
    save(D/'final-parity-receipt.json',dict(passed=True,checkpoint=64,checkpoint_sha256=sha(D/'checkpoint64.pt'),archive_sha256=config['archive_sha256'],pairs=pairs,offline_calls=calls,wall_s=time.perf_counter()-start,native=0,pixel_only=True,not_official_qualification=True))
    # Screen identities are used here only after finalcheckpoint exists.
    screens=read(Path(p['screen_registration']))['cases'];old=read(R/'stage270/plan.json')
    cases=dict(p['cases']);cohorts={r:'TRAIN_regression' for r in cases}
    order=[dict(road=r,arm='candidate') for r in ['O0','O2','N0','N1','N2','N3']]
    for i,case in enumerate(screens):
        label=f'S276-{i}';cases[label]=case;cohorts[label]='fresh_DEV_screen'
        for arm in (['baseline','candidate'] if i==0 else ['candidate','baseline']):order.append(dict(road=label,arm=arm))
    baseline=dict(p['base']);baseline.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'))
    sources=[G/'retry/ppo276_eval.py',G/'retry/ppo276_finalize.py',D/'training-plan.json',D/'checkpoint64.pt',D/'final-actor-private.npz',Path(config['archive_path']),Path(baseline['archive_path']),Path(p['screen_registration']),D/'final-parity-receipt.json']
    ep=dict(stage=276,order=order,cases=cases,cohorts=cohorts,candidate=config,baseline=baseline,sandbox_path=p['sandbox_path'],initial_observations=p['initial_observations'],TRAIN_baselines={r:old['baselines'][r] for r in p['cases']},
        final_checkpoint_sha256=sha(D/'checkpoint64.pt'),hashes={str(q):sha(q) for q in sources},no_model_reselection=True,evaluation_native_cap=6500)
    save(D/'evaluation-plan.json',ep);(D/'evaluation-plan.sha256').write_text(sha(D/'evaluation-plan.json')+'\n');(D/'evaluation-plan.sha256').chmod(0o600)
    print('Finalcheckpoint64 exported;16pixel action/state pairs exact; freshDEVpair plan frozen',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);finalize(a.parse_args().private_root.resolve())

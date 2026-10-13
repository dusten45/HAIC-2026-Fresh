"""Freeze both finalpaired models, preserve common-start evidence, no selection."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(R):
    import torch
    from retry.ppo275_model import create,vector,apply
    from retry.ppo275_build import build
    from retry.frozen_composite_runtime import prepare
    G=Path(__file__).resolve().parent.parent;D=R/'stage278';plan=read(D/'plan.json');configs={};native=0
    assert not (D/'evaluation-plan.json').exists()
    first={}
    for arm in ['control','lambda1']:
        A=D/arm;p=read(A/'training-plan.json');out=read(A/'training-outcome-private.json');assert out['technical_error'] is None and read(A/'state.json')['last_committed_batch']==10
        assert sum(e['valid_samples'] for e in out['episodes'])==8192;native+=read(A/'budget.json')['actions']
        first[arm]=dict(np.load(A/'rollout3-private.npz'))
        actor,_=create();actor.load_state_dict(torch.load(A/'checkpoint10.pt')['actor']);normal=np.load(p['normalization'])
        config=build(Path(p['base']['archive_path']),A/'final-actor-private.npz',A/'submission-final.zip');config.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'));save(A/'candidate-private.json',config);configs[arm]=config
        a=b=None;pairs=calls=0;start=time.perf_counter()
        try:
            a=prepare(p['base'],A/'parity-host',p['sandbox_path']);b=prepare(config,A/'parity-numpy',p['sandbox_path'])
            obs=np.load(R/'stage251/training/N0/cache-private.npz')['observations'];a.call('reset',obs[0]);b.call('reset',obs[0]);calls+=2
            for image in obs[:8]:
                ra,_=a.call('act',image);rb,_=b.call('act',image);calls+=2
                with torch.no_grad():mu=actor(torch.as_tensor(vector(ra,normal['mean'],normal['std']),dtype=torch.float64)).numpy()
                action=apply(ra['action'],mu);committed,_=a.call('commit',action);calls+=1
                assert np.array_equal(action,np.array(rb['action'],np.float32)) and ra['features']==rb['features']
                assert all(committed['state'][k]==rb['nominal_state'][k] for k in ['previous_steer','hazards_sha256','previous_image_sha256','lateral_acceleration']);pairs+=1
        finally:
            if a:assert a.close()['process_reaped']
            if b:assert b.close()['process_reaped']
        save(A/'parity-receipt.json',dict(passed=True,pairs=pairs,offline_calls=calls,wall_s=time.perf_counter()-start,native=0,final_checkpoint=10,archive_sha256=config['archive_sha256']))
    exact={k:bool(np.array_equal(first['control'][k],first['lambda1'][k])) for k in ['x','latent','old_mu','old_logp','reward','value','next_value','done','cut','base','executed']}
    save(D/'paired-initial-receipt.json',dict(same_initial_checkpoint=True,same_optimizer=True,same_noise_shuffle_seeds=True,first_rollout_equal=exact,
        later_trajectories_not_forced_identical=True,no_policy_selection=True))
    save(D/'budget.json',dict(actions=native,training=native,evaluation=0))
    p=read(D/'control/training-plan.json');old=read(R/'stage270/plan.json')
    sources=[G/'retry/ppo278_eval.py',G/'retry/ppo278_finalize.py',D/'plan.json',D/'paired-initial-receipt.json']
    for arm in ['control','lambda1']:sources.extend([D/arm/'checkpoint10.pt',D/arm/'candidate-private.json',Path(configs[arm]['archive_path'])])
    ep=dict(stage=278,deadline_utc=p['deadline_utc'],candidates=configs,cases={r:p['cases'][r] for r in ['N0','N2']},initial_observations={r:p['initial_observations'][r] for r in ['N0','N2']},baselines={r:old['baselines'][r] for r in ['N0','N2']},sandbox_path=p['sandbox_path'],
        order=[dict(road='N0',arm='control'),dict(road='N0',arm='lambda1'),dict(road='N2',arm='lambda1'),dict(road='N2',arm='control')],hashes={str(q):sha(q) for q in sources},TRAIN_diagnostic_not_independent=True)
    save(D/'evaluation-plan.json',ep);(D/'evaluation-plan.sha256').write_text(sha(D/'evaluation-plan.json')+'\n');(D/'evaluation-plan.sha256').chmod(0o600)
    print('278bothfinal10 exported:8inferencepairs each, firstrollout equality recorded,4TRAINdiagnostic runs frozen',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())

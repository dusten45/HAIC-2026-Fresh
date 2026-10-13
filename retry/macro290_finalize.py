"""Freeze only checkpoint16, stochasticNumPy parity, then open two fixedscreens."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save

def run(R):
 import torch
 from retry.macro290_model import create,vector,apply
 from retry.macro290_build import build
 from retry.frozen_composite_runtime import prepare
 G=Path(__file__).resolve().parent.parent;D=R/'stage290';p=read(D/'training-plan.json');out=read(D/'training-outcome-private.json');assert out['technical_error'] is None and read(D/'state.json')['last_committed_batch']==16;assert not (D/'evaluation-plan.json').exists()
 actor,_=create();cp=torch.load(D/'checkpoint16.pt');actor.load_state_dict(cp['actor']);norm=np.load(p['normalization']);candidate=build(Path(p['base']['archive_path']),D/'final-actor-private.npz',D/'submission290-final.zip');candidate.update(worker_path=str(G/'retry/macro290_worker.py'),worker_sha256=sha(G/'retry/macro290_worker.py'));save(D/'candidate-private.json',candidate)
 pairs=0;start=time.perf_counter()
 for road in ['O0','N0']:
  host=package=None;rng=np.random.default_rng(29007);remaining=0;category=0
  try:
   host=prepare(p['base'],D/('parity-host-'+road),p['sandbox_path']);package=prepare(candidate,D/('parity-numpy-'+road),p['sandbox_path']);obs=np.load(R/'stage251/training'/road/'cache-private.npz')['observations'];host.call('reset',obs[0]);package.call('reset',obs[0])
   for image in obs[:8]:
    rh,_=host.call('act',image);rp,_=package.call('act',image)
    if remaining==0:
     with torch.no_grad():prob=actor(torch.tensor(vector(rh,norm['mean'],norm['std']),dtype=torch.float64)).softmax(0).numpy()
     category=int(rng.choice(5,p=prob));remaining=3;assert np.max(abs(prob-np.array(rp['macro_audit']['probabilities'])))<1e-12
    action=apply(rh['action'],rh['features'],category);c,_=host.call('commit',action);remaining-=1
    assert np.array_equal(action,np.array(rp['action'],np.float32));assert rh['features']==rp['features'];assert rp['macro_audit']['category']==category and rp['macro_audit']['remaining']==remaining
    assert np.float32(c['memory'])==np.float32(rp['nominal_state']['previous_steer']);assert rp['executed_history']==c['history'];pairs+=1
  finally:
   if host:assert host.close()['process_reaped']
   if package:assert package.close()['process_reaped']
 save(D/'final-parity-receipt.json',dict(passed=True,pairs=pairs,checkpoint=16,checkpoint_sha256=sha(D/'checkpoint16.pt'),archive_sha256=candidate['archive_sha256'],wall_s=time.perf_counter()-start,native=0,reset_sampling_seed=29007))
 # Only final16 exists before reading registeredscreen identities for evaluation.
 assert sha(Path(p['screen_registration']))==p['screen_registration_sha256'];screens=read(Path(p['screen_registration']))['cases'];cases=dict(p['cases']);cohorts={r:'TRAIN_regression' for r in cases};order=[dict(road=r,arm='candidate') for r in ['O0','O2','N0','N1','N2','N3']]
 for i,c in enumerate(screens):
  label=f'S290-{i}';cases[label]=c;cohorts[label]='fresh_DEV_screen'
  for arm in (['baseline','candidate'] if i==0 else ['candidate','baseline']):order.append(dict(road=label,arm=arm))
 baseline=dict(p['base']);baseline.update(worker_path=str(G/'retry/macro290_worker.py'),worker_sha256=sha(G/'retry/macro290_worker.py'))
 source=[D/'checkpoint16.pt',Path(candidate['archive_path']),D/'final-parity-receipt.json',G/'retry/macro290_eval.py',Path(p['screen_registration']),D/'training-plan.json'];ep=dict(stage=290,cases=cases,cohorts=cohorts,order=order,candidate=candidate,baseline=baseline,sandbox_path=p['sandbox_path'],initial_observations=p['initial_observations'],TRAIN_baselines=read(R/'stage270/plan.json')['baselines'],final_checkpoint_sha256=sha(D/'checkpoint16.pt'),hashes={str(q):sha(q) for q in source},no_model_selection=True)
 save(D/'evaluation-plan.json',ep);(D/'evaluation-plan.sha256').write_text(sha(D/'evaluation-plan.json')+'\n');(D/'evaluation-plan.sha256').chmod(0o600);print('290final16 frozen:16stochastic NumPy/hostmacro parity pairs;10runs registered',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())

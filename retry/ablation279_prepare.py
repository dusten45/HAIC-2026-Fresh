"""Freeze two output ablations of 276 checkpoint64; no training or tuning."""
import argparse,zipfile,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(R):
 import torch
 G=Path(__file__).resolve().parent.parent;D=R/'stage279';assert not D.exists();D.mkdir(mode=0o700)
 source=R/'stage276';cp=torch.load(source/'checkpoint64.pt');assert cp['completed_batch']==64
 params=np.load(source/'final-actor-private.npz')
 for k,v in cp['actor'].items():assert np.array_equal(v.numpy(),params['actor_'+k])
 old=read(source/'evaluation-plan.json');config=read(source/'candidate-private.json');assert sha(Path(config['archive_path']))==config['archive_sha256'];assert read(source/'final-parity-receipt.json')['passed']
 candidates={}
 with zipfile.ZipFile(config['archive_path']) as z:original={n:z.read(n) for n in z.namelist()}
 for arm,scale in [('A',[0,.03,.02]),('B',[.015,0,0])]:
  members=dict(original);s=members['agent.py'].decode();assert s.count('np.array([.015,.03,.02])')==1
  s=s.replace('np.array([.015,.03,.02])','np.array('+repr(scale)+')')
  s=s.replace('        if action[0]!=base[0]:', '        self.ablation_audit=dict(base=base.tolist(),latent=latent.tolist(),full_action=np.clip(base.astype(float)+np.array([.015,.03,.02])*np.tanh(latent),[-.4,0,0],[.4,1,1]).astype(np.float32).tolist())\n        if action[0]!=base[0]:')
  members['agent.py']=s.encode();assert all(members[n]==v for n,v in original.items() if n!='agent.py')
  archive=D/(arm+'.zip')
  with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
   for n,v in sorted(members.items()):z.writestr(n,v)
  archive.chmod(0o600);c=dict(config);c.update(archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:__import__('hashlib').sha256(v).hexdigest() for n,v in members.items()},worker_path=str(G/'retry/ablation279_worker.py'),worker_sha256=sha(G/'retry/ablation279_worker.py'));candidates[arm]=c
 save(D/'budget.json',dict(actions=0,training=0,evaluation=0))
 p=dict(stage=279,deadline_utc='2026-10-16T10:01:55+00:00',candidates=candidates,cases={r:old['cases'][r] for r in ['N0','N2']},initial_observations={r:old['initial_observations'][r] for r in ['N0','N2']},baselines={r:old['TRAIN_baselines'][r] for r in ['N0','N2']},sandbox_path=old['sandbox_path'],order=[dict(arm=a,road=r) for r in ['N0','N2'] for a in ['A','B']],native_cap=2600,per_run_cap=650,checkpoint=64,checkpoint_sha256=sha(source/'checkpoint64.pt'),source_archive_sha256=config['archive_sha256'],closed_loop_actual_action_memory=True,no_training=True,no_tuning=True,no_promotion=True,TRAIN_only=True)
 sources=[G/'retry/ablation279_prepare.py',G/'retry/ablation279_worker.py',G/'retry/ablation279_eval.py',source/'checkpoint64.pt',source/'final-actor-private.npz',Path(config['archive_path']),R/'project-effective-budget-v282.json']+[Path(c['archive_path']) for c in candidates.values()]
 p['hashes']={str(q):sha(q) for q in sources};save(D/'evaluation-plan.json',p);(D/'evaluation-plan.sha256').write_text(sha(D/'evaluation-plan.json')+'\n');(D/'evaluation-plan.sha256').chmod(0o600)
 print('279 frozen:276 cp64 parameters exact, only scales removed;4TRAIN runs cap2600',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())

"""Register and run a fixed, native-zero diagnostic on already observed states."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]


def prepare(R):
    D=R/'stage348';assert not D.exists();D.mkdir(mode=0o700)
    deadline=read(R/'research-deadline-current.json')['deadline_utc']
    assert time.time()<datetime.datetime.fromisoformat(deadline.replace('Z','+00:00')).timestamp()
    v=read(R/'project-effective-budget-v359.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(233,84000,0)
    specs=[('source296',346,347,list(range(146,154)),'routing_evidence'),('current334',343,343,[137,145],'routing_evidence'),('N2',340,337,[127,128],'routing_filter')]
    groups={};sources={};comparisons=[]
    for label,stage,peer_stage,steps,key in specs:
        folder=R/f'stage{stage}/B';peer=R/f'stage{peer_stage}'/('B' if peer_stage==337 else 'A')
        p=read(R/f'stage{stage}/plan.json');cfg=p.get('configs',{}).get('B',p.get('config'))
        assert sha(cfg['archive_path'])==cfg['archive_sha256']
        group='source296' if label=='source296' else 'current334'
        entry=groups.setdefault(group,dict(package=str(folder/'cpu/package'),members_sha256=cfg['members_sha256'],states=[],image_list=[]))
        assert entry['members_sha256']==cfg['members_sha256']
        records=rows(folder/'trace-private.jsonl');pr=rows(peer/'trace-private.jsonl');images=np.load(folder/'frames-actions-private.npz')['frames_uint8'];pi=np.load(peer/'frames-actions-private.npz')['frames_uint8']
        for q in [folder/'trace-private.jsonl',folder/'frames-actions-private.npz',peer/'trace-private.jsonl',peer/'frames-actions-private.npz',Path(cfg['archive_path']),R/f'stage{stage}/plan.json']:sources[str(q)]=sha(q)
        for step in steps:
            r=records[step-1];other=pr[step-1];e=r[key];assert len(e['removed_indices'])<=1
            assert r['executed']==r['returned_action'];assert r['nominal_memory']==r['policy']['previous_steer'];assert np.float32(r['nominal_memory'])==np.float32(r['executed'][0])==np.float32(r['features'][13])
            assert r['features'][7]==records[step-2]['nominal_memory']
            common=bool(np.array_equal(images[max(0,step-4):step],pi[max(0,step-4):step]) and r['pre_physical']==other['pre_physical'] and all(r['features'][j]==other['features'][j] for j in [3,4,7,8,11,12]))
            if (label,step) in [('source296',146),('current334',137),('current334',145),('N2',127)]:assert common
            entry['states'].append(dict(label=label,step=step,features=r['features'],pixel_path=r['pixel_path'],routing_hazards=[h[:3] for h in e['routing_hazards']],full_hazards=[h[:3] for h in e['full_hazards']]))
            entry['image_list'].append(images[step-1].astype(np.float32)/255)
            comparisons.append(dict(label=label,step=step,common_input_and_prestate=common,removed=len(e['removed_indices']),actual_control=r['executed'],peer_control=other['executed'],actual_target=r['features'][1:3],peer_target=other['features'][1:3],peer_path=other['pixel_path'],feature_difference_indices=[j for j,(x,y) in enumerate(zip(r['features'],other['features'])) if x!=y]))
    for name,e in groups.items():
        images=D/f'{name}-images-private.npz';np.savez_compressed(images,images=np.asarray(e.pop('image_list')));images.chmod(0o600);e['images']=str(images);save(D/f'{name}-inputs-private.json',e);sources[str(images)]=sha(images);sources[str(D/f'{name}-inputs-private.json')]=sha(D/f'{name}-inputs-private.json')
    sources.update({str(G/'retry'/f):sha(G/'retry'/f) for f in ['link348_stage.py','link348_functions.py']})
    p=dict(stage=348,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,groups=list(groups),source_hashes=sources,budget=dict(routing_calls=24,target_calls=24,actor_calls=0,native_actions=0,resets=0,fits=0,sweeps=0,research_remaining=233,final_reserve=84000),stop='Stop on source/hash/path/target reproduction mismatch. No retry, extra call, tuning, rollout, split opening or promotion.',promotion='None; routing/target restoration only. Recorded control linkage requires common input and prestate. No counterfactual controller calls.',scope='296 O2 146-153; current334ON/H1 O2 unchanged 137/145; N2 pre132 127/128. Supersedes earlier all-held-state proposal; 203 lineage is untested.',comparisons=comparisons)
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    return p


def run(R):
    p=prepare(R);D=R/'stage348'
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='');env.pop('PYTHONPATH',None)
    for name in p['groups']:
        assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
        data=read(D/f'{name}-inputs-private.json')
        subprocess.run([str(G/'.venv/bin/python'),'-I','-B',str(G/'retry/link348_functions.py'),'--package',data['package'],'--input',str(D/f'{name}-inputs-private.json'),'--output',str(D/f'{name}-output-private.json')],env=env,check=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())

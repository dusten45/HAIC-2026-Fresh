"""Two fixed supplementary force contrasts; no native control or coefficient fit."""
import argparse,json
from pathlib import Path
import numpy as np
from retry.force255_probe import forecast


def run(root,output):
    assert not output.exists()
    results=[]
    for road,action in [('O0',67),('N0',82)]:
        folder=root/'stage251/training'/road;m=json.loads((folder/'materialized.json').read_text());z=np.load(folder/'cache-private.npz');base=z['commands'][action-1:action+2];speed=float(z['features'][action-1,4]);K=.06*(speed/.54+5)
        for mode in ['dual_neutral','paired_reduction']:
            controls=base.copy()
            if mode=='dual_neutral':controls[:,1:]=0
            else:
                d=np.minimum(controls[:,2].astype(float),controls[:,1].astype(float)/K);controls[:,1]=(controls[:,1]-K*d).astype(np.float32);controls[:,2]=(controls[:,2]-d).astype(np.float32);controls[:,1:]=np.clip(controls[:,1:],0,1)
            assert np.array_equal(controls[:,0],base[:,0]);q=forecast(m['snapshots'][str(action)],controls,True);results.append(dict(road=road,action=action,mode=mode,legal_snapshot_speed=speed,K=K,prediction=q))
    with output.open('x') as f:json.dump(dict(results=results,native_actions=0,model_queries=4,model_ticks=sum(r['prediction']['physics_ticks'] for r in results)),f,indent=2);f.write('\n')
    output.chmod(0o600)

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',type=Path,required=True);a.add_argument('--output',type=Path,required=True);p=a.parse_args();run(p.root,p.output)

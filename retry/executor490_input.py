"""Load the490 reference by pinned owners; never duplicate or transform its line."""
import hashlib,json
from pathlib import Path
import numpy as np

def array_sha(x):return hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
def load(manifest_path):
    m=json.loads(Path(manifest_path).read_text())
    for path,digest in m['owners'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    with np.load(m['line_owner'],allow_pickle=False) as z:line=z['line']
    with np.load(m['arrays_owner'],allow_pickle=False) as z:derived={k:z[k] for k in z.files}
    model=json.loads(Path(m['model_owner']).read_text())['model']
    curvature=np.asarray(json.loads(Path(m['curvature_owner']).read_text())['curvature'],dtype=np.float64)
    assert array_sha(line)==m['line_sha256'] and array_sha(derived['projected_nodes'])==m['nodes_sha256']
    assert array_sha(curvature)==m['curvature_sha256']
    n=len(line);ds=derived['ds'];nodes=derived['projected_nodes']
    assert line.shape==(n,2) and ds.shape==(n,) and curvature.shape==(n,) and nodes.shape==(n+1,)
    assert np.isfinite(line).all() and np.isfinite(curvature).all() and np.isfinite(ds).all() and np.all(ds>0)
    assert np.array_equal(ds,np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1))
    assert nodes[0]==0 and np.isfinite(nodes).all() and np.all(nodes[1:]>0)
    for x in (line,curvature,*derived.values()):x.setflags(write=False)
    profile=dict(ds=ds,curvature=curvature,speed=derived['speed'])
    fixed=dict(line=line,free_profile=profile,model=model,free_feasible=True,whole_map_GT=True)
    return fixed,derived['pace'],nodes

def bind(policy,nodes):
    # Call AFTER paired417.policy has applied its legacy speed*pace assignment.
    before={k:getattr(policy,k) for k in ('phase','previous_arc','s','last_time','launch_commanded')}
    policy.nodes=np.asarray(nodes,dtype=np.float64);policy.nodes.setflags(write=False)
    assert before=={k:getattr(policy,k) for k in before}
    assert policy.nodes.tobytes()==np.asarray(nodes,dtype=np.float64).tobytes()
    assert policy.nodes[0]==0 and np.all(policy.nodes[1:]>0) and np.isfinite(policy.nodes).all()
    return policy

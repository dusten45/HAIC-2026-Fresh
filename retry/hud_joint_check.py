"""Public HUD renderer quantization checks; no environment reset or case data."""
from pathlib import Path
from types import SimpleNamespace as N
import sys,json,time
import cv2,numpy as np,pygame
from core.vendor.car_racing import CarRacing


def render_joint(joint=0.,speed=0.,yaw=0.):
    surface=pygame.Surface((1000,800));surface.fill((0,0,0))
    wheels=[N(omega=0.,joint=N(angle=joint)) for _ in range(4)]
    fake=N(surf=surface,car=N(hull=N(linearVelocity=(0.,speed),angularVelocity=yaw),wheels=wheels))
    CarRacing._render_indicators(fake,1000,800)
    surface=pygame.transform.smoothscale(surface,(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.


def feature(image):return float(np.sum(image[75:81,32:42])-np.sum(image[75:81,42:52]))


def main():
    p=Path(sys.argv[1]);assert not p.exists();start=time.process_time()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'));import observation_agent as agent
    regenerated=np.asarray([feature(render_joint((499.5-x)/250.)) for x in range(400,601)])
    assert np.allclose(regenerated,agent.JOINT_HUD_FEATURES,rtol=0,atol=5e-8),'PUBLIC_TEMPLATE_REGENERATION'
    records=[]
    for q in np.r_[np.linspace(-.3997,.3997,101),0.,.17137,-.17137]:
        image=render_joint(float(q));estimate,interval=agent.decode_joint_hud(image,None)
        old=float(np.clip(feature(image)/51.7734,-.4,.4));lo,hi=interval
        records.append(dict(joint=float(q),old_error=abs(old-q),new_error=abs(estimate-q),in_interval=bool(lo-1e-12<=q<=hi+1e-12),interval_width=hi-lo))
    # A dynamics prior is only retained inside the independently observed bin.
    image=render_joint(.17137);prior=.1711;estimate,interval=agent.decode_joint_hud(image,prior);assert estimate==prior
    rejected,interval=agent.decode_joint_hud(image,.3);assert interval[0]<=rejected<=interval[1] and rejected!=.3
    result=dict(public_template_endpoints_checked=201,status='PASS',cases=len(records),old_MAE_rad=float(np.mean([r['old_error'] for r in records])),new_MAE_rad=float(np.mean([r['new_error'] for r in records])),
        max_interval_width_rad=max(r['interval_width'] for r in records),all_in_observed_interval=all(r['in_interval'] for r in records),
        prior_outside_interval_rejected=True,CPU_s=time.process_time()-start,native_actions=0,model_ticks=0,records=records,
        scope='Known public HUD rendering quantization under its fixed resize pipeline; not a joint-rate or physics safety certificate.')
    result['status']='PASS' if result['all_in_observed_interval'] and result['new_MAE_rad']<result['old_MAE_rad'] else 'FAIL'
    p.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));assert result['status']=='PASS'


if __name__=='__main__':main()

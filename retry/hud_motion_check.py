"""Public HUD speed/yaw quantization and prediction-conditioning checks."""
from pathlib import Path
import sys,json,time
import numpy as np
from retry.hud_joint_check import render_joint


def main():
    out=Path(sys.argv[1]);assert not out.exists();start=time.process_time()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'));import observation_agent as a
    speed_table=np.asarray([float(np.sum(render_joint(speed=(h-.5)*2.5)[76:83,10:14])) for h in range(1,41)])
    yaw_table=[]
    for endpoint in range(650,851):
        image=render_joint(yaw=(749.5-endpoint)/20.);yaw_table.append(float(np.sum(image[75:81,54:63])-np.sum(image[75:81,63:72])))
    assert np.allclose(speed_table,a.SPEED_HUD_FEATURES,rtol=0,atol=5e-8) and np.allclose(yaw_table,a.YAW_HUD_FEATURES,rtol=0,atol=5e-8)
    rows=[]
    for speed,yaw in zip(np.linspace(.001,99.999,91),np.linspace(-4.999,4.999,91)):
        image=render_joint(speed=float(speed),yaw=float(yaw));vs,wy,si,yi=a.decode_motion_hud(image,None,None)
        assert si is not None and yi is not None
        old_s=max(0.,float(np.sum(image[76:83,10:14]))/.091728-2.5)
        old_y=float(np.sum(image[75:81,54:63])-np.sum(image[75:81,63:72]))/2.109744
        rows.append(dict(speed_error=abs(vs-speed),old_speed_error=abs(old_s-speed),yaw_error=abs(wy-yaw),old_yaw_error=abs(old_y-yaw),inside=bool(si[0]-1e-12<=speed<=si[1]+1e-12 and yi[0]-1e-12<=yaw<=yi[1]+1e-12)))
        # Same-time priors inside bins survive; contradictory ones are clipped.
        new_s,new_y,_,_=a.decode_motion_hud(image,float(speed),float(yaw));assert abs(new_s-speed)<1e-12 and abs(new_y-yaw)<1e-12
    result=dict(public_template_bins_checked=241,status='PASS',cases=len(rows),all_true_values_inside_public_bins=all(r['inside'] for r in rows),
      speed_MAE_m_s=float(np.mean([r['speed_error'] for r in rows])),old_speed_MAE_m_s=float(np.mean([r['old_speed_error'] for r in rows])),
      yaw_MAE_rad_s=float(np.mean([r['yaw_error'] for r in rows])),old_yaw_MAE_rad_s=float(np.mean([r['old_yaw_error'] for r in rows])),
      CPU_s=time.process_time()-start,native_actions=0,model_ticks=0,scope='Fixed public renderer quantization; prior fusion is not a state certificate.')
    assert result['all_true_values_inside_public_bins'] and result['speed_MAE_m_s']<result['old_speed_MAE_m_s'] and result['yaw_MAE_rad_s']<result['old_yaw_MAE_rad_s']
    out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


if __name__=='__main__':main()

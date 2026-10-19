"""Finite counterexamples for reference joins; geometry is never extended."""
import json,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a

def main():
    cpu=time.process_time();out=Path(sys.argv[1]);assert not out.exists()
    # A skipped angular sample is not an observed physical break in pavement.
    points=[(0.,y,angle) for y,angle in [(1.,0.),(2.,.05),(3.,.1),(4.,.2),(5.,.25),(6.,.3)]]
    raw=np.array([[0.,-1.],[0.,0.],[0.,1.]])
    asphalt=np.ones((84,84),np.uint8);blocked=np.zeros((84,84),bool)
    def run(p=points,road=asphalt,obstacles=blocked):
        return a.reference_from_observed_width(raw,[dict(points=p)],road,obstacles)
    result,info=run();assert len(result)==8 and result[-1,1]==6.,(result,info)
    cases=['visible_gap_joined']
    row=int(round(a.IMAGE_ORIGIN_Y-1.701*3.5))
    for name in ('grass','obstacle'):
        road=asphalt.copy();obstacles=blocked.copy()
        if name=='grass':road[row,:]=0
        else:obstacles[row,:]=True
        result,_=run(road=road,obstacles=obstacles);assert result[-1,1]==3.,(name,result)
        cases.append(name+'_break_retained')
    far=[(x,y+(4. if i>=3 else 0.),angle) for i,(x,y,angle) in enumerate(points)]
    result,_=run(p=far);assert result[-1,1]==3.;cases.append('tile_limit_retained')
    invalid=list(points);invalid.insert(3,(30.,3.5,.15))
    road=asphalt.copy();road[:,80:]=0
    result,_=run(p=invalid,road=road);assert result[-1,1]==3.;cases.append('explicit_unsupported_sample_break_retained')
    record=dict(status='PASS',cases=cases,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0)
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()

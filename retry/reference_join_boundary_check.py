"""Reference joins must use the same last visible row as the row collector."""
from pathlib import Path
import sys,json,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    def point(row):return (0.,(a.IMAGE_ORIGIN_Y-row)/1.701)
    raw=np.array([point(row) for row in (69.,67.,65.,63.)])
    curve=[(*point(row),i*.05) for i,row in enumerate((68.1,66.,64.,62.,60.,58.,56.,54.,52.))]
    road=np.ones((84,84),np.uint8);blocked=np.zeros((84,84),bool)
    def run(road=road,blocked=blocked,points=curve):
        return a.reference_from_observed_width(raw,[dict(points=points)],road,blocked)
    result,info=run();assert info['observed_width_reference_used'] and len(result)>len(raw)
    rejected=[]
    for material in ('missing_road','obstacle'):
        changed=road.copy();veto=blocked.copy()
        if material=='missing_road':changed[69,:]=0
        else:veto[69,:]=True
        _,info=run(changed,veto);assert not info['observed_width_reference_used']
        rejected.append(material)
    # A whole curve below the domain remains rejected. This boundary fix
    # admits no new pixel rows: previous values68.9 already read pixel69.
    far=[(*point(row),i*.05) for i,row in enumerate((72.,71.5,71.,70.5,70.1))]
    _,info=run(points=far);assert not info['observed_width_reference_used'];rejected.append('below_domain')
    record=dict(status='PASS',valid_last_row_join=True,rejections=rejected,model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu)
    out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))


if __name__=='__main__':main()

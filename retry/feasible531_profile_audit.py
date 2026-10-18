"""Describe three already saved endpoints; never select another candidate."""
import json,time
from pathlib import Path
import numpy as np
from retry.line530_control import rebuild,scalar_clock
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response531-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());history=json.loads((D/'design-history-private.json').read_text());budget=.70*sum(w['friction'] for w in s['root']['planar']['linear']['wheels'])/s['root']['planar']['linear']['mass'];out={}
    for name,p in [('baseline',paths['baseline']),('feasibility_endpoint',rebuild(history['restored_points'],s)),('performance_endpoint',paths['candidate'])]:
        ds=np.array(p['ds']);k=np.array(p['curvature']);h=np.sqrt(np.sqrt(k*k+1e-8)/budget+1./80.**2);out[name]=dict(length_m=p['length'],scalar_clock_s=scalar_clock(p),smooth_surrogate=float(sum(ds*(h+np.roll(h,-1))/2)),max_abs_curvature=float(max(abs(k))),curvature_squared_integral=float(sum(k*k*ds)),absolute_turn_rad=float(sum(abs(k)*ds)),curvature_total_variation=float(sum(abs(k-np.roll(k,1)))),periodic_min_speed_m_s=float(np.sqrt(min(p['periodic_squared']))),mean_periodic_speed_nodes_m_s=float(np.sqrt(p['periodic_squared']).mean()))
    out.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,scope='Read-onlysavedendpoints;notnewsearch/alternatecandidatepromotion. Smoothsurrogateomitslongitudinal/sourcegovernor;profileauditdescriptive,notcausalproof/timebound.')
    with (G/'retry/feasible531_profile_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()

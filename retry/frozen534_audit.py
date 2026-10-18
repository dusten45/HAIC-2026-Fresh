"""Read-only stopped-pose geometry and baseline replay audit; no integration."""
import hashlib,json,math,time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root,polygons
from retry.corner515_model import obstacle_margin
from retry.brake506_geometry import polygon_distance
from retry.brake508_corridor import inside
from retry.drive519_control import project,reference
from retry.response528_control import choose
from retry.frozen534_model import choose as active_choose
from retry.line530_design import HALF_WIDTH,HALF_LENGTH,SHIFT
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response534-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/frozen534_contract.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());cold=json.loads((D/'cold-candidate-model-private.json').read_text());trace=cold['trace'];last=trace[-1];state=dict(last['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state);path=paths['candidate'];projection=project(root.center,path,last['progress']);t=np.array(projection['tangent']);n=np.array([-t[1],t[0]]);pos=np.array(projection['point'])+SHIFT*t;nominal=np.array([pos+a*HALF_LENGTH*t+b*HALF_WIDTH*n for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]).tolist()
    def roadgap(poly):
        d=min(polygon_distance(poly,[tuple(a),tuple(b)]) for a,b in static['boundary']);covered=all(any(inside(v,p) for p,mu in static['roads']) for v in poly);return d if covered else -d
    rows=[]
    for i,poly in enumerate(polygons(root)):
        road=roadgap(poly);obstacle=obstacle_margin([poly],static['obstacles']);rows.append(dict(part=('hull'+str(i+1)) if i<4 else ('wheel'+str(i-3)),road_margin_m=road,obstacle_margin_m=obstacle,margin_m=min(road,obstacle)))
    minimum=min(rows,key=lambda x:x['margin_m']);heading=math.atan2(-float(t[0]),float(t[1]));target,ff=reference(last['progress'],path);command=cold['commands'][-1]['detail'];reports=command.get('reports',[]);selected=next((r for r in reports if r.get('mode')=='FINAL'),reports[0] if reports else {})
    cache=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json').read_text());lookup={(x['index'],x['raw']):x for x in cache['trace']};baseline=[]
    for name in ('obstacle','curvature'):
        data=json.loads((D/f'probe-{name}-baseline-private.json').read_text());equal=[x['root_without_roads']==lookup[(x['index'],x['raw'])]['root_without_roads'] for x in data['trace']];baseline.append(dict(label=name,raw_rows=len(equal),root_states_identical_to_cached528=sum(equal),all_identical=all(equal)))
    sourcepins=all(hashlib.sha256((G/z).read_bytes()).hexdigest()==h for z,h in c['source_sha256'].items());privatepins=all(hashlib.sha256(Path(z).read_bytes()).hexdigest()==h for z,h in c['private_inputs_sha256'].items());assert sourcepins and privatepins and active_choose is choose;assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==c['fixed_path_sha256'];assert not (D/'NATIVE_STARTED.json').exists()
    window=[dict(action_index=x['index'],raw=x['raw'],margin_m=x['margin'],path_error_m=x['path_error'],speed_m_s=math.hypot(*load_root(dict(x['root_without_roads'],roads=static['root']['roads'])).planar.linear.velocity),target_m_s=x['target']) for x in trace[-8:]]
    out=dict(first_failure=cold['summary']['first_failure'],limiting_part=minimum,all_body_parts=rows,actual_pose_margin_m=last['margin'],actual_pose_path_error_m=last['path_error'],actual_pose_heading_minus_segment_rad=math.remainder(root.planar.angle-heading,2*math.pi),speed_m_s=math.hypot(*root.planar.linear.velocity),reference_m_s=target,reference_ff_m_s2=ff,nominal_outerbox_at_same_projection=dict(road_margin_m=roadgap(nominal),obstacle_margin_m=obstacle_margin([nominal],static['obstacles'])),last_control_mode=command['mode'],attempted_forecasts_max_force_peak=max((r['peak'] for r in reports),default=None),selected_final_forecast_force_peak=selected.get('peak'),selected_final_forecast_reference_overspeed=selected.get('max_reference_overspeed'),selected_final_certified=selected.get('ok'),last_two_holds_summary=dict(raw_samples=len(window),previous_hold_end_margin_m=window[3]['margin_m'],previous_hold_end_path_error_m=window[3]['path_error_m'],failed_hold_end_margin_m=window[-1]['margin_m'],failed_hold_end_path_error_m=window[-1]['path_error_m']),baseline_replay=baseline,source_pins_verified=sourcepins,private_input_pins_verified=privatepins,controller_function_identity=True,fixed533_path_SHA_unchanged=True,path_optimization_iterations=0,extra_model_ticks=0,extra_force_evaluations=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='Stoppedposegeometrydiagnosticnotnewtrajectory/counterfactualphysics. Shared528forecastchecksforce/ref/pathbutnotwhole-bodymargin;staticnominal1.25isnottrackinginvariance. Noactualfinish/gainclaim.')
    with (D/'audit-last8-private.json').open('x') as f:json.dump(window,f,indent=2)
    with (G/'retry/frozen534_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()

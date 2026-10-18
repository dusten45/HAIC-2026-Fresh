"""Saved541 minimum-margin pose ablations and prior contract mismatch; no physics."""
import datetime,hashlib,json,math,signal,time
from dataclasses import replace
from pathlib import Path
from retry.plan513_model import load_root
from retry.lap518_control import project
from retry.structure537_control import geometry_context
from retry.corner515_model import margin

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');O=Path('/workspace/haic-response544-private');O.mkdir(mode=0o700,exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));paths=read(D/'frozen-paths-private.json');path=paths['candidate'];full=read(D/'native-full-records-private.json');split=51+sum(r['raw_ticks'] for r in full[0]['rows']);rows=[read(p) for p in sorted(D.glob('raw-*.json'))][split:];rows=[r for r in rows if r['phase']=='action'];r=min(rows,key=lambda z:z['margin']);a=read(D/f"action-candidate-{r['action']:03d}.json");raws=[z for z in rows if z['action']==r['action']];k=raws.index(r);state=a['after_root_without_roads'] if k==len(raws)-1 else None
 # The minimum is at the hold end; match exact saved state before any pose change.
 assert state is not None
 root=load_root(dict(state,roads=static['root']['roads']));q=project(root.center,path,r['station']);t=q['tangent'];normal=(-t[1],t[0]);error=sum((root.center[j]-q['point'][j])*normal[j] for j in range(2));angle=math.atan2(-t[0],t[1]);delta=math.remainder(angle-root.planar.angle,2*math.pi);geometry=geometry_context(static)
 def rot(x):return (math.cos(delta)*x[0]-math.sin(delta)*x[1],math.sin(delta)*x[0]+math.cos(delta)*x[1])
 def gap(z):return margin(z,geometry['roads'],geometry['road_index'],geometry['boundary'],geometry['edge_index'],geometry['obstacles'])
 aligned=replace(root,planar=replace(root.planar,angle=root.planar.angle+delta,levers=tuple(rot(x) for x in root.planar.levers),linear=replace(root.planar.linear,wheels=tuple(replace(w,heading=w.heading+delta) for w in root.planar.linear.wheels))))
 poses=dict(actual=gap(root),position_on_reference_keep_actual_orientation=gap(replace(root,center=q['point'])),orientation_to_reference_keep_actual_center=gap(aligned),position_and_orientation_on_reference=gap(replace(aligned,center=q['point'])))
 before=read(D/'action-candidate-055.json');past=[z for z in rows if 24<z['action']<55];entry=dict(index=55,completed=54,history=[sum(z['ratio']>1 for z in past for z in z['forces']),4*len(past)],root=before['before_root_without_roads'])
 with (O/'entry-root-private.json').open('x') as f:json.dump(entry,f)
 with (O/'bias-evidence-private.json').open('x') as f:json.dump(dict(station=q['s'],normal_error=error,tangent=t,reference_point=q['point'],actual_root=state,all_candidate_actual_rows=rows),f)
 out=dict(status='SAVED541_DYNAMIC_GEOMETRY_DIAGNOSIS',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),minimum_action=r['action'],minimum_sample_at_hold_end=True,signed_normal_tracking_error_m=error,body_minus_reference_heading_rad=-delta,pose_only_clearance_m=poses,interpretation='Pose ablations are geometric counterfactuals only, not realizable dynamics or additive effects. Select one local counter-bias reference shape, then measure source-model common-plane time and terminal safety rather than static surrogate.',prior_failures=dict(smooth531='surrogate14.746595 but scalar18.580911 vs17.250273 baseline',joint532_533='time objective/primal feasibility do not establish converged or physical optimum',dynamic534='nominal box1.608604 vs dynamic wheel.437175; position error1.250157 plus heading-.120377rad; force/pathdistance alone insufficient'),new_model_ticks=0,new_native_actions=0,geometry_pose_checks=4,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,source_sha256={str(p):sha(p) for p in [G/'retry/feasible531_result.md',G/'retry/joint532_result.md',G/'retry/joint533_result.md',G/'retry/frozen534_result.md',G/'retry/frozen534_audit.json',D/'native-full-records-private.json']})
 with (G/'retry/bias544_analysis.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()

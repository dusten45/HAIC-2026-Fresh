"""Static world-stationarity and strict-boundary summaries from saved evidence."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.lineage339_stage import verify
from retry.lineage339_audit import rotation,centers,pixels


def compare(records):
    output=[]
    for row in records:
        variants=row['probe']['variants'];base=variants['original'];result=dict(stage=row['stage'],step=row['step'],variants={})
        for mode,v in variants.items():
            if mode=='original':continue
            f=np.array(v['features']);bf=np.array(base['features'])
            result['variants'][mode]=dict(removed_count=len(base['hazards'])-len(v['hazards']),candidates_changed=v['candidates']!=base['candidates'],path_changed=v['path']!=base['path'],target_changed=v['target']!=base['target'],steering_changed=v['action'][0]!=base['action'][0],pedals_changed=v['action'][1:]!=base['action'][1:],connection_evaluation_changed=v['connection_evaluation']!=base['connection_evaluation'],changed_feature_indices=np.flatnonzero(f!=bf).tolist(),action_delta=(np.array(v['action'])-base['action']).tolist(),feature_delta=(f-bf).tolist(),target_delta=None if v['target'] is None or base['target'] is None else (np.array(v['target'])-base['target']).tolist(),candidate_counts=[len(base['candidates']),len(v['candidates'])])
        output.append(result)
    return output


def run(R):
    D=R/'stage339';verify(R,True);assert read(D/'routing-only-receipt.json')['passed'];assert not (D/'context-private.json').exists();start,cpu=time.perf_counter(),time.process_time();lineages=read(D/'lineage-private.json');out={};comparisons=[]
    for stage in [337,338]:
        rows=[json.loads(s) for s in (R/f'stage{stage}/B/trace-private.jsonl').read_text().splitlines()];lr=lineages[str(stage)]['records'];samples=[]
        for tag in ['121:0','124:0']:
            birth=int(tag.split(':')[0]);entry=lr[birth-1];index=entry['tags'].index(tag);p=rows[birth-1]['tracker']['after'][index];h=rows[birth-1]['pre_physical']['hull'];origin=rotation(h['angle'])@p[:2]+h['position']
            points=[]
            for r,rec in zip(rows,lr):
                if tag not in rec['tags']:continue
                point=r['tracker']['after'][rec['tags'].index(tag)];h=r['pre_physical']['hull'];world=rotation(h['angle'])@point[:2]+h['position'];expected=rotation(-h['angle'])@(origin-h['position']);gt=centers(r['pre_physical'])
                points.append(dict(step=r['step'],age=point[3],world_stationarity_drift_m=float(np.linalg.norm(world-origin)),birth_world_point_reprojected=expected.tolist(),actual=point[:2],nearest_GT_distance_m=float(np.min(np.linalg.norm(gt-point[:2],axis=1)))))
            samples.append(dict(tag=tag,birth_point_nearest_GT_distance_m=points[0]['nearest_GT_distance_m'],points=points,maximum_world_drift_through128_m=max(q['world_stationarity_drift_m'] for q in points if q['step']<=128),maximum_world_drift_lifetime_m=max(q['world_stationarity_drift_m'] for q in points)))
        current=[]
        for r in rows[123:132]:
            gt=centers(r['pre_physical']);direct=r['tracker']['direct'];dist=[float(np.linalg.norm(np.array(p[:2])-gt[2])) for p in direct];j=int(np.argmin(dist));pd=float(np.linalg.norm(pixels(np.array(direct[j][:2]))-pixels(gt[2])));current.append(dict(step=r['step'],metric_error_m=dist[j],projection_centroid_error_px=pd))
        out[str(stage)]=dict(lineages=samples,current_contact_object_correspondence=current)
        comparisons+=compare(read(D/f'routing-only/{stage}/probes-private.json'))
    verify(R,True)
    save(D/'context-private.json',dict(data=out,strict_routing_comparisons=comparisons,
        caveat='Stationarity assumes a fixed birth world point, not a known physical object. Small drift cannot establish correct semantic birth or true occlusion. No pose used by actor.',
        cost=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu)))
    print(json.dumps(dict(data={s:dict(world_drift_through128=[v['maximum_world_drift_through128_m'] for v in d['lineages']],direct_error_range=[min(v['metric_error_m'] for v in d['current_contact_object_correspondence']),max(v['metric_error_m'] for v in d['current_contact_object_correspondence'])]) for s,d in out.items()},strict_changed={str(s):{m:{k:[q['step'] for q in comparisons if q['stage']==s and q['variants'][m][k]] for k in ['candidates_changed','path_changed','target_changed','steering_changed','pedals_changed']} for m in ['drop_birth121','drop_birth124','current_only']} for s in [337,338]})),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)

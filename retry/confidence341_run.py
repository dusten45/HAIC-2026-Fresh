"""Observed chronology and legal detection-feature distributions, no new rollout."""
import argparse
import ast
import hashlib
import json
import time
from pathlib import Path
import cv2
import numpy as np
from retry.path271_run import read,save
from retry.confidence341_stage import verify
from retry.lineage339_audit import components,centers,pixels,rotation
from retry.fallback334_math import advance


def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def observations(case):
    records=rows(case['records']);z=np.load(case['pixels'])
    if case['format']=='334':
        obs=z['observations'][:len(records)];assert np.array_equal(obs[1:,:3],obs[:-1,1:]);frames=np.rint(obs[:,-1]*255).astype(np.uint8);assert np.array_equal(frames.astype(np.float32)/255,obs[:,-1]);gt={int(k):v for k,v in read(case['GT']).items()}
    else:frames=z['frames_uint8'][:len(records)];gt={i:r['pre_physical'] for i,r in enumerate(records)}
    assert len(frames)==len(records)
    return frames,records,gt


def feature_maps(frame):
    image=frame.astype(np.float32)/255;road=((image>.32)&(image<.47)).astype(np.uint8);road[61:]=0;closed=cv2.morphologyEx(road,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));_,labels=cv2.connectedComponents(closed,connectivity=8)
    x=np.flatnonzero(closed[56]);ego=int(labels[56,x[np.argmin(abs(x-42))]]) if len(x) else None
    return road,closed,labels,ego


def features(c,frame,maps):
    road,closed,labels,ego=maps;xy=np.array(c['pixel_xy']);mask=np.zeros((84,84),np.uint8);mask[xy[:,1],xy[:,0]]=1;ring=(cv2.dilate(mask,np.ones((3,3),np.uint8))!=0)&(mask==0);wide=cv2.dilate(mask,np.ones((7,7),np.uint8))!=0
    x,y,w,h=c['bbox'];gray=frame[xy[:,1],xy[:,0]]
    return dict(area=c['area'],width=w,height=h,aspect=float(w/h),cx=c['centroid'][0],cy=c['centroid'][1],touch_boundary=bool(x==0 or y==0 or x+w==84 or y+h==61),touch_top=bool(y==0),gray_mean=float(gray.mean()),gray_range=float(np.ptp(gray)),raw_road_ring_fraction=float(road[ring].mean()),raw_road_wide_fraction=float(road[wide].mean()),closed_connected_ego=bool(ego is not None and np.any(labels[xy[:,1],xy[:,0]]==ego)))


def label(point,gt):
    if gt is None:return 'missing_GT',None
    distance=np.linalg.norm(centers(gt)-point[:2],axis=1);inside=[i for i,d in enumerate(distance) if d<=gt['obstacles'][i]['fixture']['radius']]
    return ('fixture_supported',inside[0]) if len(inside)==1 else ('unresolved',None)


def polyline_distance(path,point):
    if not path:return None
    path=np.asarray(path,float);p=np.asarray(point,float);values=[float(np.linalg.norm(v-p)) for v in path]
    for a,b in zip(path[:-1],path[1:]):
        delta=b-a;den=float(delta@delta)
        if den:values.append(float(np.linalg.norm(a+np.clip((p-a)@delta/den,0,1)*delta-p)))
    return min(values)


def chronology(R):
    G=Path(__file__).resolve().parent.parent;constants={}
    for node in ast.parse((G/'core/vendor/car_dynamics.py').read_text()).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['SIZE','HULL_POLY1','HULL_POLY2','HULL_POLY3','HULL_POLY4']:constants[node.targets[0].id]=ast.literal_eval(node.value)
    polygons=[np.asarray(constants[f'HULL_POLY{i}'],np.float32)*constants['SIZE'] for i in range(1,5)]
    source={s:rows(R/f'stage{s}/B/trace-private.jsonl') for s in [337,340]};out=[]
    for step in range(124,141):
        item=dict(step=step,phase='pre-intervention' if step<127 else 'routing intervention' if step<=129 else 'own-observation aftermath',arms={})
        for stage in [337,340]:
            r=source[stage][step-1];pre=r['pre_physical'];post=r['post_physical'];f=r['features'];center=centers(pre)[2];radius=pre['obstacles'][2]['fixture']['radius'];pre_gap=min(-cv2.pointPolygonTest(poly,tuple(map(float,center)),True)-radius for poly in polygons);pc=centers(post)[2];post_gap=min(-cv2.pointPolygonTest(poly,tuple(map(float,pc)),True)-radius for poly in polygons)
            item['arms'][str(stage)]=dict(path=r['pixel_path'],target=f[1:3],target_speed=f[6],path_length=f[9],controls=r['executed'],nominal_memory=r['nominal_memory'],previous_memory=f[7],pre_position=pre['hull']['position'],post_position=post['hull']['position'],pre_angle=pre['hull']['angle'],post_angle=post['hull']['angle'],pre_speed=r['pre']['speed_m_s'],post_speed=r['post']['speed_m_s'],pre_hull_fixture_gap_m=pre_gap,post_hull_fixture_gap_m=post_gap,planned_path_center_distance_m=polyline_distance(r['pixel_path'],center),tiles=r['post']['unique_tiles'],collision=r['collision'],touching=post['touching_obstacle_contacts'],filtered_count=len(r.get('routing_filter',{}).get('removed',[])))
        a=item['arms']['337'];b=item['arms']['340'];item['differences']=dict(path=a['path']!=b['path'],path_length=a['path_length']!=b['path_length'],target=a['target']!=b['target'],target_speed=a['target_speed']!=b['target_speed'],pedals=a['controls'][1:]!=b['controls'][1:],steering=a['controls'][0]!=b['controls'][0],nominal_memory=a['nominal_memory']!=b['nominal_memory'],pre_position=a['pre_position']!=b['pre_position'],pre_speed=a['pre_speed']!=b['pre_speed'],post_position=a['post_position']!=b['post_position'],pre_position_distance_m=float(np.linalg.norm(np.array(a['pre_position'])-b['pre_position'])),post_position_distance_m=float(np.linalg.norm(np.array(a['post_position'])-b['post_position'])))
        out.append(item)
    first={k:next((q['step'] for q in out if q['differences'][k]),None) for k in ['path','path_length','target','target_speed','pedals','steering','nominal_memory','pre_position','pre_speed','post_position']}
    return dict(records=out,first_difference=first,gap_scope='Analytic hull fixture polygons vs captured obstacle2circle at action endpoints; excludes wheel shapes/Box2D polygon skin/swept intra-action minimum. Source constants parsed as data, no physics imported or advanced.',causal_scope='Only127input is same pre-intervention scene.128+inputs include previous whole-control effects;127-129routing exclusion then130+endogenous policy/memory/physical continuation. No independent pedal/speed/steer attribution.')


def distribution(data):
    out={}
    for group in ['original6','N2']:
        out[group]={}
        for lab in ['fixture_supported','unresolved','missing_GT']:
            rr=[r for r in data if r['group']==group and r['label']==lab];first=[r for r in rr if not r['past_redetected']]
            quant={}
            for k in ['area','width','height','aspect','cx','cy','gray_mean','gray_range','raw_road_ring_fraction','raw_road_wide_fraction','past_consecutive_direct']:
                values=[r['features'][k] for r in rr]
                quant[k]=dict(min=float(min(values)),p25=float(np.quantile(values,.25)),median=float(np.median(values)),p75=float(np.quantile(values,.75)),max=float(max(values))) if values else None
            out[group][lab]=dict(count=len(rr),roads=len(set(r['road'] for r in rr)),first_sighting_count=len(first),touch_boundary_count=sum(r['features']['touch_boundary'] for r in rr),first_sighting_touch_boundary_count=sum(r['features']['touch_boundary'] for r in first),connected_ego_count=sum(r['features']['closed_connected_ego'] for r in rr),past_redetected_count=sum(r['past_redetected'] for r in rr),future_redetected_count=sum(r['future_redetected'] for r in rr),quantiles=quant,
                first_sighting_area_counts={str(v):sum(r['features']['area']==v for r in first) for v in sorted(set(r['features']['area'] for r in first))})
    return out


def run(R):
    D=R/'stage341';p=verify(R);assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));start,cpu=time.perf_counter(),time.process_time();chron=chronology(R);save(D/'chronology-private.json',chron)
    inventory=[];detections=[];retained=[];all_nodes={};context_keys=set();reconstruction_max=0.;input_count=0;appearance={};context_rows=[]
    for case in p['cases']:
        frames,records,gt=observations(case);tags=[];previous=[];nodes={};maxerr=0.;case_detections=[];case_retained=[]
        for i,(frame,r) in enumerate(zip(frames,records)):
            t=r['tracker'];assert t['before']==previous;comp=components(frame);assert [c['metric'] for c in comp]==t['direct'];input_count+=1
            rebuilt,lineage,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],case['fallback']);a=np.asarray(rebuilt).reshape(-1,4);b=np.asarray(t['after']).reshape(-1,4);assert a.shape==b.shape
            err=float(np.max(abs(a-b))) if a.size else 0.;assert err<1e-10;maxerr=max(maxerr,err)
            pending=[dict(tag=tag,predicted=point) for tag,point,old in zip(tags,transported,t['before']) if old[3]<8 and abs(point[0])<=35 and -5<=point[1]<=35]
            fh=hashlib.sha256(frame.tobytes()).hexdigest();ch=digest([t['before'],t['affine'],t['after']]);maps=feature_maps(frame);current_labels=[]
            for j,c in enumerate(comp):
                uid=f"{case['key']}:{i}:{j}";parents=[];keep=[]
                for old in pending:
                    if np.hypot(old['predicted'][0]-c['metric'][0],old['predicted'][1]-c['metric'][1])<=2:parents.append(old)
                    else:keep.append(old)
                pending=keep+[dict(tag=uid,predicted=c['metric']+[0])]
                for parent in parents:nodes[parent['tag']]['future_redetected']=True
                lab,identity=label(c['metric'],gt.get(i));current_labels.append(identity);f=features(c,frame,maps)
                streak=1+max((nodes[q['tag']]['features']['past_consecutive_direct'] for q in parents if q['predicted'][3]==1),default=0);f['past_consecutive_direct']=streak
                n=dict(uid=uid,case=case['key'],road=case['road'],group=case['group'],step=i+1,direct_index=j,frame_hash=fh,context_hash=ch,features=f,label=lab,supported_id=identity,past_redetected=bool(parents),parent_tags=[q['tag'] for q in parents],past_redetection_gap=min((q['predicted'][3] for q in parents),default=None),future_redetected=False,appearance_key=f"{case['road']}:{fh}:{j}",context_key=f"{case['road']}:{fh}:{ch}:{j}")
                nodes[uid]=n;case_detections.append(n)
            aftertags=[q['tag'] for q in pending];assert len(aftertags)==len(t['after']);assert all((lineage[j]<0 and aftertags[j]==f"{case['key']}:{i}:{-lineage[j]-1}") or (lineage[j]>=0 and aftertags[j]==tags[lineage[j]]) for j in range(len(aftertags)))
            for point,tag in zip(t['after'],aftertags):
                if point[3]==0:continue
                node=nodes[tag];identity=node['supported_id'];g=gt.get(i);in_roi=None;error=None
                if identity is not None and g is not None:
                    center=centers(g)[identity];pixel=pixels(center);in_roi=bool(0<=pixel[0]<84 and 0<=pixel[1]<61);error=float(np.linalg.norm(np.array(point[:2])-center))
                case_retained.append(dict(case=case['key'],road=case['road'],group=case['group'],step=i+1,tag=tag,age=point[3],label_at_birth=node['label'],birth_first_sighting=not node['past_redetected'],birth_consecutive_direct=node['features']['past_consecutive_direct'],birth_touch_boundary=node['features']['touch_boundary'],supported_id=identity,GT_at_current=g is not None,geometric_roi=in_roi,without_current_fixture_supported_direct=bool(identity is not None and identity not in current_labels),current_birth_identity_error_m=error,context_key=f"{case['road']}:{fh}:{ch}:{aftertags.index(tag)}"))
            tags=aftertags;previous=t['after']
        all_nodes.update(nodes);detections+=case_detections;retained+=case_retained;reconstruction_max=max(reconstruction_max,maxerr)
        inventory.append(dict(key=case['key'],road=case['road'],inputs=len(records),GT_input_boundaries=len(gt),direct_detections=len(case_detections),retained_point_observations=len(case_retained),detector_exact=True,tracker_reconstruction_max_error=maxerr))
        print(json.dumps(inventory[-1]),flush=True)
    # Prefer actual GT availability, then fixed registration order, without a
    # semantic label or output-dependent selection criterion.
    for n in detections:
        key=n['appearance_key'];old=appearance.get(key)
        if old is None or old['label']=='missing_GT' and n['label']!='missing_GT':appearance[key]=n
        if n['context_key'] not in context_keys:context_keys.add(n['context_key']);context_rows.append(n)
    dedup=list(appearance.values());retained_unique={}
    for q in retained:
        key=q['context_key'];old=retained_unique.get(key)
        if old is None or old['label_at_birth']=='missing_GT' and q['label_at_birth']!='missing_GT':retained_unique[key]=q
    retention={}
    for group in ['original6','N2']:
        retention[group]={}
        for lab in ['fixture_supported','unresolved','missing_GT']:
            rr=[q for q in retained_unique.values() if q['group']==group and q['label_at_birth']==lab]
            retention[group][lab]=dict(point_observations=len(rr),unique_births=len(set(q['tag'] for q in rr)),supported_without_current_direct_in_geometric_ROI=sum(q['without_current_fixture_supported_direct'] and q['geometric_roi'] is True for q in rr),unconfirmed_birth_point_observations=sum(q['birth_first_sighting'] for q in rr),age_counts={str(a):sum(q['age']==a for q in rr) for a in range(1,9)},actual_visibility_labels=0,actual_occlusion_labels=0)
    focal=[]
    for step in [121,124]:
        n=next(q for q in detections if q['case']=='N2_337' and q['step']==step and q['direct_index']==0);signature_keys=['area','width','height','touch_boundary','closed_connected_ego','past_consecutive_direct'];signature={k:n['features'][k] for k in signature_keys};matches=[q for q in dedup if q['label']=='fixture_supported' and all(q['features'][k]==v for k,v in signature.items())]
        focal.append(dict(birth_action=step,features=n['features'],past_redetected=n['past_redetected'],future_redetected=n['future_redetected'],signature=signature,fixture_supported_exact_coarse_signature_matches=len(matches),match_roads=sorted(set(q['road'] for q in matches))))
    verify(R)
    import sys
    assert not any(n.split('.')[0] in ['Box2D','core','gym','gymnasium','env_wrapper'] for n in sys.modules)
    cost=dict(new_native_actions=0,new_environment_resets=0,new_actor_calls=0,new_learning_fits=0,parameter_sweeps=0,new_source_physics_ticks=0,existing_input_frames_processed=input_count,detector_reconstruction_calls=input_count,tracker_algebra_reconstruction_calls=input_count,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu)
    output=dict(inventory=inventory,raw_detection_count=len(detections),appearance_deduplicated_detection_count=len(dedup),context_deduplicated_detection_count=len(context_rows),retained_raw_point_observations=len(retained),retained_context_deduplicated_point_observations=len(retained_unique),tracker_reconstruction_max_error=reconstruction_max,appearance_distributions=distribution(dedup),context_distributions=distribution(context_rows),retention=retention,focal_comparison=focal,chronology_first_differences=chron['first_difference'],cost=cost,
        limits=['Fixture-center compatibility is diagnostic geometric support, not semantic truth. All other/missing births remain unresolved, never false-positive negatives.',
                'Future redetection is descriptive only, forbidden as a causal online feature. Past count uses existing source association only, not GT IDs.',
                'No authoritative visibility/occlusion labels or RGB/material truth. Nondetection is not occlusion; in-ROI is not visible.',
                'Selected compatible TRAIN subset with shared N2 histories, not exhaustive corpus or independent samples. No missing frames synthesized.'])
    save(D/'detections-private.json',detections);save(D/'appearance-deduplicated-private.json',dedup);save(D/'context-deduplicated-private.json',context_rows);save(D/'retained-private.json',list(retained_unique.values()));save(D/'analysis-private.json',output)
    print(json.dumps(dict(first_differences=chron['first_difference'],cost=cost,focal=focal,appearance_counts={g:{lab:d['count'] for lab,d in v.items()} for g,v in output['appearance_distributions'].items()})),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)

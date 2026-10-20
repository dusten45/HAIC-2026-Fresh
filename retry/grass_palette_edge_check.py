"""Public-renderer regressions for the dual grass/asphalt palette fallback.

Synthetic original public road/checker polygons only. No saved image, map,
case parameters, simulator or physics step is read. Supply a prior source
revision to check that successful legacy support is never expanded. A feasible
dualpalette may tighten it inward; physical-road inclusion remains strict.
"""
import argparse
import ast
import hashlib
import itertools
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'submit_core'),str(ROOT)]
import observation_agent as candidate
from retry.observed_track_tiles import (generate_tile_layers,grass_checker_layers,local_nodes,
    GRASS_DIM,PUBLIC_ZOOM)
from retry.raw_boundary_renderer import render_scene


def legacy_functions(revision):
    source=subprocess.run(['git','show',revision+':submit_core/observation_agent.py'],
        cwd=ROOT,check=True,capture_output=True,text=True).stdout
    names={'recover_pixel_edge','recover_plain_run_edge','recover_shaded_run_edge'}
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name in names]
    if {n.name for n in nodes}!=names:raise ValueError('Legacy functions missing')
    namespace=dict(np=np,math=math,cv2=cv2)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<legacy public edge inversion>','exec'),namespace)
    return namespace


def inside(point,polygon):
    cross=[(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
        for a,b in zip(polygon,polygon[1:]+polygon[:1])]
    return min(cross)>=-1e-9 or max(cross)<=1e-9


def point_segment(point,a,b):
    d=np.asarray(b)-a;p=np.asarray(point)-a
    t=float(np.clip(p@d/(d@d),0,1))if d@d else 0.
    return float(np.linalg.norm(p-t*d))


def runs(image,row):
    mask=(image[row]>.36)&(image[row]<.47)
    change=np.diff(np.pad(mask.astype(np.int8),(1,1)))
    return [(int(a),int(b))for a,b in zip(np.flatnonzero(change==1),np.flatnonzero(change==-1))if b-a>=8]


def check(revision,cpu_limit=150,extended=False):
    cpu=time.process_time();legacy=legacy_functions(revision)
    if not hasattr(candidate,'recover_grass_palette_edge'):raise ValueError('Candidate helper unavailable')
    counts=dict(scenes=0,queries=0,accepted=0,new_fallback_accepted=0,
        legacy_accepted_unchanged=0,legacy_tightened=0,legacy_rejected=0,
        physical_outside=0,new_physical_outside=0,
        legacy_physical_outside=0,negative_rejections=0)
    failures=[];negative=[];samples=[]
    no_block=np.zeros((84,84),bool);no_paint=np.zeros_like(no_block)
    headings=(-.55,-.18,.21,.58)
    families=[(h,(0.,)*15,False)for h in headings]
    if extended:
        families += [(h,(0.,)*15,True)for h in(-1.25,-.9,0.,.9,1.25)]
        families += [(0.,(0.,.15,.15,0.,-.15,-.15,0.,.15,.15,0.,-.15,-.15,0.,0.,0.),True)]
    family_queries={str(i):0 for i in range(len(families))}
    angles=(-.71,.13,.83)
    phases=(.07,.43,.91)
    for family_id,angle,phase,road_phase,raster_phase in itertools.product(
            range(len(families)),angles,phases,range(3),(.05,.47,.91)):
        if time.process_time()-cpu>cpu_limit:raise RuntimeError('CPU_LIMIT: incomplete suite')
        heading,turns,centered=families[family_id]
        center=(500.+raster_phase,65.+2*raster_phase)
        if centered:
            reference=local_nodes((0.,0.),heading,turns)[3]['raw_center']
            center=(500.-reference[0]+raster_phase,430.-reference[1]+2*raster_phase)
        model=generate_tile_layers(center,heading,turns,index_phase6=road_phase,
            contact_reset_flags=[False]*14,border_flags=[False]*14)
        grass=grass_checker_layers(world_to_body_angle=angle,
            world_to_body_translation=(phase*2*GRASS_DIM,(1-phase)*2*GRASS_DIM))
        layers=[(q['original_vertices'],tuple(q['rgb_lo']))for q in grass+model['layers']]
        image=render_scene(layers,background=(102,204,102)).astype(np.float32)/255.
        physical=[q['original_vertices']for q in model['layers']if q['kind']=='road']
        counts['scenes']+=1
        for row in np.linspace(14,48,7,dtype=int):
            for start,end in runs(image,int(row)):
                if start<5 or end>79:continue
                interval=(start,end)
                for index,direction in ((start,1),(end-1,-1)):
                    counts['queries']+=1
                    family_queries[str(family_id)]+=1
                    old=legacy['recover_plain_run_edge'](image,int(row),index,direction,no_block,no_paint,interval)
                    new=candidate.recover_plain_run_edge(image,int(row),index,direction,no_block,no_paint,interval)
                    if old is not None:
                        if new is None:counts['legacy_rejected']+=1
                        elif direction*(new-old)<0:
                            failures.append(dict(kind='LEGACY_SUPPORT_EXPANDED',old=old,new=new,direction=direction))
                        elif new==old:counts['legacy_accepted_unchanged']+=1
                        else:counts['legacy_tightened']+=1
                    if new is None:continue
                    counts['accepted']+=1
                    # The submission applies .35m along image/body x, not
                    # normal distance. Check this exact contracted inset.
                    source_x=(float(new)+.5)*1000/84-.5+direction*.35*PUBLIC_ZOOM
                    source_y=799.-((int(row)+.5)*800/84-.5)
                    contained=any(inside((source_x,source_y),polygon)for polygon in physical)
                    if not contained:
                        counts['physical_outside']+=1
                        counts['legacy_physical_outside'if old is not None else'new_physical_outside']+=1
                        distance=min(point_segment((source_x,source_y),a,b)for polygon in physical
                            for a,b in zip(polygon,polygon[1:]+polygon[:1]))
                        failures.append(dict(kind='INSET_OUTSIDE_PHYSICAL_ROAD',heading=heading,
                            checker_angle=angle,phase=phase,road_phase=road_phase,
                            raster_phase=raster_phase,
                            family_id=family_id,
                            row=int(row),direction=direction,old=old,new=new,
                            outside_distance_source_pixels=distance,
                            outside_distance_m=distance/PUBLIC_ZOOM))
                    if old is None:
                        counts['new_fallback_accepted']+=1
                        if len(samples)<12:samples.append(dict(heading=heading,checker_angle=angle,
                            checker_phase=phase,road_phase=road_phase,row=int(row),direction=direction,
                            returned_edge=float(new),after_inset_inside=contained))
                    # Vetoes are checked on actual rendered positive windows.
                    if len(negative)<48:
                        blocked=np.ones_like(no_block);paint=np.ones_like(no_paint)
                        for name,b,p in (('blocked',blocked,no_paint),('paint_veto',no_block,paint)):
                            result=candidate.recover_plain_run_edge(image,int(row),index,direction,b,p,interval)
                            negative.append(dict(kind=name,rejected=result is None))
        # No need to keep full synthetic arrays after their direct checks.
    # Explicit material/visibility negatives cover last-two plateau and range
    # contradictions, alongside real rendered blocked/paint tests above.
    row=20;index=40;direction=1
    patterns={
        'pure_grass':[160,175,160,175,160,175,160,175],
        'paint_mix':[255,76,255,76,255,76,255,76],
        'occlusion':[160,170,160,0,100,100,100,100],
        'narrow_road':[160,175,160,100,100,160,175,160],
    }
    for name,values in patterns.items():
        image=np.full((84,84),160/255.,np.float32)
        image[row,index+np.arange(-3,5)]=np.asarray(values,np.float32)/255.
        result=candidate.recover_grass_palette_edge(image,row,index,direction,no_block)
        negative.append(dict(kind=name,rejected=result is None))
    counts['negative_rejections']=sum(q['rejected']for q in negative)
    if not counts['new_fallback_accepted']:failures.append(dict(kind='NO_NEW_PALETTE_PATH_EXERCISED'))
    if not all(family_queries.values()):failures.append(dict(kind='UNEXERCISED_GEOMETRY_FAMILY'))
    if counts['negative_rejections']!=len(negative):failures.append(dict(kind='NEGATIVE_ACCEPTED'))
    return dict(status='PASS'if not failures else'FAIL',counts=counts,
        new_fallback_physical_inset_status='PASS'if not counts['new_physical_outside']else'FAIL',
        failures=failures,negative_cases=negative,new_fallback_examples=samples,
        CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        source_revision_legacy=revision,gray_tolerance_changed=False,
        candidate_source_sha256=hashlib.sha256(Path(candidate.__file__).read_bytes()).hexdigest(),
        extended_geometry=extended,family_query_counts=family_queries,
        legacy_contract='NEVER_EXPANDED: feasible dualpalette may tighten existing edges inward; fullphysicaloutside0 remains mandatory.',
        scope='Finite original public tile/checker geometry regressions; no universal geometry proof or actual-input support promotion.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baseline-revision',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--cpu-limit',type=float,default=150)
    parser.add_argument('--extended',action='store_true')
    args=parser.parse_args();result=check(args.baseline_revision,args.cpu_limit,args.extended)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k not in('negative_cases','new_fallback_examples')}))
    raise SystemExit(0 if result['status']=='PASS'else 1)

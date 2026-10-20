"""Synthetic current-pixel regressions for strict bracketed flank bridging.

No saved observation, hidden map or simulator is used. These cases test the
finite component/anchor contract; they are not a proof of hidden pavement.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'submit_core'),str(ROOT)]
import observation_agent as a


def fixture(count=1,gray=100.):
    first_y=32;last_y=first_y+count+1
    image=np.full((84,84),160/255.,np.float32)
    image[first_y:last_y+1,28:51]=gray/255.
    cover=np.zeros_like(image,dtype=bool);cover[first_y:last_y+1,39:45]=True
    image[cover]=60/255.
    rows=[(y,28,50,39,45)for y in range(first_y+1,last_y)]
    first=(first_y,28,50,39,45);last=(last_y,28,50,39,45)
    zero=np.zeros_like(cover)
    return dict(image=image,asphalt=((image>.36)&(image<.47)).astype(np.uint8),
        cover=cover,obstacle=zero.copy(),grass=zero.copy(),rows=rows,first=first,last=last,slope=0.)


def call(f):
    return bool(a.observed_extension_flank_bridge(**f))


def legacy_infer(revision):
    source=subprocess.run(['git','show',revision+':submit_core/observation_agent.py'],
        cwd=ROOT,check=True,capture_output=True,text=True).stdout
    fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='infer_local_road_support')
    namespace=a.__dict__.copy();exec(compile(ast.Module(body=[fn],type_ignores=[]),'<legacy infer>', 'exec'),namespace)
    return namespace['infer_local_road_support']


def check(revision):
    cpu=time.process_time();cases=[]
    def record(name,f,expected):
        actual=call(f);cases.append(dict(name=name,expected=expected,actual=actual,ok=actual==expected))
    for count in range(1,5):
        for gray in (100.,102.,105.):
            f=fixture(count,gray)
            # First originalthree-sample window is inconsistent, while its
            # inner two samples and both full current anchors are coherent.
            for row in f['rows']:f['image'][row[0],47]=(gray+11)/255.
            record(f'inner_window_{count}_{gray}',f,True)
            f=fixture(count,gray)
            for row in f['rows']:f['image'][row[0],45]=(gray+11)/255.
            record(f'alternate_window_{count}_{gray}',f,True)
    f=fixture(3)
    for i,row in enumerate(f['rows']):f['image'][row[0],45:48]=(100+2*i)/255.
    record('bounded_varying_shades',f,True)
    for name in ('cover','obstacle','grass','asphalt'):
        f=fixture();y=f['rows'][0][0]
        if name=='asphalt':f[name][y,46]=0
        else:f[name][y,46]=True
        record(name+'_veto',f,False)
    for gray,label in ((60.,'occlusion'),(76.,'red_paint'),(255.,'white_paint'),(160.,'grass_color')):
        f=fixture();y=f['rows'][0][0];f['image'][y,45:48]=gray/255.
        # A stale/inferred asphalt flag must not override current material.
        f['asphalt'][y,45:48]=1
        record(label+'_current_range',f,False)
    f=fixture();f['rows']=[];record('zero_gap',f,False)
    f=fixture();f['first']=f['rows'][0];record('missing_strict_first_bracket',f,False)
    f=fixture();f['last']=f['rows'][0];record('missing_strict_last_bracket',f,False)
    f=fixture();f['first']=f['last'];record('same_anchor_not_two_brackets',f,False)
    f=fixture(5);record('over_one_tile_span',f,False)
    f=fixture(3);f['slope']=2.;record('sloped_span_over_one_tile',f,False)
    f=fixture(3);f['rows'].pop(1);record('missing_internal_row',f,False)
    f=fixture();f['rows']*=2;record('duplicate_internal_row',f,False)
    f=fixture();first=list(f['first']);first[2]=46;f['first']=tuple(first)
    record('anchor_has_only_two_samples',f,False)
    f=fixture();f['image'][f['first'][0],45:51]=109/255.
    record('anchor_shade_range_conflict',f,False)
    f=fixture();f['image'][f['first'][0],47]=111/255.
    record('strict_first_three_sample_contamination',f,False)
    f=fixture();f['image'][f['last'][0],47]=111/255.
    record('strict_last_three_sample_contamination',f,False)
    f=fixture(2);rows=list(f['rows']);sy,l,r,start,end=rows[1]
    rows[1]=(sy,l,r,start,end+3);f['rows']=rows
    record('no_strict_horizontal_path_overlap',f,False)
    # Exercise caller atomicity and unchanged legacy mode on a whole synthetic
    # vehicle occlusion. Wide end rows satisfy the original inclusion fit.
    image=np.full((84,84),160/255.,np.float32);cover=np.zeros((84,84),np.uint8)
    cover[34:44,39:45]=1
    for y in range(34,44):image[y,(20 if y<=38 else 28):48]=100/255.
    image[cover>0]=60/255.;image[37,47]=111/255.
    # Ending each wide right flank at47 makes its third sample the mixed edge.
    image[34:39,48]=160/255.
    asphalt=((image>.36)&(image<.47)).astype(np.uint8);zero=np.zeros((84,84),bool)
    old=legacy_infer(revision)
    legacy_result=old(image,asphalt,zero,.2,False,30.,cover_override=cover,connected_anchors=False)
    normal=a.infer_local_road_support(image,asphalt,zero,.2,False,30.,cover_override=cover,connected_anchors=False)
    same=np.array_equal(legacy_result[0],normal[0])and legacy_result[1]==normal[1]
    cases.append(dict(name='nonconnected_caller_mode_bit_identical',expected=True,actual=same,ok=same))
    bridged=a.infer_local_road_support(image,asphalt,zero,.2,False,30.,cover_override=cover,connected_anchors=True)
    added=bool(np.all(bridged[0][37,39:45]))
    cases.append(dict(name='whole_caller_atomic_current_bridge',expected=True,actual=added,ok=added))
    # Current grass in the actual occlusion gap must veto both ordinary and
    # bridge inference; a successful nearby flank cannot fill it.
    bad=image.copy();bad[36:38,40:42]=160/255.
    assert a.coherent_grass_mask(bad)[37,41]
    bad_asphalt=((bad>.36)&(bad<.47)).astype(np.uint8)
    refused=a.infer_local_road_support(bad,bad_asphalt,zero,.2,False,30.,cover_override=cover,connected_anchors=True)
    untouched=not bool(refused[0][37,41])
    cases.append(dict(name='whole_caller_visible_grass_gap_veto',expected=True,actual=untouched,ok=untouched))
    return dict(status='PASS'if all(q['ok']for q in cases)else'FAIL',cases=cases,
        passed=sum(q['ok']for q in cases),count=len(cases),CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0,legacy_revision=revision,
        candidate_sha256=hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),
        scope='Synthetic currentpalette/mask/graph/caller regressions. Everyoriginaltwo-column window is retained; thresholds/span/strictbrackets unchanged. No physicalhiddenroad certificate.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--baseline-revision',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=check(args.baseline_revision)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='cases'}));print('FAILURES',json.dumps([q for q in result['cases']if not q['ok']]))
    raise SystemExit(0 if result['status']=='PASS'else 1)

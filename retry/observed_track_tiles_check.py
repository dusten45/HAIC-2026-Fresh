"""Synthetic public tile/paint checks; never creates a track/environment."""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from retry.observed_track_tiles import (STEP,WIDTH,BORDER,generate_tile_layers,
    interior_border_flags,local_nodes,grass_checker_layers)
from retry.raw_boundary_renderer import render_scene
from retry.raw_pixel_intervals import raster_layer_enclosure,forward_enclosure


def run_checks():
    start=time.process_time();tests=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        tests.append(dict(name=name,passed=True))
    turns=[.2,-.1,.05,0.,-.03,.02,0.,0.]
    model=generate_tile_layers((450.,110.),.1,turns,index_phase6=5,
        contact_reset_flags=[False]*7,border_flags=[True]*7)
    nodes=model['nodes'];layers=model['layers']
    check('arbitrary_node_count_no_closing_tile',len(nodes)==8 and len(model['tiles'])==7 and not model['metadata']['closing_seam_included'])
    distances=[math.dist(a['body_center'],b['body_center']) for a,b in zip(nodes,nodes[1:])]
    check('public_three_point_five_meter_step',all(abs(d-STEP)<1e-12 for d in distances))
    timing=local_nodes((0.,0.),0.,[.2,0.])
    check('stored_normal_average_and_next_step_timing',timing[0]['normal_angle']==.1 and
        abs(timing[1]['body_center'][0]+STEP*math.sin(.2))<1e-14 and
        abs(timing[1]['body_center'][1]-STEP*math.cos(.2))<1e-14)
    rejected=False
    try:local_nodes((0.,0.),0.,[.31001,0.])
    except ValueError:rejected=True
    check('public_turn_bound_rejected',rejected)
    check('shared_shade_paint_phase6',[(t['index_phase6'],t['original_road_gray']) for t in model['tiles'][:3]]==[(0,102),(1,104),(2,107)] and
        [layer['rgb_lo'] for layer in layers if layer['kind']=='border'][:3]==[(255,255,255),(255,0,0),(255,255,255)])
    check('original_road_then_border_order',[v['kind'] for v in layers]==['road','border']*7)
    check('explicit_true_zero_side_border_not_silently_omitted',
        model['tiles'][-1]['border_side']==0 and layers[-1]['kind']=='border' and
        len(set(layers[-1]['vertices']))==2 and layers[-1]['optional'] is False)
    reset=generate_tile_layers((450.,110.),.1,turns,index_phase6=5,
        contact_reset_flags=[True]*7,border_flags=[False]*7)
    check('contact_resets_public_shade',all(v['rgb_lo']==v['rgb_hi']==(102,102,102) for v in reset['layers']))
    unknown=generate_tile_layers((450.,110.),.1,turns,index_phase6=5)
    check('unknown_contact_and_border_preserved',unknown['metadata']['contact_history_unknown'] and unknown['metadata']['border_history_unknown'] and
        any(v['optional'] for v in unknown['layers'] if v['kind']=='border'))
    curved=local_nodes((0.,0.),0.,[.12]*12)
    straight=local_nodes((0.,0.),0.,[0.]*12)
    check('four_turn_border_run_and_backpropagation',all(interior_border_flags(curved)))
    check('missing_border_history_stays_unknown',interior_border_flags(straight)[0] is None and interior_border_flags(straight)[3] is False and interior_border_flags(straight)[-1] is None)
    # Independent transcription of the public generator's update timing and
    # original world-coordinate road/border formulas, shifted into local camera.
    beta=.1;x=y=0.;track=[]
    for delta in turns:
        before=beta;beta+=delta
        x+=-math.sin(before)*STEP;y+=math.cos(before)*STEP
        track.append((before*.5+beta*.5,x,y))
    x0,y0=track[0][1:];expected=[]
    for i in range(1,len(track)):
        b1,x1,y1=track[i];b2,x2,y2=track[i-1]
        road=[(x1-WIDTH*math.cos(b1),y1-WIDTH*math.sin(b1)),(x1+WIDTH*math.cos(b1),y1+WIDTH*math.sin(b1)),
            (x2+WIDTH*math.cos(b2),y2+WIDTH*math.sin(b2)),(x2-WIDTH*math.cos(b2),y2-WIDTH*math.sin(b2))]
        side=1 if b2>b1 else -1 if b2<b1 else 0
        border=[(x1+side*WIDTH*math.cos(b1),y1+side*WIDTH*math.sin(b1)),
            (x1+side*(WIDTH+BORDER)*math.cos(b1),y1+side*(WIDTH+BORDER)*math.sin(b1)),
            (x2+side*(WIDTH+BORDER)*math.cos(b2),y2+side*(WIDTH+BORDER)*math.sin(b2)),
            (x2+side*WIDTH*math.cos(b2),y2+side*WIDTH*math.sin(b2))]
        for poly in (road,border):expected.append([(450.+16.2*(px-x0),110.+16.2*(py-y0)) for px,py in poly])
    check('public_original_quad_formulas',all(np.allclose(layer['original_vertices'],poly,rtol=0,atol=1e-11) for layer,poly in zip(layers,expected)))
    integer_expected=[[(math.trunc(x),math.trunc(y)) for x,y in poly] for poly in expected]
    check('source_integer_vertex_truncation',all(layer['vertices']==poly for layer,poly in zip(layers,integer_expected)))
    lo,hi=raster_layer_enclosure(layers,((102,204,102),(102,204,102)))
    gl,gh=forward_enclosure(lo,hi)
    actual=render_scene([(poly,layer['rgb_lo']) for poly,layer in zip(expected,layers)],background=(102,204,102))
    check('synthetic_piecewise_corner_paint_render_enclosed',bool(np.all(gl<=actual) and np.all(actual<=gh)))
    checker=grass_checker_layers(world_to_body_angle=0.,world_to_body_translation=(0.,0.))
    check('public_checker_square_not_half_area_chessboard',any(layer['vertices']==[(770,200),(500,200),(500,470),(770,470)] for layer in checker) and all(layer['rgb_lo']==(102,230,102) for layer in checker))
    check('no_scene_or_parameter_coverage_claim',not model['metadata']['scene_complete'] and not model['metadata']['original_parameter_coverage_proved'])
    return dict(status='PUBLIC_LOCAL_TRACK_TILE_LAYER_PASS',tests=tests,CPU_s=time.process_time()-start,
        model_ticks=0,native_actions=0,synthetic_renders=1,
        scope='No simulator/seed/hidden track. Public timing/quads/shade/contact/parity/border-history/checker formulas and one synthetic render.',
        limitations='Local ordinary fragment only, without global seam/checkpoint generation or complete parameter/scene coverage. Checker camera parameters and border/contact choices are hypotheses.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=run_checks()
    if args.output:
        if args.output.exists():raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps(result))


if __name__=='__main__':main()

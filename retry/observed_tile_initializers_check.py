"""Public seed-feature checks; no claim that proposals cover actual geometry."""
import argparse
import json
from pathlib import Path
import time

import cv2
import numpy as np

from retry.observed_tile_initializers import (ORIGIN_X,ORIGIN_Y,SX,SY,TURN,
    extract_tile_initializers)
from retry.observed_track_tiles import generate_tile_layers
from retry.raw_boundary_renderer import render_scene


def run_checks():
    start=time.process_time();tests=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        tests.append(dict(name=name,passed=True))
    cover=np.zeros((84,84),np.uint8)
    cv2.rectangle(cover,(round(ORIGIN_X-1.4*SX),round(ORIGIN_Y-2.6*SY)),
        (round(ORIGIN_X+1.4*SX),round(ORIGIN_Y+2.4*SY)),1,-1)
    cover=cover.astype(bool)
    model=generate_tile_layers((500.,140.),0.,[0.,.2,-.1,0.,0.,0.,0.,0.],
        index_phase6=0,contact_reset_flags=[False]*7,border_flags=[False]*7)
    gray=render_scene([(layer['vertices'],layer['rgb_lo']) for layer in model['layers']])
    before=gray.copy();result=extract_tile_initializers(gray,cover)
    check('public_piecewise_flanks_detected',all(len(points)>=3 for points in result['visible_flank_points']))
    check('public_shade_seam_points_detected',bool(result['shade_transition_points']))
    check('public_node_proposals_detected',bool(result['node_candidates']))
    check('phase_aliases_retained',result['all_phase_aliases']==list(range(6)) and
        all(node['phase_aliases']==list(range(6)) for node in result['node_candidates']))
    check('input_image_not_modified',np.array_equal(gray,before))
    check('no_hidden_pixel_fill_or_admission_claim',result['parameter_coverage_proved'] is False and
        result['full_render_zero_verified'] is False and 'support_mask' not in result)
    visible=True
    for transition in result['shade_transition_points']:
        x,y=transition['point'];xs={int(np.floor(x)),int(np.ceil(x))};ys={int(np.floor(y)),int(np.ceil(y))}
        visible &= not any(cover[yy,xx] for yy in ys for xx in xs)
    check('seam_points_only_visible_samples',visible)
    check('seed_turns_obey_public_bound',all(max(abs(v) for v in seed['turn_updates'])<=TURN for seed in
        result['generator_pair_seeds']+result['kink_to_straight_seeds']))
    blank=extract_tile_initializers(np.full((84,84),160,np.uint8),cover)
    check('blank_grass_no_node_or_hidden_completion',not blank['node_candidates'] and not blank['generator_pair_seeds'])
    unknown=extract_tile_initializers(gray,cover,observed_mask=np.zeros_like(cover))
    check('unobserved_frame_no_features',not unknown['visible_flank_points'][0] and not unknown['shade_transition_points'])
    normalized=extract_tile_initializers((gray/255.).astype(np.float32),cover)
    check('official_float_quantization_roundtrip',normalized['row_flanks']==result['row_flanks'])
    rejected=False
    try:extract_tile_initializers(np.full((84,84),np.nan),cover)
    except ValueError:rejected=True
    check('nonfinite_image_rejected',rejected)
    return dict(status='PUBLIC_IMAGE_TILE_INITIALIZER_FEATURE_PASS',tests=tests,
        CPU_s=time.process_time()-start,model_ticks=0,native_actions=0,
        synthetic_nodes=len(result['node_candidates']),synthetic_generator_seeds=len(result['generator_pair_seeds']),
        limits='Engineering proposals only. This checks visible feature extraction and premise gates, not full-render-zero seed quality or complete geometry/phase coverage.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=run_checks()
    if args.output:
        if args.output.exists():raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps(result))


if __name__=='__main__':main()

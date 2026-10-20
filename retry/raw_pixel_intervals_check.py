"""Public raw-pixel interval checks without creating an environment/world."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np
import pygame

from retry.raw_pixel_intervals import AUDITED_SOURCES,audit_backend,forward_enclosure,preprocess_raw_rgb


def run_checks():
    start = time.process_time();rng=np.random.default_rng(20261020)
    checks=[];pipeline_images=0
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(dict(name=name,passed=True))
    def contains(lo,hi,image):
        return bool(np.all(lo<=image) and np.all(image<=hi))
    image = rng.integers(0,256,(800,1000,3),dtype=np.uint8)
    lo,hi=forward_enclosure(image,image);pipeline_images+=2
    check('singleton_exact_no_gray_allowance',np.array_equal(lo,hi))
    # Independent official call sequence through the actual wrapper function.
    from env_wrapper import image_preprocessing
    surface=pygame.surfarray.make_surface(np.transpose(image,(1,0,2)))
    surface=pygame.transform.flip(surface,False,True)
    surface=pygame.transform.smoothscale(surface,(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    official=image_preprocessing(rgb);pipeline_images+=1
    check('exact_official_wrapper_quantization',np.array_equal(official,(lo/255.).astype(np.float32)))
    flipped=preprocess_raw_rgb(image[::-1].copy(),flip_y=False);pipeline_images+=1
    check('vertical_flip_permutation_exact',np.array_equal(flipped,lo))
    lower=np.zeros_like(image);upper=np.full_like(image,255)
    l,u=forward_enclosure(lower,upper);pipeline_images+=2
    actual=preprocess_raw_rgb(image);pipeline_images+=1
    check('full_uint8_domain_enclosed',contains(l,u,actual))
    quant_low=np.full_like(image,102);quant_high=np.full_like(image,103)
    l,u=forward_enclosure(quant_low,quant_high);pipeline_images+=2
    middle=quant_low+rng.integers(0,2,image.shape,dtype=np.uint8)
    actual=preprocess_raw_rgb(middle);pipeline_images+=1
    check('one_gray_step_rounding_enclosed',contains(l,u,actual))
    random_pass=True;raw_cases=12;interior_samples=3
    for _ in range(raw_cases):
        low=rng.integers(0,256,image.shape,dtype=np.uint8)
        high=np.minimum(low.astype(np.uint16)+rng.integers(0,17,image.shape,dtype=np.uint16),255).astype(np.uint8)
        l,u=forward_enclosure(low,high);pipeline_images+=2
        for _ in range(interior_samples):
            span=high.astype(np.int16)-low.astype(np.int16)
            actual_rgb=(low.astype(np.int16)+np.floor(rng.random(image.shape)*(span+1)).astype(np.int16)).astype(np.uint8)
            actual=preprocess_raw_rgb(actual_rgb);pipeline_images+=1
            random_pass &= contains(l,u,actual)
    check('random_componentwise_interiors_enclosed',random_pass)
    paint_low=np.full_like(image,102);paint_high=paint_low.copy()
    paint_low[:,480:520]=(255,0,0);paint_high[:,480:520]=(255,255,255)
    l,u=forward_enclosure(paint_low,paint_high);pipeline_images+=2
    paint=paint_low.copy();selector=rng.integers(0,2,(800,40),dtype=np.uint8).astype(bool)
    paint[:,480:520][selector]=(255,255,255)
    actual=preprocess_raw_rgb(paint);pipeline_images+=1
    check('mixed_red_white_paint_quantization_enclosed',contains(l,u,actual))
    check('paint_interval_not_single_material_proof',bool(np.any(u>l)))
    rejected=False
    try:forward_enclosure(quant_high,quant_low)
    except ValueError:rejected=True
    check('inverted_interval_rejected',rejected)
    rejected=False
    try:forward_enclosure(image.astype(float),image)
    except ValueError:rejected=True
    check('wrong_dtype_rejected',rejected)
    return dict(status='AUDITED_RAW_PREPROCESSING_INTERVAL_PASS',tests=checks,
        backend=audit_backend(),pipeline_images=pipeline_images,
        CPU_s=time.process_time()-start,model_ticks=0,native_actions=0,
        sources=list(AUDITED_SOURCES),
        proof='Fixed shape SSE shrink uses nonnegative pixel-independent weights and unsigned accumulators bounded by255*ceil(1000/96)=2805 and255*ceil(800/96)=2295<65536. Uint8 OpenCV linear and gray operations use nonnegative bounded integer coefficients, monotone shifts/round/saturation. Composition and flip preserve componentwise order.',
        limits='Soundness requires supplied raw post-raster RGB bounds to include every gfxdraw/occlusion/HUD/text possibility. Gfxdraw geometry bounds, hidden scene choices and whole-cell material identity are not proved here. Regression samples alone are not the monotonicity proof.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=run_checks()
    if args.output:
        if args.output.exists():raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps(result))


if __name__=='__main__':main()

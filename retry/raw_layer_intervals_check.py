"""Public fixed-geometry gfxdraw bounds checks; no environment/world."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
import pygame
import pygame.gfxdraw

from retry.raw_pixel_intervals import (_polygon_masks,forward_enclosure,
    preprocess_raw_rgb,raster_layer_enclosure)


def run_checks():
    start=time.process_time();rng=np.random.default_rng(61020);tests=[];drawn_images=0
    def check(name,condition):
        if not condition:raise AssertionError(name)
        tests.append(dict(name=name,passed=True))
    def render(background,items):
        surface=pygame.Surface((1000,800),depth=32)
        if np.asarray(background).shape==(3,):surface.fill(tuple(map(int,background)))
        else:pygame.surfarray.blit_array(surface,np.transpose(background,(1,0,2)))
        for vertices,color in items:
            pygame.gfxdraw.aapolygon(surface,vertices,tuple(map(int,color)))
            pygame.gfxdraw.filled_polygon(surface,vertices,tuple(map(int,color)))
        return np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    vertices=((100,100),(900,103),(810,650),(160,700))
    layer=dict(vertices=vertices,rgb_lo=(102,102,102),rgb_hi=(107,107,107))
    lower,upper=raster_layer_enclosure([layer],((102,204,102),(102,230,102)))
    actual=render((102,220,102),[(vertices,(105,105,105))]);drawn_images+=1
    check('road_grass_palette_enclosed',bool(np.all(lower<=actual) and np.all(actual<=upper)))
    fill,affect=_polygon_masks(vertices)
    check('certain_fill_overwrites_background',bool(np.all(lower[fill]==(102,102,102)) and np.all(upper[fill]==(107,107,107))))
    check('outside_affect_background_unchanged',bool(np.all(lower[~affect]==(102,204,102)) and np.all(upper[~affect]==(102,230,102))))
    optional=dict(layer,optional=True)
    l,u=raster_layer_enclosure([optional],((102,204,102),(102,230,102)))
    absent=render((102,220,102),[]);drawn_images+=1
    check('optional_layer_absence_enclosed',bool(np.all(l<=absent) and np.all(absent<=u)))
    check('optional_layer_presence_enclosed',bool(np.all(l<=actual) and np.all(actual<=u)))
    red=dict(vertices=((400,80),(420,80),(430,730),(410,730)),rgb_lo=(255,0,0),rgb_hi=(255,255,255),optional=True)
    l,u=raster_layer_enclosure([layer,red],((102,204,102),(102,230,102)))
    paint=render((102,204,102),[(vertices,(102,102,102)),(red['vertices'],(255,0,0))]);drawn_images+=1
    white=render((102,230,102),[(vertices,(107,107,107)),(red['vertices'],(255,255,255))]);drawn_images+=1
    check('ordered_optional_red_white_layer_enclosed',bool(np.all(l<=paint) and np.all(paint<=u) and np.all(l<=white) and np.all(white<=u)))
    fl,fu=forward_enclosure(l,u)
    processed=preprocess_raw_rgb(paint)
    check('layer_bounds_survive_official_preprocessing',bool(np.all(fl<=processed) and np.all(processed<=fu)))
    random_pass=True
    polygons=[vertices,((-20,20),(1010,17),(996,390),(10,420)),((10,13),(990,16),(500,777)),((2,2),(997,798),(996,798))]
    for index in range(24):
        vertex=polygons[index%len(polygons)]
        bglo=rng.integers(0,256,3);bghi=np.maximum(bglo,rng.integers(0,256,3))
        fglo=rng.integers(0,256,3);fghi=np.maximum(fglo,rng.integers(0,256,3))
        bg=rng.integers(bglo,bghi+1);fg=rng.integers(fglo,fghi+1)
        l,u=raster_layer_enclosure([dict(vertices=vertex,rgb_lo=fglo,rgb_hi=fghi)],(bglo,bghi))
        image=render(bg,[(vertex,fg)]);drawn_images+=1
        random_pass &= bool(np.all(l<=image) and np.all(image<=u))
    check('random_color_clipped_slender_polygon_regression',random_pass)
    # Negative-rounding alpha1: white-on-black alone misses a real affected
    # location; reverse polarity detects it. This is why support masks use both.
    dark=pygame.Surface((2,2),depth=32);dark.fill((0,0,0))
    light=pygame.Surface((2,2),depth=32);light.fill((255,255,255))
    pygame.gfxdraw.pixel(dark,0,0,(255,255,255,1))
    pygame.gfxdraw.pixel(light,0,0,(0,0,0,1))
    check('alpha1_negative_rounding_reverse_mask_needed',dark.get_at((0,0))[0]==0 and light.get_at((0,0))[0]<255)
    rejected=False
    try:raster_layer_enclosure([dict(layer,vertices=((1.2,0),(2,1),(1,3)))],((0,0,0),(255,255,255)))
    except ValueError:rejected=True
    check('noninteger_geometry_rejected',rejected)
    rejected=False
    try:raster_layer_enclosure([dict(layer,rgb_lo=(108,108,108))],((0,0,0),(255,255,255)))
    except ValueError:rejected=True
    check('inverted_material_rejected',rejected)
    roi=(250,120,700,390);area=np.s_[roi[1]:roi[3],roi[0]:roi[2]]
    full_lo,full_hi=raster_layer_enclosure([layer,red],((102,204,102),(102,230,102)))
    crop_lo,crop_hi=raster_layer_enclosure([layer,red],((102,204,102),(102,230,102)),interest_box=roi)
    check('interest_rectangle_exact_inside',np.array_equal(full_lo[area],crop_lo[area]) and np.array_equal(full_hi[area],crop_hi[area]))
    check('interest_rectangle_globally_widens',bool(np.all(crop_lo<=full_lo) and np.all(crop_hi>=full_hi)))
    outside=np.ones((800,1000),bool);outside[area]=False
    check('outside_interest_is_full_unknown',bool(np.all(crop_lo[outside]==0) and np.all(crop_hi[outside]==255)))
    f_lo,f_hi=forward_enclosure(full_lo,full_hi)
    c_lo,c_hi=forward_enclosure(crop_lo,crop_hi)
    check('cropped_forward_bounds_remain_outer',bool(np.all(c_lo<=f_lo) and np.all(c_hi>=f_hi)))
    rejected=True
    for invalid_roi in [(0,0,0,10),(-1,0,10,10),(0,0,1001,800),(0.,0,10,10),(0,0,10)]:
        try:raster_layer_enclosure([layer],((0,0,0),(255,255,255)),interest_box=invalid_roi)
        except ValueError:continue
        rejected=False
    check('invalid_interest_rectangle_rejected',rejected)
    fill,affect=_polygon_masks(vertices)
    check('cached_masks_are_readonly',not fill.flags.writeable and not affect.flags.writeable)
    return dict(status='FIXED_INTEGER_GFXDRAW_LAYER_ENCLOSURE_PASS',tests=tests,
        CPU_s=time.process_time()-start,drawn_images=drawn_images,model_ticks=0,native_actions=0,
        proof='Filled_polygon opaque pixels overwrite. AA-only pixels remain in the background/material channel hull. Union of white-on-black and black-on-white affected masks detects every positive-alpha operation including alpha1 negative rounding. Optional layers retain both presence and absence.',
        limitations='Exact integer geometry/order is supplied. RGB boxes allow arbitrary pointwise shade choices but do not certify geometry, scene completeness, HUD, unseen/cropped polygons or material meaning. Regression samples supplement source review and are not exhaustive proof.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=run_checks()
    if args.output:
        if args.output.exists():raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps(result))


if __name__=='__main__':main()

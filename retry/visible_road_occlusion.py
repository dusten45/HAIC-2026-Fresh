"""Renderer-provenance occlusion stencil, without RGB color heuristics."""
import hashlib
import math

import cv2
import numpy as np
import pygame

from core.vendor.car_racing import (MAX_SHAPE_DIM, OBSTACLE_RENDER_VERTICES,
                                  STATE_H, STATE_W, WINDOW_H, WINDOW_W)
from core.vendor.car_dynamics import SIZE, WHEEL_R, WHEEL_W
from retry.current_view_road_oracle import camera, draw_polygon, road_mask


def polygon_pixels(polygon, zoom, translation, angle):
    points=[pygame.math.Vector2(p).rotate_rad(angle) for p in polygon]
    return [(p.x*zoom+translation[0],p.y*zoom+translation[1]) for p in points]


def renderer_polygon(surface,polygon,value,zoom,translation,angle):
    projected=polygon_pixels(polygon,zoom,translation,angle)
    if any(-MAX_SHAPE_DIM<=x<=WINDOW_W+MAX_SHAPE_DIM and
           -MAX_SHAPE_DIM<=y<=WINDOW_H+MAX_SHAPE_DIM for x,y in projected):
        draw_polygon(surface,polygon,(value,)*3,zoom,translation,angle)


def hud_polygons(state):
    """Every opaque HUD polygon, including any bar extending above its slab."""
    W,H=WINDOW_W,WINDOW_H;s,h=W/40.,H/40.
    polygons=[[(W,H),(W,H-5*h),(0,H-5*h),(0,H)]]
    def vertical(place,val):return [(place*s,H-(h+h*val)),((place+1)*s,H-(h+h*val)),((place+1)*s,H-h),(place*s,H-h)]
    def horizontal(place,val):return [(place*s,H-4*h),((place+val)*s,H-4*h),((place+val)*s,H-2*h),(place*s,H-2*h)]
    if abs(state['speed_m_s'])>1e-4:polygons.append(vertical(5,.02*state['speed_m_s']))
    for i,w in enumerate(state['wheels']):
        if abs(w['omega'])>1e-4:polygons.append(vertical(7+i,.01*w['omega']))
    if abs(state['wheels'][0]['joint_angle'])>1e-4:polygons.append(horizontal(20,-10*state['wheels'][0]['joint_angle']))
    if abs(state['angular_velocity'])>1e-4:polygons.append(horizontal(30,-.8*state['angular_velocity']))
    # Native font42 reward text is centered at y750 and entirely inside the slab.
    return polygons


def occlusion_stencil(road_layers,obstacles,car_objects,state,zoom,translation,angle):
    """Opaque-material provenance in native draw order; fixed half-coverage bin."""
    surface=pygame.Surface((WINDOW_W,WINDOW_H));surface.fill((0,0,0))
    # Later road paint clears earlier curb coverage. Retain the native ordering.
    for polygon,is_curb in road_layers:
        renderer_polygon(surface,polygon,255 if is_curb else 0,zoom,translation,angle)
    for x,y,radius in obstacles:
        polygon=[(x+radius*math.cos(2*math.pi*i/OBSTACLE_RENDER_VERTICES),
                  y+radius*math.sin(2*math.pi*i/OBSTACLE_RENDER_VERTICES)) for i in range(OBSTACLE_RENDER_VERTICES)]
        renderer_polygon(surface,polygon,255,zoom,translation,angle)
    # state_pixels disables skid particles. Wheels precede the hull.
    for obj in car_objects:
        transform=obj['transform']
        for vertices in obj['fixtures']:
            polygon=[tuple(transform*v) for v in vertices]
            pygame.draw.polygon(surface,(255,255,255),polygon_pixels(polygon,zoom,translation,angle))
            if obj.get('phase') is None:continue
            phase=obj['phase'];s1,s2=math.sin(phase),math.sin(phase+1.2)
            c1,c2=math.cos(phase),math.cos(phase+1.2)
            if s1>0 and s2>0:continue
            if s1>0:c1=float(np.sign(c1))
            if s2>0:c2=float(np.sign(c2))
            stripe=[(-WHEEL_W*SIZE,WHEEL_R*c1*SIZE),(WHEEL_W*SIZE,WHEEL_R*c1*SIZE),
                    (WHEEL_W*SIZE,WHEEL_R*c2*SIZE),(-WHEEL_W*SIZE,WHEEL_R*c2*SIZE)]
            stripe=[tuple(transform*v) for v in stripe]
            # Stripe is opaque too; its native gray color is not road visibility.
            pygame.draw.polygon(surface,(255,255,255),polygon_pixels(stripe,zoom,translation,angle))
    surface=pygame.transform.flip(surface,False,True)
    for polygon in hud_polygons(state):pygame.draw.polygon(surface,(255,255,255),polygon)
    scaled=pygame.transform.smoothscale(surface,(STATE_W,STATE_H))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(scaled)),(1,0,2))
    gray=cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY)
    return (gray>=128).astype(np.uint8),gray


def visible_road_mask(env):
    from retry.full_route_reproduction import truth
    raw=env.unwrapped;A,receipt=road_mask(env)
    layers=[]
    for polygon,color in raw.road_poly:
        label=tuple(color) in ((255,255,255),(255,0,0))
        assert label or np.all(np.asarray(color)<255)
        layers.append((polygon,label))
    obstacles=[(*map(float,o.position),float(o.fixtures[0].shape.radius)) for o in raw.obstacles]
    objects=[{'transform':o.transform,'fixtures':[list(f.shape.vertices) for f in o.fixtures],
              'phase':getattr(o,'phase',None)} for o in raw.car.drawlist]
    O,_=occlusion_stencil(layers,obstacles,objects,truth(env),*camera(raw))
    B=(A.astype(bool)&~O.astype(bool)).astype(np.uint8)
    assert np.array_equal(A-B,A*O)
    receipt.update(scope='current camera; renderer-visible GT; occluded cells false; unknown/nonroad conflated',
                   full_gt_mask_sha256=receipt['mask_sha256'],occlusion_mask_sha256=hashlib.sha256(O.tobytes()).hexdigest(),
                   mask_sha256=hashlib.sha256(B.tobytes()).hexdigest(),road_pixels=int(B.sum()),
                   removed_occluded_road_pixels=int((A-B).sum()),occlusion_pixels=int(O.sum()),
                   occlusion_definition='native draw-order stencil: curb ownership,16-gon obstacles,car fixtures/stripes,postflipHUD;96to84;coverage>=128',
                   B_formula='B=A & ~O; no added filling; inherited road postprocessing unchanged')
    return B,receipt

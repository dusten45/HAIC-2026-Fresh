"""Hash-qualified reconstruction of a previously captured diagnostic road mask."""
import ast
import hashlib
import inspect
import math
import textwrap
from types import SimpleNamespace as N

from Box2D import b2PolygonShape,b2Transform
import numpy as np

import core.vendor.car_racing as cr
from retry.current_view_road_oracle import camera,draw_polygon,render_road_mask
from retry.visible_road_occlusion import occlusion_stencil


def saved_geometry(track):
    """Invoke the frozen native road/curb construction on a non-physics proxy."""
    body=ast.parse(textwrap.dedent(inspect.getsource(cr.CarRacing._create_track))).body[0].body
    first=next(i for i,x in enumerate(body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='border' for t in x.targets))
    class ShapeCollector:
        def CreateStaticBody(self,fixtures):return N(fixtures=[N(shape=b2PolygonShape(vertices=fixtures.shape.vertices))])
    proxy=N(world=ShapeCollector(),fd_tile=N(shape=b2PolygonShape()),road_color=np.array([102.,102.,102.]),road_poly=[],road=[])
    namespace=vars(cr).copy();namespace.update(self=proxy,track=track)
    code=ast.fix_missing_locations(ast.Module(body=body[first:-1],type_ignores=[]));exec(compile(code,'saved_native_road_geometry','exec'),namespace)
    return [(p,tuple(c) in ((255,255,255),(255,0,0))) for p,c in proxy.road_poly],[[tuple(v) for v in o.fixtures[0].shape.vertices] for o in proxy.road]


def reconstruction(scene,state,receipt):
    layers,polygons=saved_geometry(scene['track'])
    cam=camera(N(car=N(hull=N(position=state['position'],angle=state['angle'])),t=state['time']))
    A,_=render_road_mask(polygons,*cam,draw_polygon)
    assert hashlib.sha256(A.tobytes()).hexdigest()==receipt['full_gt_mask_sha256']
    def transform(s):
        t=b2Transform();t.position=tuple(s['position']);t.angle=s['angle'];return t
    objects=[{'transform':transform(w),'fixtures':scene['wheel_fixture_local_vertices'][i],'phase':0.} for i,w in enumerate(state['wheels'])]
    objects.append({'transform':transform(state),'fixtures':scene['hull_fixture_local_vertices'],'phase':None})
    obstacles=[(*o['position'],o['radius']) for o in scene['obstacles']]
    # Saved wheel phases may be absent. Accept only an exact already-recorded mask
    # receipt; this is reconstruction provenance, not replay of original RGB.
    for phase in (0.,.7,1.6,3.4,5.9):
        for o in objects[:-1]:o['phase']=phase
        O,_=occlusion_stencil(layers,obstacles,objects,state,*cam);B=A*(1-O)
        if hashlib.sha256(B.tobytes()).hexdigest()==receipt['mask_sha256']:
            return A,B,{'recorded_full_GT_sha_exact':True,'recorded_visible_GT_sha_exact':True,'wheel_phase_proxy':phase,'original_RGB_reconstructed':False,'new_env_or_physics_actions':0}
    raise ValueError('Saved visible mask cannot be reconstructed exactly; comparison withheld')

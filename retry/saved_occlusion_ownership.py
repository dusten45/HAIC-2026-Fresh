"""Evaluator-only saved material ownership, qualified by native occlusion SHA."""
import hashlib
from types import SimpleNamespace as N
from Box2D import b2Transform
import numpy as np
from retry.current_view_road_oracle import camera
from retry.saved_road_input_reconstruction import saved_geometry
from retry.visible_road_occlusion import occlusion_stencil


def ownership(scene,state,receipt,layers=None):
    if layers is None:layers=saved_geometry(scene['track'])[0]
    cam=camera(N(car=N(hull=N(position=state['position'],angle=state['angle'])),t=state['time']))
    def transform(s):
        t=b2Transform();t.position=tuple(s['position']);t.angle=s['angle'];return t
    objects=[{'transform':transform(w),'fixtures':scene['wheel_fixture_local_vertices'][i],'phase':0.} for i,w in enumerate(state['wheels'])]
    objects.append({'transform':transform(state),'fixtures':scene['hull_fixture_local_vertices'],'phase':None})
    obstacles=[(*o['position'],o['radius']) for o in scene['obstacles']]
    found=False
    for phase in (0.,.7,1.6,3.4,5.9):
        for o in objects[:-1]:o['phase']=phase
        O,gray=occlusion_stencil(layers,obstacles,objects,state,*cam)
        if hashlib.sha256(O.tobytes()).hexdigest()==receipt['occlusion_mask_sha256']:
            found=True;break
    assert found,'Full occlusion receipt mismatch; withhold ownership classification'
    HUD,hud_gray=occlusion_stencil([],[],[],state,*cam)
    masks={'occlusion':O,'occlusion_coverage':gray,'HUD':HUD,'HUD_coverage':hud_gray}
    for name,args in [('car',([],[],objects)),('obstacles',([],obstacles,[])),('curb',(layers,[],[]))]:
        _,coverage=occlusion_stencil(*args,state,*cam)
        masks[name+'_coverage']=np.where(hud_gray>0,0,coverage).astype(np.uint8)
    return masks,{'full_native_occlusion_SHA_exact':True,'phase_proxy':phase,'regions_may_overlap':True,'new_env_or_physics_steps':0}

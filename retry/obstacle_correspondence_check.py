"""Static public disks under camera motion, clipping and actual vehicle opacity."""
from pathlib import Path
import json,sys,time,math
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def world(pixel):return np.array([(pixel[0]-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-pixel[1])/1.701])


def render(center,vehicle=False,object_present=True,road_gray=102):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def source(v):
        x=a.IMAGE_ORIGIN_X+1.3608*v[0];y=a.IMAGE_ORIGIN_Y-1.701*v[1]
        return ((x+.5)*1000/84-.5,799-((y+.5)*800/84-.5))
    def draw(poly,color):
        p=[source(v) for v in poly];gfxdraw.aapolygon(surface,p,color);gfxdraw.filled_polygon(surface,p,color)
    # The fixed-width public physical road is centred on the fixed object.
    x=center[0];draw([(x-40/6,-100),(x+40/6,-100),(x+40/6,100),(x-40/6,100)],(road_gray,)*3)
    if object_present:
        theta=np.arange(16)*2*math.pi/16
        draw(center+1.2*np.column_stack((np.cos(theta),np.sin(theta))),(255,165,0))
    if vehicle:
        for poly in (a.core.HULL_POLY1,a.core.HULL_POLY2,a.core.HULL_POLY3,a.core.HULL_POLY4):draw(np.array(poly)*a.core.SIZE,(204,0,0))
        for pos in np.array(a.core.WHEELPOS)*a.core.SIZE:
            draw(pos+np.array([[-.28,-.54],[.28,-.54],[.28,.54],[-.28,.54]]),(0,0,0))
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255


def sequence(pixels,vehicle=False):
    tracks=[];previous=None;rows=[];previous_field=None;previous_raw_field=None
    for pixel in pixels:
        center=world(pixel)
        # Exactly known own-action camera translation in this raster fixture.
        if previous is not None:
            for track in tracks:track['center']=(np.array(track['center'])+center-previous).tolist()
        image=render(center,vehicle);raw,_=a.detect_observed_obstacles(image)
        tracks,counts=a.update_observed_obstacles(image,raw,tracks,0.)
        reference=center+np.column_stack((np.full(31,-1.),np.linspace(-30.,60.,31)))
        stations=np.linspace(0.,90.,31)
        field=a.deform_observed_reference(reference,reference,stations,[(q['center'],q['radius']) for q in tracks])-reference
        raw_field=a.deform_observed_reference(reference,reference,stations,raw)-reference
        rows.append(dict(raw=len(raw),tracks=len(tracks),counts=counts,
            center_error_m=float(np.linalg.norm(np.array(tracks[0]['center'])-center)) if tracks else None,
            field_jump_m=0. if previous_field is None else float(np.max(np.linalg.norm(field-previous_field,axis=1))),
            raw_field_jump_m=0. if previous_raw_field is None else float(np.max(np.linalg.norm(raw_field-previous_raw_field,axis=1)))))
        assert len(tracks)==1,'TRACK_DROPPED_OR_DUPLICATED'
        previous=center;previous_field=field;previous_raw_field=raw_field
    return rows


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    crop=sequence([(4.5,y) for y in (65.5,67.5,68.5,69.5,71.5,65.5)])
    side=sequence([(x,50.) for x in (4.5,2.5,.1,-2.,-4.,4.5)])
    cover=sequence([(41.5,y) for y in (50.,54.,58.,62.,50.)],vehicle=True)
    assert any(r['raw']==0 for r in crop+side+cover)
    assert max(r['raw_field_jump_m'] for r in crop+side+cover)>1.,'NONVACUOUS_REFERENCE_DISAPPEARANCE'
    assert max(r['field_jump_m'] for r in crop+side+cover)<1e-12,'CROP_OR_OPACITY_MOVED_REFERENCE'
    assert max(r['center_error_m'] for r in crop+side+cover)<math.hypot(1/1.3608,1/1.701)
    center=world((60.,30.));image=render(center);raw,_=a.detect_observed_obstacles(image)
    tracks,_=a.update_observed_obstacles(image,raw,[],0.);assert len(tracks)==1
    removed=render(center,object_present=False);tracks,counts=a.update_observed_obstacles(removed,[],tracks,0.)
    assert not tracks and counts['negative']==1,'VISIBLE_NEGATIVE_IGNORED'
    tracks,_=a.update_observed_obstacles(image,raw,[],0.)
    mixed=removed.copy();mixed[30,60]=170/255.
    tracks,counts=a.update_observed_obstacles(mixed,[],tracks,0.)
    assert not tracks and counts['negative']==1,'ISOLATED_MIXED_PIXEL_PRESERVED_GHOST'
    grass=np.full((84,84),170/255.,np.float32)
    raw,_=a.detect_observed_obstacles(grass);tracks,_=a.update_observed_obstacles(grass,raw,[],0.)
    assert not tracks,'UNOBSERVED_OBJECT_INVENTED'
    observer=a.Agent();observer.obstacle_tracks=[dict(center=[1.,2.],radius=1.6)];observer.reference_lattice=np.ones((3,2));observer.reset(None)
    assert not observer.obstacle_tracks and not observer.reference_lattice
    phase_cases=0;phase_recoveries=0;max_recovered_center_shift=0.;max_centroid_bias_px=0.;max_associated_shift=0.
    for shade in (102,104,107):
        initial=world((26.5,37.5));frame=render(initial,road_gray=shade)
        detected,_=a.detect_observed_obstacles(frame);assert len(detected)==1
        old,_=a.update_observed_obstacles(frame,detected,[],0.)
        for x in np.arange(25.,27.,.1):
          for y in np.arange(37.,39.,.1):
            center=world((x,y));frame=render(center,road_gray=shade)
            raw,_=a.detect_observed_obstacles(frame)
            prior=[dict(old[0],center=(np.array(old[0]['center'])+center-initial).tolist())]
            tracks,counts=a.update_observed_obstacles(frame,raw,prior,0.)
            assert len(tracks)==1,'FULL_VISIBLE_RASTER_PHASE_DROPOUT'
            if raw:
                bias=float(np.max(np.abs((np.array(raw[0][0])-center)*[1.3608,1.701])))
                max_centroid_bias_px=max(max_centroid_bias_px,bias)
                assert bias<=1.,'PUBLIC_CENTROID_OUTSIDE_PIXEL_LOCALIZATION_BOX'
            associated_shift=float(np.linalg.norm(np.array(tracks[0]['center'])-prior[0]['center']))
            max_associated_shift=max(max_associated_shift,associated_shift)
            assert associated_shift<1e-12,'CONSISTENT_CURRENT_MEASUREMENT_REPLACED_PRIOR'
            phase_cases+=1
            if not raw:
                phase_recoveries+=1
                shift=float(np.linalg.norm(np.array(tracks[0]['center'])-prior[0]['center']))
                max_recovered_center_shift=max(max_recovered_center_shift,shift)
                assert counts['partial']==1 and shift<1e-12
            empty=render(center,object_present=False,road_gray=shade)
            empty[int(round(y)),int(round(x))]=170/255.
            tracks,counts=a.update_observed_obstacles(empty,[],prior,0.)
            assert not tracks,'ONE_BRIGHT_PIXEL_PASSED_SHAPE_RECHECK'
    assert phase_recoveries>0,'NONVACUOUS_MIXED_CORE_RECHECK'
    center=world((26.5,37.5));frame=render(center);raw,_=a.detect_observed_obstacles(frame)
    prior=[dict(center=(np.array(raw[0][0])+[2/1.3608,0]).tolist(),radius=1.6)]
    tracks,_=a.update_observed_obstacles(frame,raw,prior,0.)
    assert len(tracks)==1 and np.linalg.norm(np.array(tracks[0]['center'])-prior[0]['center'])>.5/1.3608,'INCONSISTENT_PRIOR_FROZEN'
    result=dict(status='PASS',crop=crop,side_crop=side,vehicle_cover=cover,
        full_visible_phase_cases=phase_cases,mixed_core_recoveries=phase_recoveries,
        recovered_center_shift_m=max_recovered_center_shift,
        max_public_centroid_bias_px=max_centroid_bias_px,consistent_observation_center_shift_m=max_associated_shift,
        inconsistent_prior_corrected=True,
        visible_negative_removed=True,no_history_no_invention=True,reset_clears_memory=True,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        limitation='Known static object positions outside visibility are own-action estimates, not newly observed or universally validated. No hidden road pixels are filled.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('crop','side_crop','vehicle_cover')}))


if __name__=='__main__':main()

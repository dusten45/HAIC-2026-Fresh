"""Observation-only experimental input adapter for the actual runtime598 core.

All physical states/history below are estimates or explicit mechanical priors.
The returned runtime admission is NOT a true-state safety certificate. No global
map, seed, stored prefix command, tracker or evaluation data is loaded here.
"""
import math
import numpy as np
import cv2
import runtime598 as core


_BASELINE_CHOOSE=core.choose
_BASELINE_BACKUP=core.backup


def force_feasible_backup(counter,cost,max_ticks):
    """Keep a force-feasible original backup; otherwise reduce steering only.

    These four-raw probes are filters, not safety certificates. The unchanged
    outer certifier still checks every original constraint over all12 holds.
    """
    def command(root,high,low,progress):
        original=_BASELINE_BACKUP(root,high,low,progress)
        index=core.bounds(root.roads)
        def force_safe(action):
            state=core.replace(root,planar=core.replace(root.planar,steer=-float(action[0])))
            cost['joint_backup_checks']=cost.get('joint_backup_checks',0)+1
            for _ in range(4):
                rows=core.force_rows(state,action);cost['force_evaluations']+=4
                if max(row['ratio'] for row in rows)>core.ADMISSION:return False
                if counter[0]>=max_ticks:raise RuntimeError('JOINT_BACKUP_MODEL_CAP')
                state=core.tick(state,float(action[1]),float(action[2]),index,counter)
                cost['forecast_ticks']+=1
            return True
        if force_safe(original):return original
        hold=float(np.float32(-sum(root.planar.joints[:2])/2.))
        for steer in (float(np.float32((hold+float(original[0]))/2.)),hold):
            adjusted=original.copy();adjusted[0]=steer
            if force_safe(adjusted):return adjusted
        return original
    return command


def joint_feasibility_fallback(root,high,low,progress,counter,cost,max_ticks,history,geometry,baseline):
    """Bounded original-certifier repair after the original pedal search fails.

    The original backup's pedals remain unchanged; its steering is projected
    only when it fails a force probe. Full certification remains mandatory.
    """
    initial=core.nominal(root,high,progress)
    hold=float(np.float32(-sum(root.planar.joints[:2])/2.))
    steers=[]
    for value in (hold,float(np.float32((hold+float(initial[0]))/2.))):
        if value!=float(initial[0]) and value not in steers:steers.append(value)
    certify=core.certifier(root,high,low,progress,counter,cost,geometry,max_ticks,history)
    trials=[];feasible=[];before=cost['forecast_calls']
    original_backup=core.backup
    core.backup=force_feasible_backup(counter,cost,max_ticks)
    try:
        for steer in steers:
            for i in range(16,-1,-1):
                u=float(np.float32(-1.+i/8.))
                action=np.array([steer,max(0.,u),max(0.,-u)],np.float32)
                report=certify(action)
                trials.append(dict(steer=steer,u=u,joint_fallback=True,**report))
                if report['ok']:feasible.append((action,report,u))
        if feasible:
            action,_,u=max(feasible,key=lambda row:(row[1]['first_hold']['progress_gain'],row[2],
                -abs(float(row[0][0])-float(initial[0]))))
            final=certify(action)
    finally:core.backup=original_backup
    combined=dict(baseline,joint_fallback=True,joint_fallback_trials=len(trials),
        baseline_mode=baseline['mode'],trials=list(baseline.get('trials',[]))+trials)
    if not feasible:return None,combined
    if cost['forecast_calls']-before>35:raise RuntimeError('JOINT_FALLBACK_FORECAST_CAP')
    if not final['ok']:
        return None,dict(combined,mode='FINAL_CERTIFICATION_FAILED',final_recertified=False)
    return action,dict(combined,mode='JOINT_FEASIBILITY_REPAIR',final_recertified=True,
        reports=[*baseline.get('reports',[]),dict(mode='FINAL',**final)])


def choose_with_joint_feasibility(root,high,low,progress,counter,cost,max_ticks=60000,history=(0,0),geometry=None):
    action,report=_BASELINE_CHOOSE(root,high,low,progress,counter,cost,max_ticks,history,geometry)
    if action is not None or report['mode']!='NO_ADMISSIBLE_ACTION':return action,report
    return joint_feasibility_fallback(root,high,low,progress,counter,cost,max_ticks,history,geometry,report)


core.choose=choose_with_joint_feasibility

# Pixel centres after public 1000x800 -> 96x96 -> 84x84 rendering,
# including the vertical flip about WINDOW_H-1. No fitted camera offset.
IMAGE_ORIGIN_X=(500.+.5)*84./1000.-.5
IMAGE_ORIGIN_Y=(799.-200.+.5)*84./800.-.5


def observed_obstacle_coordinates(points,arc,normal,center):
    """Locate an observed object on a finite observed polyline.

    Select the nearest finite segment first. An object beyond a crop endpoint
    retains its longitudinal residual; this does not extend the reference.
    """
    center=np.asarray(center,dtype=np.float64)
    delta=np.diff(points,axis=0);squared=np.sum(delta*delta,axis=1)
    valid=np.flatnonzero(squared>1e-12)
    if not len(valid):
        return float(arc[0]),float((center-points[0])@normal[0])
    fraction=np.clip(np.sum((center-points[:-1])*delta,axis=1)/np.maximum(squared,1e-12),0.,1.)
    projected=points[:-1]+fraction[:,None]*delta
    j=int(valid[np.argmin(np.sum((projected[valid]-center)**2,axis=1))])
    f=float(fraction[j]);tangent=delta[j]/math.sqrt(float(squared[j]))
    n=(1.-f)*normal[j]+f*normal[j+1]
    n/=max(float(np.linalg.norm(n)),1e-6)
    residual=center-projected[j]
    station=float(arc[j]+f*(arc[j+1]-arc[j]))
    along=float(residual@tangent)
    if (j==valid[0] and f==0. and along<0.) or (j==valid[-1] and f==1. and along>0.):
        station+=along
    return station,float(residual@n)


def observed_reference_lattice(points,previous):
    """Reobserve a fixed spatial lattice on the CURRENT finite centreline."""
    points=np.asarray(points,np.float64);step=21./6.
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    delta=np.diff(points,axis=0);squared=np.sum(delta*delta,axis=1)
    valid=np.flatnonzero(squared>1e-12);matches=[]
    if previous is not None and len(previous)>=3:
        previous=np.asarray(previous,np.float64)
        for i,point in enumerate(previous):
            f=np.clip(np.sum((point-points[:-1])*delta,axis=1)/np.maximum(squared,1e-12),0.,1.)
            projected=points[:-1]+f[:,None]*delta
            old_t=previous[min(i+1,len(previous)-1)]-previous[max(0,i-1)]
            old_t/=max(float(np.linalg.norm(old_t)),1e-6)
            candidates=[j for j in valid if float(delta[j]@old_t)/math.sqrt(float(squared[j]))>=math.cos(.31)
                and float(np.linalg.norm(projected[j]-point))<=math.hypot(1/1.3608,1/1.701)]
            if candidates:
                j=min(candidates,key=lambda k:float(np.linalg.norm(projected[k]-point)))
                s=float(arc[j]+f[j]*(arc[j+1]-arc[j]))
                # An endpoint clamp is not a correspondence to an old node
                # outside current support. It cannot anchor the lattice.
                if (j==valid[0] and f[j]==0.) or (j==valid[-1] and f[j]==1.):continue
                matches.append((i,s))
    phase=0.;accepted=False
    if len(matches)>=3 and all(b[1]>a[1] for a,b in zip(matches,matches[1:])):
        offsets=np.array([s-i*step for i,s in matches])
        # Same pixel localization bound as correspondence, not a force fit.
        if float(np.ptp(offsets))<=2*math.hypot(1/1.3608,1/1.701):
            phase=float(np.median(offsets)%step);accepted=True
            if min(phase,step-phase)<1e-9:phase=0.
    sample=np.arange(phase,float(arc[-1])+1e-9,step)
    if len(sample)<3:
        # The row collector normally supplies >=7m. Do not claim a uniform
        # derivative grid where the current support is actually shorter.
        return points,dict(reference_lattice_used=False,reference_lattice_matches=len(matches))
    result=np.column_stack([np.interp(sample,arc,points[:,j]) for j in range(2)])
    return result,dict(reference_lattice_used=True,reference_lattice_matches=len(matches),
        reference_lattice_correspondence=accepted,reference_geometry_sample_step_m=step,
        reference_lattice_phase_m=float(sample[0]),
        reference_lattice_unrepresented_suffix_m=float(arc[-1]-sample[-1]))


def deform_observed_reference(points,observed,source_stations,obstacles):
    """Object correspondence uses all observed support, before grid sampling."""
    points=points.copy()
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    tangent=np.gradient(points,arc,axis=0)
    normal=np.column_stack((tangent[:,1],-tangent[:,0]));normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-6)
    dense_arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(observed,axis=0),axis=1))]
    dense_tangent=np.gradient(observed,dense_arc,axis=0)
    dense_normal=np.column_stack((dense_tangent[:,1],-dense_tangent[:,0]));dense_normal/=np.maximum(np.linalg.norm(dense_normal,axis=1,keepdims=True),1e-6)
    for center,radius in obstacles:
        station,signed=observed_obstacle_coordinates(observed,dense_arc,dense_normal,center)
        # Evaluate the unchanged16m physical offset on dense observed arc
        # coordinates. The final sparse chord must not reanchor the field.
        amplitude=-math.copysign(max(0.,3.8-abs(signed)),signed if signed else 1.)
        points+=(amplitude*np.exp(-.5*((source_stations-station)/16.)**2))[:,None]*normal
    return points


def observed_reference_progress(points,arc,center):
    # Initial progress must use the SAME continuous projection as the original
    # certifier. A nearest-node value can start ahead and fake a backward step.
    return float(core.project(tuple(center),dict(points=points.tolist(),arcs=arc.tolist(),
        length=float(arc[-1]),observed_open=True))['s'])


def observed_reference_curvature(points):
    """Three observed points define local geometric curvature, including ends.

    Two successive one-sided gradients halve a circular boundary's curvature;
    moving the crop then changes a fixed physical point's speed input.
    """
    delta=np.diff(points,axis=0)
    cross=np.abs(delta[:-1,0]*delta[1:,1]-delta[:-1,1]*delta[1:,0])
    denominator=np.linalg.norm(delta[:-1],axis=1)*np.linalg.norm(delta[1:],axis=1)*np.linalg.norm(points[2:]-points[:-2],axis=1)
    interior=2*cross/np.maximum(denominator,1e-12)
    return np.r_[interior[0],interior,interior[-1]]


def observed_reference_derivative_support(points,previous,lattice_info,image,blocked,opaque):
    """At most one observed past base node; never current road or output."""
    info=dict(reference_past_derivative_support_used=False)
    def reject(reason):
        return None,dict(info,reference_past_derivative_support_reason=reason)
    if not (lattice_info.get('reference_lattice_used',False)
        and lattice_info.get('reference_lattice_correspondence',False)
        and lattice_info.get('reference_lattice_matches',0)>=3):return reject('CURRENT_LATTICE_NOT_ACCEPTED')
    if previous is None or len(previous)<3:return reject('NO_PAST_OBSERVATION')
    points=np.asarray(points,np.float64);previous=np.asarray(previous,np.float64)
    if observed_reference_run_direction(points,previous)!=1:return reject('AMBIGUOUS_DIRECTION')
    pixel=math.hypot(1/1.3608,1/1.701);step=21./6.
    distances=np.linalg.norm(previous-points[0],axis=1);j=int(np.argmin(distances))
    if distances[j]>pixel or j==0:return reject('NO_ADJACENT_PAST_NODE')
    past=previous[j-1].copy();incoming=points[0]-past;outgoing=points[1]-points[0]
    gap=float(np.linalg.norm(incoming));forward=float(np.linalg.norm(outgoing))
    if not step-pixel<=gap<=step+pixel:return reject('PAST_NODE_SPACING')
    if forward<1e-6 or float(incoming@outgoing)/(gap*forward)<math.cos(.31):return reject('PAST_NODE_DIRECTION')
    # A visible contradiction vetoes the support. Vehicle occlusion or crop
    # does not convert an earlier observation into current road evidence.
    hidden=False
    for fraction in np.linspace(0.,1.,max(2,int(math.ceil(gap*1.701))+1)):
        point=(1.-fraction)*past+fraction*points[0]
        x=IMAGE_ORIGIN_X+1.3608*point[0];y=IMAGE_ORIGIN_Y-1.701*point[1]
        if not 1<=x<=82 or not 5<=y<=69:
            hidden=True;continue
        ix,iy=int(round(x)),int(round(y))
        if blocked[iy,ix]:return reject('CURRENT_OBSTACLE_CONTRADICTION')
        if opaque[iy,ix]:hidden=True;continue
        if not .36<float(image[iy,ix])<.47:return reject('CURRENT_MATERIAL_CONTRADICTION')
    return past,dict(info,reference_past_derivative_support_used=True,
        reference_past_derivative_support_reason='ONE_ADJACENT_OBSERVED_NODE',
        reference_past_derivative_current_hidden=hidden,
        reference_past_derivative_is_current_road_evidence=False)


def deform_reference_with_derivative_support(points,observed,source_stations,obstacles,past=None):
    """Apply the same current-object field and curvature, then discard past."""
    if past is None:
        deformed=deform_observed_reference(points,observed,source_stations,obstacles)
        return deformed,observed_reference_curvature(deformed)
    # The past node has an observed spatial-grid identity, not a copied old
    # obstacle deformation. Current dense/object coordinates define its field.
    supported=np.vstack((past,points))
    stations=np.r_[source_stations[0]-(21./6.),source_stations]
    deformed=deform_observed_reference(supported,observed,stations,obstacles)
    return deformed[1:],observed_reference_curvature(deformed)[1:]


def object_adjacent_asphalt(image,asphalt,flat,visible_obstacles):
    """Keep CURRENT road-colour plateaus beside a confirmed orange object.

    An object's contrast is not a road/grass edge. Ignore only its bounded,
    connected colour support when testing neighbouring observed road pixels;
    never add foreground, paint, hidden, or inferred road pixels.
    """
    if not visible_obstacles:return np.zeros(image.shape,bool)
    road_low=(102.-2.)/255.;road_high=(107.1+2.)/255.
    foreground=((image>road_high)&(image<176/255.)).astype(np.uint8)
    count,labels,stats,centers=cv2.connectedComponentsWithStats(foreground)
    ignore=np.zeros(image.shape,bool);bound=1.2+math.hypot(1/1.3608,1/1.701)
    for i in range(1,count):
        x,y,w,h,area=stats[i]
        if not (3<=area<=30 and min(w,h)>=2 and max(w,h)<=3*min(w,h)):continue
        component=labels==i
        if not np.any(component&(image>164/255.)):continue
        center=((centers[i,0]-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-centers[i,1])/1.701)
        if not any(np.linalg.norm(np.asarray(center)-p)<=bound for p,r in visible_obstacles):continue
        ignore|=component
    kernel=np.ones((3,3),np.uint8)
    high=cv2.dilate(np.where(ignore,0.,image).astype(np.float32),kernel)
    low=cv2.erode(np.where(ignore,1.,image).astype(np.float32),kernel)
    samples=cv2.filter2D((~ignore).astype(np.float32),-1,kernel,borderType=cv2.BORDER_CONSTANT)
    paint=cv2.dilate(((image<.35)|(image>.75)).astype(np.uint8),np.ones((3,9),np.uint8))>0
    candidate=(asphalt.astype(bool)&(image>=road_low)&(image<=road_high)&~ignore&~paint&~flat)
    candidate&=(high-low<=(5.1+2)/255.)&(samples>=4)
    # Recovery must be caused by an actual foreground neighbour. This cannot
    # relax the road/grass or paint test elsewhere in the scene.
    candidate&=cv2.dilate(ignore.astype(np.uint8),kernel)>0
    candidate[:5]=False;candidate[54:]=False;candidate[:,0]=False;candidate[:,-1]=False
    return candidate


OBJECT_SX=1.3608
OBJECT_SY=1.701
OBJECT_RADIUS=float(np.float32(1.2))
OBJECT_OLD_SOURCE_ERROR_M=3*math.hypot(84/1000/OBJECT_SX,84/800/OBJECT_SY)
# pygame2.6.1 SDL_gfx: vertex truncation sqrt(2), AA minor-axis support
# <=1+1000/65536, then source-pixel cell half-diagonal sqrt(2)/2.
# scale_mmx64.c 14-bit area steps shift X/Y edges by <=1/256,1/512.
# This unshifted-center bound requires the complete source shape unclipped.
OBJECT_SOURCE_ERROR_M=(1.5*math.sqrt(2)+1+1000/65536+math.hypot(1/256,1/512))/16.2
OBJECT_QUANTIZATION_GRAY=3.0

def _object_raster_samples(bounds,subdivisions):
    x0,y0,x1,y1=bounds
    yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
    u=(xx.ravel()+.5)*96/84-.5;v=(yy.ravel()+.5)*96/84-.5
    j=np.floor(u);k=np.floor(v);wx=u-j;wy=v-k
    side=84/96
    offsets=(np.arange(subdivisions)+.5)*side/subdivisions
    ax,ay=np.meshgrid(offsets,offsets)
    pts=[];weights=[]
    for dx in (0,1):
      for dy in (0,1):
        px=(j+dx)*side-.5;py=(k+dy)*side-.5
        pts.append(np.stack(((px[:,None]+ax.ravel())/OBJECT_SX,(py[:,None]+ay.ravel())/OBJECT_SY),axis=-1))
        w=((1-wx) if dx==0 else wx)*((1-wy) if dy==0 else wy)
        weights.append(np.broadcast_to(w[:,None]/subdivisions**2,(len(w),subdivisions**2)))
    sample_radius=.5*math.hypot(side/subdivisions/OBJECT_SX,side/subdivisions/OBJECT_SY)
    return np.concatenate(pts,axis=1),np.concatenate(weights,axis=1),sample_radius

def compatible_object_envelope(image,bounds,road_interval,cell_m=.075,subdivisions=8,refinements=1):
    """Return union of all surviving center cells, or reject.

    bounds is a fully observed, externally checked rectangular ROI in pixels.
    image is uint8 grayscale. road_interval is current enclosing-ring min/max.
    The caller must reject grass/paint/opaque/crop and keep collision disks.
    """
    x0,y0,x1,y1=map(int,bounds);roi=np.asarray(image)[y0:y1+1,x0:x1+1].astype(float)
    if roi.size==0 or x0<1 or x1>82 or y0<5 or y1>53:return dict(accepted=False,reason='ROI_VISIBILITY')
    bright=np.argwhere((roi>164)&(roi<176))
    if not len(bright):return dict(accepted=False,reason='NO_CURRENT_BRIGHT_CORE')
    lowroad,highroad=map(float,road_interval)
    if not 98<=lowroad<=highroad<=110 or highroad-lowroad>7.1:return dict(accepted=False,reason='ROAD_PLATEAU')
    # Every bright pixel must receive some object contribution. A source point
    # of its positive four-box kernel is within this radius of its pixel center.
    side=84/96
    kernel_error=math.hypot(1.5*side/OBJECT_SX,1.5*side/OBJECT_SY)
    reach=OBJECT_RADIUS+OBJECT_SOURCE_ERROR_M+kernel_error
    bx=(bright[:,1]+x0)/OBJECT_SX;by=(bright[:,0]+y0)/OBJECT_SY
    # Establish the no-clipping premise using the wider historical domain.
    # Reject the entire inference when any possible full center cell might
    # invoke SDL_gfx clipping; do not select only convenient interior aliases.
    old_reach=OBJECT_RADIUS+OBJECT_OLD_SOURCE_ERROR_M+kernel_error
    old_left=max(bx-old_reach);old_right=min(bx+old_reach)
    old_bottom=max(by-old_reach);old_top=min(by+old_reach)
    halo=(OBJECT_RADIUS+OBJECT_OLD_SOURCE_ERROR_M+cell_m/math.sqrt(2))*16.2
    raw_left=old_left*16.2+.5*1000/84-.5-halo
    raw_right=(old_right+cell_m)*16.2+.5*1000/84-.5+halo
    raw_near=799.5-((old_top+cell_m)*OBJECT_SY+.5)*800/84-halo
    raw_far=799.5-(old_bottom*OBJECT_SY+.5)*800/84+halo
    if not (1<raw_left<=raw_right<998 and 1<raw_near<=raw_far<798):
        return dict(accepted=False,reason='UNCERTAIN_SOURCE_CLIPPING')
    left=max(bx-reach);right=min(bx+reach);bottom=max(by-reach);top=min(by+reach)
    if left>right or bottom>top:return dict(accepted=False,reason='NO_CENTER_DOMAIN')
    xs=np.arange(left,right+cell_m,cell_m);ys=np.arange(bottom,top+cell_m,cell_m)
    centers=np.stack(np.meshgrid(xs,ys),axis=-1).reshape(-1,2)
    halfcell=cell_m/math.sqrt(2)
    tested=len(centers);observed=roi.ravel();best_violation=float('inf')
    # Each level is independently an outer enclosure. The inexpensive level
    # rejects contradictions before finer quadrature; all its unknown cells
    # reach the final level. No best-fit cell or orientation is selected.
    levels=(4,subdivisions) if subdivisions>4 else (subdivisions,)
    samples=[_object_raster_samples((x0,y0,x1,y1),level) for level in levels]
    for refinement in range(refinements+1):
        for points,weights,integration_error in samples:
            lower=max(0,OBJECT_RADIUS*math.cos(math.pi/16)-OBJECT_SOURCE_ERROR_M-integration_error-halfcell)
            upper=OBJECT_RADIUS+OBJECT_SOURCE_ERROR_M+integration_error+halfcell
            kept=[]
            for start in range(0,len(centers),32):
                c=centers[start:start+32]
                distance=np.linalg.norm(points[None,:,:,:]-c[:,None,None,:],axis=-1)
                fmin=np.sum((distance<=lower)*weights[None,:,:],axis=-1)
                fmax=np.sum((distance<=upper)*weights[None,:,:],axis=-1)
                predicted_low=lowroad+(173.1-lowroad)*fmin-OBJECT_QUANTIZATION_GRAY
                predicted_high=highroad+(173.1-highroad)*fmax+OBJECT_QUANTIZATION_GRAY
                violation=np.max(np.maximum(predicted_low-observed,observed-predicted_high),axis=1)
                best_violation=min(best_violation,float(violation.min()))
                kept.extend(c[violation<=0].tolist())
            if not kept:break
            centers=np.asarray(kept)
        if not kept:break
        if refinement<refinements:
            # Every parent square is partitioned into all four children.
            # Only pixel contradictions remove children; no alias is sampled.
            offsets=np.array([[-1,-1],[-1,1],[1,-1],[1,1]])*(cell_m/4)
            centers=(centers[:,None,:]+offsets[None,:,:]).reshape(-1,2)
            tested+=len(centers);cell_m*=.5;halfcell=cell_m/math.sqrt(2)
    if not kept:return dict(accepted=False,reason='NO_COMPATIBLE_CENTER',tested_center_cells=tested,best_violation_gray=best_violation)
    kept=np.array(kept);envelope_radius=OBJECT_RADIUS+halfcell
    return dict(accepted=True,compatible_center_cells=len(kept),tested_center_cells=tested,centers_world_pixel_origin=kept.tolist(),center_cell_half_diagonal_m=halfcell,
        silhouette_union_box_world_pixel_origin=[*(kept.min(axis=0)-envelope_radius),*(kept.max(axis=0)+envelope_radius)],
        source_raster_envelope_m=OBJECT_SOURCE_ERROR_M,quantization_gray=OBJECT_QUANTIZATION_GRAY,orientation='all, inscribed/circumscribed16gon',
        engineering_assumptions='Unclipped SDL_gfx quantization/AA, source-pixel cells and SSE area-edge drift are bounded separately; final arithmetic ±3gray unchanged. Caller validates full current road ring. Not a universal safety certificate.')


def detect_observed_obstacles(image,mixed=False):
    asphalt=((image>.36)&(image<.47)).astype(np.uint8)
    # For rechecking an ALREADY observed disk, a half-covered public orange
    # pixel can be below164: max road107.1, orange .299*255+.587*165=173.1.
    # New tracks still require the original164 threshold. The relaxed core
    # requires the same component/road guards AND an original bright pixel.
    lower=((107.1+(.299*255+.587*165))*.5)/255. if mixed else 164/255.
    bright=((image>lower)&(image<176/255.)).astype(np.uint8);bright[69:]=0
    count,labels,stats,centers=cv2.connectedComponentsWithStats(bright)
    obstacles=[];blocked=np.zeros((84,84),bool)
    for i in range(1,count):
        x,y,w,h,area=stats[i];cx,cy=centers[i];ix,iy=int(round(cx)),int(round(cy))
        patch=asphalt[max(0,iy-4):min(69,iy+5),max(0,ix-4):min(84,ix+5)]
        if mixed and not np.any((labels==i)&(image>164/255.)):continue
        if 3<=area<=30 and min(w,h)>=2 and max(w,h)<=3*min(w,h) and patch.size and np.mean(patch)>.42:
            obstacles.append((((cx-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-cy)/1.701),1.6))
            blocked[max(0,y-2):min(84,y+h+2),max(0,x-2):min(84,x+w+2)]=True
    return obstacles,blocked


def observed_object_road_patch(image,center,joint):
    """Infer pavement under a CURRENT fully surrounded public object.

    The closed two-pixel asphalt ring is observed. Its interior is a local
    road-continuity hypothesis, not observed pixels. A compatible16-gon raster
    must explain the whole ROI. Return its collision envelope separately.
    """
    px=IMAGE_ORIGIN_X+OBJECT_SX*center[0];py=IMAGE_ORIGIN_Y-OBJECT_SY*center[1]
    # Register the ROI to the CURRENT connected orange/road transition. A
    # fixed large crop can include an unrelated flank's grass even when a
    # smaller complete material contour has a closed pavement ring.
    foreground=((image>(107.1+2.)/255.)&(image<176/255.)).astype(np.uint8)
    count,labels,stats,centers=cv2.connectedComponentsWithStats(foreground)
    candidates=[]
    for i in range(1,count):
        x,y,w,h,area=stats[i]
        if not (3<=area<=30 and min(w,h)>=2 and max(w,h)<=3*min(w,h)):continue
        if not np.any((labels==i)&(image>164/255.)):continue
        distance=math.hypot((centers[i,0]-px)/OBJECT_SX,(centers[i,1]-py)/OBJECT_SY)
        if distance<=math.hypot(1/OBJECT_SX,1/OBJECT_SY):candidates.append((distance,x,y,w,h))
    if not candidates:return None
    _,x,y,w,h=min(candidates)
    # Three surrounding output pixels retain a two-pixel verified ring and
    # overlap its existing inset mesh; no fixed road crop is searched.
    x0=int(x)-3;x1=int(x+w-1)+3;y0=int(y)-3;y1=int(y+h-1)+3
    if x0<1 or x1>82 or y0<5 or y1>53:return None
    if np.any(vehicle_projection_mask(joint)[y0:y1+1,x0:x1+1]):return None
    roi=np.rint(image[y0:y1+1,x0:x1+1]*255.).astype(np.uint8)
    ring=np.ones(roi.shape,bool);ring[2:-2,2:-2]=False
    values=roi[ring].astype(float)
    if min(values)<100. or max(values)>109.1 or np.ptp(values)>7.1:return None
    # Source filters truncate positive RGB mixtures. Enumerating every final
    # channel-rounding breakpoint on grey<=109.1 -> orange(255,165,0) gives
    # RGB2GRAY<=173, including final resize rounding. The wider coverage
    # interval below must not excuse a different bright material.
    if min(roi.ravel())<100 or max(roi.ravel())>173:return None
    envelope=compatible_object_envelope(np.rint(image*255.).astype(np.uint8),
        (x0,y0,x1,y1),(float(min(values)),float(max(values))))
    if not envelope['accepted']:return None
    cells=np.asarray(envelope['centers_world_pixel_origin'])
    midpoint=(cells.min(axis=0)+cells.max(axis=0))*.5
    collision_center=(float(midpoint[0]-IMAGE_ORIGIN_X/OBJECT_SX),
        float(IMAGE_ORIGIN_Y/OBJECT_SY-midpoint[1]))
    collision_radius=OBJECT_RADIUS+envelope['center_cell_half_diagonal_m']+float(np.max(np.linalg.norm(cells-midpoint,axis=1)))
    cell_radius=OBJECT_RADIUS+envelope['center_cell_half_diagonal_m']
    cell_disks=[((float(p[0]-IMAGE_ORIGIN_X/OBJECT_SX),
        float(IMAGE_ORIGIN_Y/OBJECT_SY-p[1])),cell_radius) for p in cells]
    # Boundaries lie inside the CURRENT enclosing road plateau. Retain the
    # existing0.35m inward allowance on every edge of this inferred patch.
    left=(x0+1-IMAGE_ORIGIN_X)/OBJECT_SX+.35;right=(x1-1-IMAGE_ORIGIN_X)/OBJECT_SX-.35
    near=(IMAGE_ORIGIN_Y-(y1-1))/OBJECT_SY+.35;far=(IMAGE_ORIGIN_Y-(y0+1))/OBJECT_SY-.35
    if left>=right or near>=far:return None
    patch=np.array([[left,near],[right,near],[right,far],[left,far]])
    return patch,(collision_center,collision_radius),dict(
        compatible_center_cells=envelope['compatible_center_cells'],
        collision_envelope_radius_m=collision_radius,
        collision_cell_disks=cell_disks,
        source_raster_envelope_m=OBJECT_SOURCE_ERROR_M,
        quantization_gray=OBJECT_QUANTIZATION_GRAY,
        inferred_road_under_object=True,closed_current_asphalt_ring=True,
        observed_roi_pixels=[x0,y0,x1,y1],universal_bound=False)


def observed_object_plateau_connectors(image,patch,roi,roads,opaque):
    """Current plateau strips join independently inset representations.

    The explained object's ROI anchors the strips. A bounded continuation
    outside it needs current pixels at the same enclosing plateau levels;
    the object fit, inferred patch and collision exclusion stay unchanged.
    """
    sx,sy=OBJECT_SX,OBJECT_SY;ox,oy=IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y
    x0,y0,x1,y1=map(int,roi)
    if x0<1 or x1>82 or y0<5 or y1>53 or x1-x0<4 or y1-y0<4:return []
    view=image[y0:y1+1,x0:x1+1]
    ring=np.ones(view.shape,bool);ring[2:-2,2:-2]=False
    if not view.size or min(view[ring])<100/255. or max(view[ring])>109.1/255. or np.ptp(view[ring])>7.1/255.:return []
    paint=cv2.dilate(((image<.35)|(image>.75)).astype(np.uint8),np.ones((3,9),np.uint8))>0
    clear=(image>=100/255.)&(image<=109.1/255.)&~opaque.astype(bool)&~paint
    inset=.35
    # Existing patch begins one sample inside the outer ring. A connector's
    # inset footprint must extend strictly beyond that independently inset
    # line; derive the necessary strip depth from the unchanged metric inset.
    nx=int(math.floor(1+2*inset*sx))+1
    ny=int(math.floor(1+2*inset*sy))+1
    strips=[(x0,y0,x0+nx,y1,'vertical'),(x1-nx,y0,x1,y1,'vertical'),
            (x0,y0,x1,y0+ny,'horizontal'),(x0,y1-ny,x1,y1,'horizontal')]
    # Independent insets can leave the existing mesh just OUTSIDE the ROI.
    # Keep the old proposals and add only one inset-derived strip across each
    # flank. Every extra pixel must be visible and match the enclosing ring;
    # this extends observed pavement, not the object's hidden-road inference.
    strips.extend([(x0-nx,y0,x0+nx,y1,'vertical'),(x1-nx,y0,x1+nx,y1,'vertical'),
                   (x0,y0-ny,x1,y0+ny,'horizontal'),(x0,y1-ny,x1,y1+ny,'horizontal')])
    yy,xx=np.indices(image.shape)
    wx=(xx-ox)/sx;wy=(oy-yy)/sy;signs=[]
    for first,last in zip(patch,np.roll(patch,-1,axis=0)):
        signs.append((last[0]-first[0])*(wy-first[1])-(last[1]-first[1])*(wx-first[0]))
    signs=np.asarray(signs);in_patch=np.all(signs>=0.,axis=0)|np.all(signs<=0.,axis=0)
    # An already-supported overlap need not repeat the ring's shade. Current
    # grass/paint/object/opaque vetoes still apply throughout the whole strip.
    same_level=clear&(in_patch|((image>=min(view[ring]))&(image<=max(view[ring]))))
    def overlap(p,q):
        return cv2.intersectConvexConvex(np.asarray(p,np.float32),np.asarray(q,np.float32))[0]>1e-9
    connectors=[]
    for l,t,r,b,axis in strips:
        if l<1 or r>82 or t<5 or b>53:continue
        extended=l<x0 or r>x1 or t<y0 or b>y1
        allowed=same_level if extended else clear
        good=np.all(allowed[t:b+1,l:r+1],axis=1 if axis=='vertical' else 0)
        ends=np.diff(np.pad(good,(1,1)).astype(np.int16));starts=np.flatnonzero(ends==1);stops=np.flatnonzero(ends==-1)
        for start,stop in zip(starts,stops):
            a,c,d,e=(l,t+start,r,t+stop-1) if axis=='vertical' else (l+start,t,l+stop-1,b)
            values=image[c:e+1,a:d+1]
            if extended:values=values[~in_patch[c:e+1,a:d+1]]
            if not values.size:continue
            if np.ptp(values)>7.1/255.:continue
            left=(a-ox)/sx+inset;right=(d-ox)/sx-inset
            near=(oy-e)/sy+inset;far=(oy-c)/sy-inset
            if left>=right or near>=far:continue
            candidate=np.array([[left,near],[right,near],[right,far],[left,far]])
            if not overlap(candidate,patch) or not any(overlap(candidate,p) for p,g in roads):continue
            # Existing sampled geometry must actually have omitted part of
            # this current plateau; redundant strips add nothing to the map.
            old=[patch]+[np.asarray(p) for p,g in roads]
            iy,ix=np.mgrid[c:e+1,a:d+1]
            samples=np.column_stack(((ix.ravel()-ox)/sx,(oy-iy.ravel())/sy))
            samples=samples[(samples[:,0]>=left)&(samples[:,0]<=right)&(samples[:,1]>=near)&(samples[:,1]<=far)]
            if not len(samples):continue
            covered=lambda point:any(cv2.pointPolygonTest(np.asarray(p,np.float32),tuple(point),False)>=0 for p in old)
            if all(covered(point) for point in samples):continue
            connectors.append(candidate)
    return connectors


def update_observed_obstacles(image,detections,previous,joint):
    """Associate static observed disks; distinguish negative from hidden pixels.

    Memory is own-action transported. Partial/cropped centroids cannot overwrite
    a previously observed centre. Hidden objects remain estimates, not fresh
    observations, and never supply road pixels.
    """
    opaque=vehicle_projection_mask(joint).astype(bool);opaque[69:]=True
    bright=(image>164/255.)&(image<176/255.)
    yy,xx=np.indices(image.shape);tracks=[];used=set();counts=dict(observed=0,partial=0,hidden=0,negative=0)
    pixel_bound=math.hypot(1/1.3608,1/1.701)
    mixed,_=detect_observed_obstacles(image,mixed=True) if previous else ([],None)
    mixed_used=set()
    for old in previous:
        center=np.asarray(old['center'],np.float64)
        px=IMAGE_ORIGIN_X+1.3608*center[0];py=IMAGE_ORIGIN_Y-1.701*center[1]
        # Public radius1.2 plus a pixel's support covers a mixed edge sample.
        footprint=((xx-px)/1.3608)**2+((yy-py)/1.701)**2<=(1.2+pixel_bound)**2
        clipped=px-(1.2+pixel_bound)*1.3608<0 or px+(1.2+pixel_bound)*1.3608>83 or py-(1.2+pixel_bound)*1.701<0 or py+(1.2+pixel_bound)*1.701>68
        hidden=bool(clipped or np.any(footprint&opaque))
        visible=footprint&~opaque
        evidence=bool(np.any(visible&bright))
        candidates=[i for i,(p,r) in enumerate(detections) if i not in used and np.linalg.norm(np.asarray(p)-center)<=1.2+pixel_bound]
        match=min(candidates,key=lambda i:float(np.linalg.norm(np.asarray(detections[i][0])-center))) if candidates else None
        if match is not None:
            used.add(match)
            nearby=[i for i,(p,r) in enumerate(mixed) if i not in mixed_used and np.linalg.norm(np.asarray(p)-np.asarray(detections[match][0]))<=1.2+pixel_bound]
            if nearby:mixed_used.add(min(nearby,key=lambda i:float(np.linalg.norm(np.asarray(mixed[i][0])-np.asarray(detections[match][0])))))
            if hidden:status='partial'
            else:
                # A threshold-component centroid is a pixel-localized
                # measurement, not an exact physical disk centre. Preserve
                # an own-action prior still consistent with that CURRENT
                # measurement; otherwise project it into the observed box.
                measured=np.asarray(detections[match][0])
                pixel=np.array([1/1.3608,1/1.701])
                center=np.clip(center,measured-pixel,measured+pixel)
                status='observed'
        elif hidden:status='partial' if evidence else 'hidden'
        else:
            nearby=[i for i,(p,r) in enumerate(mixed) if i not in mixed_used and np.linalg.norm(np.asarray(p)-center)<=1.2+pixel_bound]
            if not nearby:counts['negative']+=1;continue
            mixed_used.add(min(nearby,key=lambda i:float(np.linalg.norm(np.asarray(mixed[i][0])-center))))
            status='partial'
        tracks.append(dict(center=center.tolist(),radius=old['radius'],status=status));counts[status]+=1
    for i,(center,radius) in enumerate(detections):
        if i not in used:tracks.append(dict(center=list(center),radius=radius,status='observed'));counts['observed']+=1
    return tracks,counts


# Public green HUD templates for integer polygon endpoints x400..600.
# Generated by retry.hud_joint_check from the public renderer; no case data.
JOINT_HUD_FEATURES=np.array([
    21.23137474,21.03529739,20.81176567,20.61176682,20.40000343,20.18823814,
    19.97255135,19.76862907,19.54902077,19.32156944,19.09019852,18.85490417,
    18.63529587,18.40000153,18.1725502,17.94509888,17.71764946,17.50196266,
    17.27843285,17.04706192,16.8196106,16.59215927,16.36078644,16.13333511,
    15.90588474,15.67843342,15.44706249,15.22353268,15.02353287,14.8196106,
    14.61176682,14.38431644,14.17255211,13.98431683,13.76470852,13.54902172,
    13.33725834,13.14902306,12.93725777,12.72549343,12.51372814,12.30588436,
    12.09412098,11.8862772,11.67451286,11.45882607,11.24706173,11.03529644,
    10.83921719,10.63921738,10.41176605,10.21961021,9.996080399,9.796080589,
    9.572550774,9.360786438,9.168629646,8.945100784,8.737257004,8.545100212,
    8.325491905,8.121570587,7.909804821,7.698039532,7.486274719,7.274509907,
    7.074509621,6.858823299,6.654901981,6.450980663,6.239215851,6.023530006,
    5.827451229,5.611764908,5.400000095,5.192157269,4.992156982,4.764706135,
    4.564705849,4.356862068,4.137254715,3.941176653,3.733333588,3.517647266,
    3.301960945,3.113725662,2.878431559,2.682353258,2.466667175,2.26274538,
    2.062745094,1.82745111,1.603921652,1.376470685,1.141176462,0.9215687513,
    0.6823529005,0.4588235319,0.231372565,0,-0.2078431547,-0.4392157197,
    -0.6666666865,-0.890196085,-1.129411817,-1.349019647,-1.584313869,-1.811764717,
    -2.035294294,-2.270588398,-2.470588207,-2.674510002,-2.890196323,-3.086274624,
    -3.321568489,-3.50980401,-3.72549057,-3.941176414,-4.149019718,-4.345098495,
    -4.564705849,-4.772549152,-4.976470947,-5.199999809,-5.403921604,-5.607842922,
    -5.819608212,-6.035294056,-6.231372833,-6.447059155,-6.658823967,-6.862745285,
    -7.06666708,-7.282352924,-7.48235321,-7.694118023,-7.905882359,-8.117647171,
    -8.32941246,-8.533332825,-8.752941132,-8.945098877,-9.152941704,-9.376470566,
    -9.568628311,-9.792157173,-10.00392151,-10.20392227,-10.42745113,-10.61960793,
    -10.84705925,-11.04705906,-11.24313736,-11.45490265,-11.66666698,-11.88235283,
    -12.09411812,-12.3019619,-12.51372528,-12.72156906,-12.93333435,-13.14509869,
    -13.35686302,-13.5450983,-13.75686264,-13.97254944,-14.19215775,-14.38039207,
    -14.59215736,-14.81960869,-15.02745247,-15.23137283,-15.4352951,-15.65490246,
    -15.88627434,-16.11372566,-16.34117699,-16.5686264,-16.79999924,-17.02745247,
    -17.25490379,-17.48627663,-17.70980644,-17.92549133,-18.15294075,-18.38039398,
    -18.6078434,-18.84313774,-19.06274605,-19.29804039,-19.52941322,-19.75686455,
    -19.97647095,-20.18039322,-20.39608002,-20.60784531,-20.81960869,-21.03137398,
    -21.24313927,-21.44705963,-21.6549015,
],np.float64)


SPEED_HUD_FEATURES=np.array([
    0.4274509847,0.6588235497,0.8745098114,1.094117761,1.313725591,1.525490403,
    1.741176605,1.964706063,2.184313774,2.403921604,2.619607687,2.843137503,
    3.058823824,3.27058816,3.49019599,3.705882311,3.925490141,4.149019718,
    4.360784531,4.584313869,4.800000191,5.011765003,5.23137331,5.458823681,
    5.666666985,5.882353306,6.105883121,6.325490475,6.552941799,6.760784626,
    6.972549438,7.18823576,7.40784359,7.62745142,7.847059727,8.062746048,
    8.290196419,8.498039246,8.72549057,8.960783958,
],np.float64)

YAW_HUD_FEATURES=np.array([
    10.84706116,10.737257,10.62353134,10.52549267,10.41568756,10.30980587,
    10.19608021,10.09019852,9.984315872,9.866668701,9.74902153,9.631374359,
    9.513727188,9.407845497,9.282354355,9.164707184,9.050981522,8.941178322,
    8.831374168,8.70588398,8.588236809,8.470590591,8.352942467,8.247060776,
    8.121569633,8.007844925,7.890198231,7.77255106,7.674511433,7.560786247,
    7.46274662,7.337256432,7.24313879,7.141178131,7.031374454,6.917649269,
    6.82745266,6.70588398,6.600001812,6.498040199,6.384315491,6.278432846,
    6.168628693,6.062746525,5.956864357,5.843138695,5.752942562,5.635295868,
    5.533334732,5.423530579,5.317647934,5.207843781,5.109805107,4.996079445,
    4.886275291,4.784315109,4.678432465,4.560785294,4.466668129,4.360785484,
    4.250980854,4.141177177,4.039216518,3.929412127,3.827450991,3.709804058,
    3.611764669,3.494117498,3.392156839,3.29019618,3.188235521,3.078431606,
    2.968627453,2.862745047,2.749019861,2.647058964,2.537255049,2.431372881,
    2.325490236,2.21568656,2.117646933,2.015686274,1.898039341,1.796078444,
    1.686274648,1.58431375,1.470588326,1.360784411,1.254902124,1.149019718,
    1.050980449,0.9372549653,0.8156862855,0.6980392337,0.5764706135,0.4627451301,
    0.3529411852,0.231372565,0.1176470593,0,-0.1058823541,-0.2235294133,
    -0.3372549117,-0.4588235319,-0.5686274767,-0.6823529601,-0.8039215803,-0.9215686321,
    -1.043137312,-1.156862855,-1.254902005,-1.360784411,-1.466666818,-1.576470733,
    -1.690196157,-1.792156935,-1.90196085,-2.003921747,-2.12156868,-2.223529577,
    -2.333333492,-2.431372643,-2.545098066,-2.643137217,-2.752941132,-2.854902267,
    -2.968627691,-3.074510098,-3.184313774,-3.294117928,-3.396078587,-3.498039484,
    -3.600000143,-3.717647076,-3.815686464,-3.933333635,-4.035294533,-4.145098209,
    -4.247059345,-4.356863499,-4.466666698,-4.572549343,-4.666666985,-4.784313679,
    -4.890196323,-5.000000477,-5.101960659,-5.215686321,-5.313725471,-5.423529148,
    -5.52941227,-5.639216423,-5.741177082,-5.858824253,-5.949019909,-6.062745571,
    -6.168627739,-6.274510384,-6.38431406,-6.490196705,-6.60392189,-6.705883026,
    -6.811765194,-6.933334351,-7.023530006,-7.137256145,-7.247059822,-7.349020481,
    -7.447059631,-7.568627834,-7.666667461,-7.780393124,-7.886275768,-7.996079445,
    -8.117648125,-8.227452278,-8.352942467,-8.458824158,-8.576472282,-8.694119453,
    -8.811765671,-8.937255859,-9.047060013,-9.156864166,-9.270589828,-9.388237,
    -9.513727188,-9.619609833,-9.73725605,-9.854903221,-9.972551346,-10.09019756,
    -10.19608021,-10.30196285,-10.41568851,-10.52157021,-10.63137436,-10.72941303,
    -10.84313869,-10.96470737,-11.05490398,
],np.float64)

def decode_motion_hud(image,predicted_speed,predicted_yaw):
    """Public source-pixel bins, conditioned on same-time own-action priors."""
    value=float(np.sum(image[76:83,10:14]))
    if abs(value)<=np.finfo(np.float32).eps*120:speed=0.;speed_interval=(0.,1e-4)
    else:
        errors=abs(SPEED_HUD_FEATURES-value);index=int(np.argmin(errors))
        if errors[index]<=np.finfo(np.float32).eps*120:
            low=2.5*index;high=2.5*(index+1)
            speed=(low+high)*.5 if predicted_speed is None else float(np.clip(predicted_speed,low,high))
            speed_interval=(low,high)
        else:speed=max(0.,value/.091728-2.5);speed_interval=None
    value=float(np.sum(image[75:81,54:63])-np.sum(image[75:81,63:72]))
    if abs(value)<=np.finfo(np.float32).eps*120:yaw=0.;yaw_interval=(-1e-4,1e-4)
    else:
        errors=abs(YAW_HUD_FEATURES-value);index=int(np.argmin(errors))
        if errors[index]<=np.finfo(np.float32).eps*120:
            endpoint=650+index;low=max(-5.,(749-endpoint)/20.);high=min(5.,(750-endpoint)/20.)
            yaw=(low+high)*.5 if predicted_yaw is None else float(np.clip(predicted_yaw,low,high))
            yaw_interval=(low,high)
        else:yaw=value/2.109744;yaw_interval=None
    return speed,yaw,speed_interval,yaw_interval


def decode_joint_hud(image,predicted):
    """Invert the public integer endpoint; retain a prediction inside its bin."""
    value=float(np.sum(image[75:81,32:42])-np.sum(image[75:81,42:52]))
    if abs(value)<=np.finfo(np.float32).eps*120:return 0.,(-1e-4,1e-4)
    errors=abs(JOINT_HUD_FEATURES-value);index=int(np.argmin(errors))
    # Only claim a quantization interval when the public template matches.
    if errors[index]>np.finfo(np.float32).eps*120:
        estimate=float(np.clip(value/51.7734,-.4,.4))
        return estimate,None
    endpoint=400+index;low=max(-.4,(499-endpoint)/250.);high=min(.4,(500-endpoint)/250.)
    estimate=(low+high)*.5 if predicted is None else float(np.clip(predicted,low,high))
    return estimate,(low,high)


def recover_pixel_edge(image,y,index,direction,blocked,max_row=55):
    """Invert a fully visible, monotone two-colour raster edge by area.

    Flat-step area gives a location estimate; resizing still has phase error.
    Plateau and monotonicity checks reject mixed materials, occlusion and
    clipped support. This is not a verified uncertainty bound.
    """
    ids=index+direction*np.arange(-3,5)
    if y>=max_row or min(ids)<0 or max(ids)>=84 or np.any(blocked[y,ids]):return None
    values=image[y,ids].astype(np.float64)
    quantum=1./255.
    if np.ptp(values[:2])>2*quantum or np.ptp(values[-2:])>2*quantum:return None
    outside=float(np.mean(values[:2]));inside=float(np.mean(values[-2:]))
    if not .36<inside<.47 or abs(inside-outside)<24*quantum:return None
    fraction=(values-outside)/(inside-outside)
    tolerance=quantum/abs(inside-outside)
    if min(fraction)<-tolerance or max(fraction)>1+tolerance or min(np.diff(fraction))<-tolerance:return None
    edge=4.5-float(np.sum(np.clip(fraction,0.,1.)))
    if not -2.5<=edge<=2.5:return None
    return float(index+direction*edge)


def recover_plain_run_edge(image,y,index,direction,blocked,paint_near,road_interval=None,max_row=55):
    """Place the same8-sample inversion on a visible road/grass transition."""
    # Inner plateau offsets are3,4. At most3 exterior shifts keep BOTH
    # samples in the original enclosing road run, including a steep raster.
    for exterior in range(4):
        anchor=index-direction*exterior
        ids=anchor+direction*np.arange(-3,5)
        if min(ids)<0 or max(ids)>=84 or paint_near[y,anchor]:continue
        if road_interval is not None and not all(road_interval[0]<=anchor+direction*k<road_interval[1] for k in (3,4)):continue
        if not 156/255.<=float(np.mean(image[y,ids[:2]]))<=184/255.:continue
        measured=recover_pixel_edge(image,y,anchor,direction,blocked,max_row=max_row)
        # Keep the original inversion-domain scale relative to the RAW run,
        # rather than silently expanding it with each search-window shift.
        if measured is not None and abs(measured-index)<=2.5:
            palette=recover_shaded_run_edge(image,y,anchor,direction,blocked)
            # A single-colour fit may overstate coverage at a shade seam.
            # Where the palette also explains the samples, keep the more
            # inward edge; the existing estimate is never expanded.
            if palette is not None:measured+=direction*max(0.,direction*(palette-measured))
            grass_palette=recover_grass_palette_edge(image,y,anchor,direction,blocked)
            if grass_palette is not None:measured+=direction*max(0.,direction*(grass_palette-measured))
            if abs(measured-index)>2.5:return None
            return measured
    # A public road-tile shade seam is not a reversed road/grass transition.
    # Only after every original constant-colour window fails, test the same
    # windows against the bounded public asphalt palette.
    for exterior in range(4):
        anchor=index-direction*exterior
        ids=anchor+direction*np.arange(-3,5)
        if min(ids)<0 or max(ids)>=84 or paint_near[y,anchor]:continue
        if road_interval is not None and not all(road_interval[0]<=anchor+direction*k<road_interval[1] for k in (3,4)):continue
        measured=recover_shaded_run_edge(image,y,anchor,direction,blocked)
        if measured is not None and abs(measured-index)<=2.5:
            grass_palette=recover_grass_palette_edge(image,y,anchor,direction,blocked)
            if grass_palette is not None:measured+=direction*max(0.,direction*(grass_palette-measured))
            if abs(measured-index)<=2.5:return measured
            return None
    # A checker-grass seam can vary outside the road as well. Preserve all
    # public grass shades only after both established inversions reject.
    for exterior in range(4):
        anchor=index-direction*exterior
        ids=anchor+direction*np.arange(-3,5)
        if min(ids)<0 or max(ids)>=84 or paint_near[y,anchor]:continue
        if road_interval is not None and not all(road_interval[0]<=anchor+direction*k<road_interval[1] for k in (3,4)):continue
        measured=recover_grass_palette_edge(image,y,anchor,direction,blocked)
        if measured is not None and abs(measured-index)<=2.5:return measured
    return None


def recover_shaded_run_edge(image,y,index,direction,blocked):
    """Conservative area edge from monotone COVERAGE, not constant road gray.

    Public asphalt tiles span102..107.1 before the raster arithmetic. Their
    existing two-gray allowance gives100..109.1 in pixels. Keep the original
    grass plateau, visibility, quantization and eight-sample support guards.
    """
    ids=index+direction*np.arange(-3,5);q=1/255.
    if y>=54 or min(ids)<0 or max(ids)>=84 or np.any(blocked[y,ids]):return None
    values=image[y,ids].astype(np.float64);grass=float(np.mean(values[:2]))
    low=100/255.;high=109.1/255.
    if np.ptp(values[:2])>2*q or not 156*q<=grass<=184*q:return None
    if min(values[-2:])<low or max(values[-2:])>high or np.ptp(values[-2:])>2*q:return None
    if grass-high<24*q:return None
    lower=np.clip((grass-values-q)/(grass-low),0.,1.)
    upper=np.clip((grass-values+q)/(grass-high),0.,1.)
    # A monotone coverage must explain EVERY observed sample. This retains
    # material contradictions instead of smoothing them into a passing edge.
    if np.any(values<low-q) or np.any(values>grass+q):return None
    lower=np.maximum.accumulate(lower);upper=np.minimum.accumulate(upper[::-1])[::-1]
    if np.any(lower>upper):return None
    # Minimum compatible road coverage puts the edge furthest into the road;
    # the ordinary0.35m flank inset is still applied by the caller.
    edge=4.5-float(np.sum(lower))
    if not -2.5<=edge<=2.5:return None
    return float(index+direction*edge)


def recover_grass_palette_edge(image,y,index,direction,blocked):
    """Inward area edge retaining both public checker-grass shade aliases.

    The original pixel palettes, quantization and inner-plateau guards remain.
    Gray can vary across the grass seam; road COVERAGE must be monotone and
    explain every sample. No single grass shade or best-fit edge is selected.
    """
    ids=index+direction*np.arange(-3,5);q=1/255.
    if y>=54 or min(ids)<0 or max(ids)>=84 or np.any(blocked[y,ids]):return None
    values=image[y,ids].astype(np.float64)
    low=100*q;high=109.1*q;grass_low=156*q;grass_high=184*q
    if min(values[:2])<grass_low or max(values[:2])>grass_high:return None
    if min(values[-2:])<low or max(values[-2:])>high or np.ptp(values[-2:])>2*q:return None
    if np.any(values<low-q) or np.any(values>grass_high+q):return None
    lower=np.clip((grass_low-values-q)/(grass_low-low),0.,1.)
    upper=np.clip((grass_high-values+q)/(grass_high-high),0.,1.)
    lower=np.maximum.accumulate(lower);upper=np.minimum.accumulate(upper[::-1])[::-1]
    if np.any(lower>upper):return None
    edge=4.5-float(np.sum(lower))
    if not -2.5<=edge<=2.5:return None
    return float(index+direction*edge)


def _raster_halfplane(ids,row,edges,slope):
    """Continuous-area 1000x800->96 filter followed by public84 linear resize."""
    u=(ids+.5)*96./84.-.5;j=np.floor(u);wx=u-j
    v=(row+.5)*96./84.-.5;k=math.floor(v);wy=v-k
    width=84./96.;result=np.zeros((len(edges),len(ids)),np.float64)
    for dx in (0,1):
        right=(j+dx+1)*width-.5
        for dy in (0,1):
            low=(k+dy)*width-.5;high=low+width
            t0=right[None,:]-edges[:,None]-slope*(low-row)
            if abs(slope)<1e-9:area=np.clip(t0,0.,width)/width
            else:
                t1=right[None,:]-edges[:,None]-slope*(high-row)
                primitive=lambda t:.5*(np.maximum(t,0.)**2-np.maximum(t-width,0.)**2)
                area=np.clip((primitive(t1)-primitive(t0))/(-slope*width*width),0.,1.)
            result+=area*((1-wx) if dx==0 else wx)[None,:]*((1-wy) if dy==0 else wy)
    return result


def observe_outer_edge(image,point,radial,blocked,reference=False):
    """Observe a plain contour along its2D normal, allowing public tile shades."""
    step=1/(2.7*6.);extent=16
    if reference:
        # Area96 support + linear96->84 support + remap84 support + source
        # antialias pixel. Add five source samples for actual flat plateaus.
        nx,ny=abs(radial[0]),abs(radial[1])
        pixel96=(nx*1000/96.+ny*800/96.)/(2.7*6.)
        pixel84=nx/1.3608+ny/1.701
        extent=int(math.ceil((1.5*pixel96+pixel84+step)/step))+5
    distance=np.arange(-extent,extent+1)*step
    world=np.asarray(point)[None,:]+distance[:,None]*np.asarray(radial)[None,:]
    xs=IMAGE_ORIGIN_X+1.3608*world[:,0];ys=IMAGE_ORIGIN_Y-1.701*world[:,1]
    if min(xs)<1 or max(xs)>82 or min(ys)<5 or max(ys)>=54:return None
    ix=np.rint(xs).astype(int);iy=np.rint(ys).astype(int)
    if np.any(blocked[iy,ix]):return None
    values=cv2.remap(image,xs.astype(np.float32)[None,:],ys.astype(np.float32)[None,:],cv2.INTER_LINEAR)[0].astype(float)
    inside=values[:5];outside=values[-5:];q=1/255.
    if min(inside)<=.36 or max(inside)>=.47 or np.ptp(inside)>(5.1+2)*q:return None
    if min(outside)<156*q or max(outside)>184*q or np.ptp(outside)>(26*.587+2)*q:return None
    road=float(np.median(inside));grass=float(np.median(outside))
    if grass-road<24*q:return None
    fraction=(values-road)/(grass-road);cross=np.flatnonzero((fraction[:-1]<.5)&(fraction[1:]>=.5))
    if len(cross)!=1:return None
    transition=fraction[(fraction>.1)&(fraction<.9)]
    if len(transition)<2 or min(np.diff(transition))<-2*q/(grass-road):return None
    i=int(cross[0]);delta=distance[i]+(.5-fraction[i])/(fraction[i+1]-fraction[i])*step
    return np.asarray(point)+delta*np.asarray(radial)


def recover_curb_edge(image,y,index,direction,slope,blocked):
    """Fit visible road/paint/grass layers; mixed-paint junctions stay unknown."""
    ids=index+direction*np.arange(-7,5)
    if y<2 or y>=54 or abs(slope)>1. or min(ids)<0 or max(ids)>=84:return None
    if np.any(blocked[y-1:y+2,ids]):return None
    patch=image[y-1:y+2,ids].astype(np.float64);q=1./255.
    if np.ptp(patch[:,:3])>3*q or np.ptp(patch[:,-2:])>3*q:return None
    grass=float(np.median(patch[:,:3]));road=float(np.median(patch[:,-2:]))
    if not .36<road<.47 or not 156*q<=grass<=184*q:return None
    white=np.max(patch)>grass+8*q;red=np.min(patch)<road-8*q
    if white==red:return None
    paint=1. if white else 76./255.
    edges=index+direction*np.linspace(-2.5,.5,49)
    # Public BORDER=8/6 metres; anisotropic84 projection of a normal offset.
    curb_width=(8./6.)*1.3608*math.sqrt(1.+(slope*1.701/1.3608)**2)
    predictions=[]
    for row in (y-1,y,y+1):
        edge=edges+slope*(row-y)
        inner=_raster_halfplane(ids,row,edge,slope)
        outer=_raster_halfplane(ids,row,edge-direction*curb_width,slope)
        if direction<0:inner=1-inner;outer=1-outer
        predictions.append(grass+(paint-grass)*outer+(road-paint)*inner)
    model=np.stack(predictions,axis=1);residual=model-patch[None,:,:]
    score=np.mean(residual**2,axis=(1,2));best=int(np.argmin(score))
    # One public high-resolution pixel of raster phase plus gray quantization.
    tolerance=2*q+(84./1000.)*max(abs(paint-road),abs(paint-grass))
    if math.sqrt(float(score[best]))>tolerance/2 or np.max(abs(residual[best]))>tolerance:return None
    return float(edges[best])


def observe_mixed_curb_edge(image,point,outward,blocked,grass_pixels=None):
    """Visible road/curb/grass inverse with a paint mixture per tangent ray.

    The public red/white tile junction can produce any effective gray between
    the two paint colors. Fit that nuisance color, not an asphalt threshold.
    All rays need visible road and grass plateaus; no hidden continuation.
    """
    nx,ny=float(outward[0]),float(outward[1])
    axis=0 if abs(nx/1.3608)>=abs(ny/1.701) else 1
    normal_axis=nx if axis==0 else ny;normal_other=ny if axis==0 else nx
    scale=1.3608 if axis==0 else -1.701;other_scale=-1.701 if axis==0 else 1.3608
    coordinate=IMAGE_ORIGIN_X+1.3608*point[0] if axis==0 else IMAGE_ORIGIN_Y-1.701*point[1]
    tangent=IMAGE_ORIGIN_Y-1.701*point[1] if axis==0 else IMAGE_ORIGIN_X+1.3608*point[0]
    index=int(round(coordinate));row=int(round(tangent));direction=-1 if normal_axis*scale>0 else 1
    slope=-(normal_other/other_scale)/(normal_axis/scale)
    if abs(slope)>1.000001:return None
    width=(8./6.)*abs(scale/normal_axis);rays=np.arange(row-1,row+2)
    if min(rays)<2 or max(rays)>81:return None
    # The coarse width-offset location is only a search anchor. A white tile
    # junction can hide the first grass plateau beyond the old fixed window.
    # Search to the public curb-width plus raster-support reach, accepting
    # only actual coherent grass and actual road plateaus on two rays.
    max_context=int(math.ceil(2*width+2*84./96.+3));q=1./255.;patch=None
    if grass_pixels is None:grass_pixels=coherent_grass_mask(image)
    for extent in range(7,max_context+1):
        ids=index+direction*np.arange(-extent,5)
        if min(ids)<2 or max(ids)>81:break
        yy,xx=np.meshgrid(ids,rays) if axis==1 else np.meshgrid(rays,ids,indexing='ij')
        if np.any(yy<5) or np.any(yy>=54) or np.any(blocked[yy,xx]):continue
        candidate=image[yy,xx].astype(np.float64)
        ray_grass=np.median(candidate[:,:3],axis=1);ray_road=np.median(candidate[:,-2:],axis=1)
        valid=(np.ptp(candidate[:,:3],axis=1)<=3*q)&(np.ptp(candidate[:,-2:],axis=1)<=7.1*q)
        valid&=(ray_road>.36)&(ray_road<.47)&(ray_grass>=156*q)&(ray_grass<=184*q)
        valid&=np.all(grass_pixels[yy[:,:3],xx[:,:3]],axis=1)
        if int(valid.sum())>=2:patch=candidate;break
    if patch is None:return None
    grass=float(np.median(ray_grass[valid]));road=float(np.median(ray_road[valid]))
    reach=int(math.ceil(width+1.));edges=index+direction*np.arange(-16*reach,9)/16.
    def predict(slope,width):
        models=[];paints=[]
        for ray in rays:
            edge=edges+slope*(ray-row)
            inner=_raster_halfplane(ids,int(ray),edge,slope)
            outer=_raster_halfplane(ids,int(ray),edge-direction*width,slope)
            if direction<0:inner=1-inner;outer=1-outer
            alpha=outer-inner;constant=ray_grass[int(ray-row+1)]*(1-outer)+ray_road[int(ray-row+1)]*inner
            target=patch[int(ray-row+1)]
            denominator=np.sum(alpha*alpha,axis=1)
            paint=np.sum(alpha*(target[None,:]-constant),axis=1)/np.maximum(denominator,1e-12)
            paint=np.clip(paint,76./255.,1.)
            models.append(constant+paint[:,None]*alpha);paints.append(paint)
        return np.stack(models,axis=1),paints
    model,paints=predict(slope,width)
    residual=model-patch[None,:,:]
    # Infer the local curb direction from individually visible material rays,
    # rather than imposing the opposite road contour's smoothed normal.
    tolerance=2*q+(84./1000.)*max(1.-road,1.-grass)
    located=[]
    for k,ray in enumerate(rays):
        if not valid[k]:continue
        scores=np.mean(residual[:,k,:]**2,axis=1)
        fits=np.flatnonzero((scores<=(tolerance/2)**2)&(np.max(abs(residual[:,k,:]),axis=1)<=tolerance))
        if not len(fits) or np.ptp(edges[fits])>1.:continue
        best=int(fits[np.argmin(scores[fits])])
        located.append((float(ray-row),float(edges[best]+slope*(ray-row))))
    if len(located)<2:return None
    positions=np.asarray(located);design=np.column_stack((np.ones(len(positions)),positions[:,0]))
    intercept,fitted_slope=np.linalg.lstsq(design,positions[:,1],rcond=None)[0]
    gradient=np.array([1.3608,-fitted_slope*(-1.701)]) if axis==0 else np.array([-fitted_slope*1.3608,-1.701])
    if float(gradient@np.asarray(outward))<0:gradient=-gradient
    gradient/=np.linalg.norm(gradient)
    if float(gradient@np.asarray(outward))<math.cos(.31):return None
    slope=float(fitted_slope)
    width=(8./6.)*math.hypot(abs(scale),slope*abs(other_scale))
    model,paints=predict(slope,width);residual=model-patch[None,:,:]
    # A junction can cut one ray along the normal. Two actual neighbouring
    # material rays must agree on the same edge; the third is an outlier,
    # never invented material support. Keep the original residual tolerance.
    ray_score=np.mean(residual**2,axis=2);ray_score[:,~valid]=float('inf')
    selected=np.argsort(ray_score,axis=1)[:,:2]
    chosen=np.take_along_axis(residual,selected[:,:,None],axis=1)
    score=np.mean(chosen**2,axis=(1,2));best=int(np.argmin(score))
    tolerance=2*q+(84./1000.)*max(1.-road,1.-grass)
    acceptable=(score<=(tolerance/2)**2)&(np.max(abs(chosen),axis=(1,2))<=tolerance)
    plausible=np.flatnonzero(acceptable)
    if not len(plausible) or np.ptp(edges[plausible])>1.:return None
    # Take the road-side plausible edge. The later map still uses its .35m
    # flank inset, plus the existing source-pixel/node-chord allowance below.
    edge=float(edges[plausible[np.argmax(direction*edges[plausible])]])
    edge+=direction*(84./1000.)
    denominator=normal_axis*scale-slope*normal_other*other_scale
    if abs(denominator)<1e-8:return None
    along=(edge+slope*(tangent-row)-coordinate)/denominator
    observed=np.asarray(point)+along*np.asarray(outward)
    return observed,dict(rms=float(math.sqrt(score[best])),paint_gray=[float(p[best]*255) for p in paints])


def observe_white_curb_inner(image,point,outward,blocked,grass_pixels=None):
    """Direct road/near-pure-white transition, independent of the outer curb.

    Actual material rays bracket the query within one public tile. A near-
    white ray anchors the material; a mixed neighbour uses its observed peak
    as a conservative paint level. Outer-curb pixels beyond the peak are not
    used. Corner and raster uncertainty are charged towards the road.
    """
    if grass_pixels is None:grass_pixels=coherent_grass_mask(image)
    nx,ny=outward;axis=0 if abs(nx/1.3608)>=abs(ny/1.701) else 1
    scale=1.3608 if axis==0 else -1.701;other_scale=-1.701 if axis==0 else 1.3608
    normal_axis=nx if axis==0 else ny;normal_other=ny if axis==0 else nx
    coordinate=IMAGE_ORIGIN_X+1.3608*point[0] if axis==0 else IMAGE_ORIGIN_Y-1.701*point[1]
    tangent=IMAGE_ORIGIN_Y-1.701*point[1] if axis==0 else IMAGE_ORIGIN_X+1.3608*point[0]
    index=int(round(coordinate));row=int(round(tangent));direction=-1 if normal_axis*scale>0 else 1
    slope=-(normal_other/other_scale)/(normal_axis/scale);q=1./255.
    reach=int(math.ceil((8./6.)*abs(scale/normal_axis)+2*84./96.+2))
    ids=index+direction*np.arange(-reach,6);tangent_reach=int(math.ceil((21./6.)*abs(other_scale)/2))
    rays=range(row-tangent_reach,row+tangent_reach+1)
    if min(ids)<2 or max(ids)>81 or row<3 or row>80:return None
    evidence=[]
    for ray in rays:
        yy,xx=(ids,np.full_like(ids,ray)) if axis==1 else (np.full_like(ids,ray),ids)
        if np.any(yy<5) or np.any(yy>=54) or np.any(blocked[yy,xx]):continue
        values=image[yy,xx].astype(np.float64);road=float(np.median(values[-3:]))
        if not .36<road<.47 or np.ptp(values[-3:])>7.1*q:continue
        peak=int(np.argmax(values[:-3]));paint=float(values[peak])
        if paint<=186*q or peak+4>=len(ids):continue
        neighbours=np.delete(values[max(0,peak-1):peak+2],peak-max(0,peak-1))
        if not len(neighbours):continue
        sample_ids=ids[peak:];samples=values[peak:]
        if np.any(grass_pixels[yy[peak:],xx[peak:]]):continue
        pure=paint>=253*q and max(neighbours)>=250*q
        evidence.append((ray,sample_ids,samples,road,paint,pure))
    # One near-pure white ray identifies the material. A neighbouring mixed
    # white/red ray may support its inner transition too. Its observed peak
    # is a conservative lower paint level, not an assumed pure255 plateau.
    if len(evidence)<2 or not any(e[-1] for e in evidence):return None
    # For an actually bracketed, monotone paint/road transition, integrated
    # edge area survives the public symmetric raster filters. A single
    # half-plane likelihood would be false at a rendered road-tile corner.
    locations=[]
    for ray,sample_ids,samples,road,paint,pure in evidence:
        if np.max(np.diff(samples))>7.1*q:continue
        fraction=np.clip((paint-samples)/(paint-road),0.,1.)
        edge=float(sample_ids[0]+direction*(len(samples)-.5-float(np.sum(fraction))))
        locations.append((ray,edge,len(samples)/(paint-road),pure))
    candidates=[]
    for i,first in enumerate(locations):
        for second in locations[i+1:]:
            if not min(first[0],second[0])<=row<=max(first[0],second[0]):continue
            span=abs(second[0]-first[0])/abs(other_scale)
            if span>21./6.:continue
            candidates.append((span,first,second))
    if not candidates:return None
    span,first,last=min(candidates,key=lambda x:x[0])
    slope=(last[1]-first[1])/(last[0]-first[0])
    edge=first[1]+slope*(row-first[0])
    gradient=np.array([1.3608,slope*1.701]) if axis==0 else np.array([-slope*1.3608,-1.701])
    magnitude=float(np.linalg.norm(gradient));normal=gradient/magnitude
    tangent_world=np.array([-normal[1],normal[0]])
    raster_support=(1.5*84./96.)*(abs(tangent_world[0])/1.3608+abs(tangent_world[1])/1.701)+1/(2.7*6.)
    # Engineering corner envelope from public node turn/spacing and actual
    # observed bracket. Its uncertainty is charged towards the road, never
    # used to fill past the observed material rays.
    slack=max(raster_support,span*.5)*math.tan(.31)*magnitude
    phase=84./(1000. if axis==0 else 800.)
    quantization=2*q*max(first[2],last[2])
    edge+=direction*(slack+phase+quantization)
    denominator=normal_axis*scale-slope*normal_other*other_scale
    if abs(denominator)<1e-8:return None
    along=(edge+slope*(tangent-row)-coordinate)/denominator
    observed=np.asarray(point)+along*np.asarray(outward)
    return observed,dict(rms=None,paint_gray=[255.],method='bracketed visible paint/road area centroid',
        engineering_edge_uncertainty_m=(slack+phase+quantization)/magnitude,
        universal_bound=False)


def visible_road_evidence(image):
    """Interior asphalt pixels actually seen, excluding opaque/HUD support."""
    mask=((image>.36)&(image<.47)).astype(np.uint8)
    mask[70:]=0;mask[55:70,34:51]=0
    return cv2.erode(mask,np.ones((3,3),np.uint8),iterations=1)


def register_road_frames(previous,current):
    """Observed rigid camera motion, with forward/backward pixel checks."""
    a=np.rint(previous*255).astype(np.uint8);b=np.rint(current*255).astype(np.uint8)
    mask=np.zeros((84,84),np.uint8);mask[5:70,2:82]=255;mask[54:70,33:52]=0
    points=cv2.goodFeaturesToTrack(a,128,.01,3,mask=mask)
    if points is None or len(points)<8:return None
    q,status,_=cv2.calcOpticalFlowPyrLK(a,b,points,None,winSize=(15,15),maxLevel=3)
    if q is None:return None
    back,reverse,_=cv2.calcOpticalFlowPyrLK(b,a,q,None,winSize=(15,15),maxLevel=3)
    if back is None:return None
    valid=status.ravel().astype(bool)&reverse.ravel().astype(bool)
    valid&=np.linalg.norm(back[:,0]-points[:,0],axis=1)<=.5
    if np.sum(valid)<8:return None
    p=points[valid,0].astype(np.float64);q=q[valid,0].astype(np.float64)
    for v in (p,q):v[:,0]=(v[:,0]-IMAGE_ORIGIN_X)/1.3608;v[:,1]=(IMAGE_ORIGIN_Y-v[:,1])/1.701
    transform,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=.25,maxIters=200,confidence=.99)
    if transform is None or inliers is None:return None
    keep=inliers.ravel().astype(bool);scale=math.hypot(transform[0,0],transform[1,0])
    if np.mean(keep)<.8 or not .98<=scale<=1.02:return None
    residual=np.linalg.norm(p@transform[:,:2].T+transform[:,2]-q,axis=1)
    if max(residual[keep])>.25:return None
    # Physical rigid transform -> anisotropic pixel transform.
    D=np.diag([1.3608,-1.701]);origin=np.array([IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y])
    linear=D@transform[:,:2]@np.linalg.inv(D)
    translation=origin+D@transform[:,2]-linear@origin
    return np.column_stack((linear,translation))


def vehicle_occluded_pixels(image):
    """Non-asphalt interior of the known opaque hull, not its whole box."""
    mask=np.zeros((84,84),np.uint8)
    for poly in (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4):
        points=np.array([(IMAGE_ORIGIN_X+1.3608*x*core.SIZE,
                          IMAGE_ORIGIN_Y-1.701*y*core.SIZE) for x,y in poly])
        cv2.fillPoly(mask,[np.rint(points).astype(np.int32)],1)
    mask=cv2.erode(mask,np.ones((3,3),np.uint8),iterations=1)
    return mask&(((image<=.36)|(image>=.47)).astype(np.uint8))


def vehicle_projection_mask(joint):
    """Public vehicle silhouette plus one output-pixel raster fringe."""
    mask=np.zeros((84,84),np.uint8)
    polys=[[(x*core.SIZE,y*core.SIZE) for x,y in p] for p in
           (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4)]
    for i,(x,y) in enumerate(core.WHEELPOS):
        polys.append(core.rectangle((x*core.SIZE,y*core.SIZE),joint if i<2 else 0.))
    for poly in polys:
        pixels=np.array([(IMAGE_ORIGIN_X+1.3608*x,IMAGE_ORIGIN_Y-1.701*y) for x,y in poly])
        cv2.fillPoly(mask,[np.rint(pixels).astype(np.int32)],1)
    return cv2.dilate(mask,np.ones((3,3),np.uint8),iterations=1)


def _rotated_extrema(dx,dy,lo,hi,axis):
    def f(t):return dx*math.cos(t)-dy*math.sin(t)if axis==0 else dx*math.sin(t)+dy*math.cos(t)
    phase=math.atan2(-dy,dx)if axis==0 else math.atan2(dx,dy)
    angles=[lo,hi]+[phase+k*math.pi for k in range(-3,4)if lo<=phase+k*math.pi<=hi]
    return min(map(f,angles)),max(map(f,angles))

def source_bbox_vehicle_cover(joint_interval):
    """Public part bounds through area/linear sampling, no output dilation.

    One observed HUD joint bin; the other three retain full mechanical limits.
    Assumes public kinematic wheel anchors and final zoom. This is an observer
    engineering enclosure, not a bound on Box2D constraint-position residuals.
    """
    other_intervals=((-0.4,0.4),)*3
    if joint_interval is None:return None,dict(reason='NO_CURRENT_JOINT_INTERVAL')
    intervals=[tuple(joint_interval)]+list(other_intervals)
    if len(intervals)!=4 or any(not all(map(math.isfinite,z))or z[0]>z[1]for z in intervals):return None,dict(reason='INVALID_JOINT_INTERVAL')
    boxes=[]
    def projected(xlo,ylo,xhi,yhi):
        return(math.floor(math.nextafter(500+16.2*xlo,-math.inf)),math.floor(math.nextafter(200+16.2*ylo,-math.inf)),math.floor(math.nextafter(500+16.2*xhi,math.inf))+1,math.floor(math.nextafter(200+16.2*yhi,math.inf))+1)
    for polygon in (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4):
        p=np.asarray(polygon)*core.SIZE;boxes.append(projected(p[:,0].min(),p[:,1].min(),p[:,0].max(),p[:,1].max()))
    for (cx,cy),(lo,hi)in zip(core.WHEELPOS,intervals):
        points=[(-.28,.54),(.28,.54),(.28,-.54),(-.28,-.54)]
        xx=[_rotated_extrema(x,y,lo,hi,0)for x,y in points];yy=[_rotated_extrema(x,y,lo,hi,1)for x,y in points]
        boxes.append(projected(cx*core.SIZE+min(z[0]for z in xx),cy*core.SIZE+min(z[0]for z in yy),cx*core.SIZE+max(z[1]for z in xx),cy*core.SIZE+max(z[1]for z in yy)))
    # Union audited fixedpoint SSE and ideal area-shrink source dependencies.
    i=np.arange(84,dtype=np.int64);j=(16*i+1)//14
    sx=16384*1000//96;sy=16384*800//96
    left=np.minimum(j*sx//16384,j*1000//96);right=np.maximum(((j+2)*sx+16383)//16384,((j+2)*1000+95)//96)
    top=np.minimum(j*sy//16384,j*800//96);bottom=np.maximum(((j+2)*sy+16383)//16384,((j+2)*800+95)//96)
    lowy=800-bottom;highy=800-top;cover=np.zeros((84,84),bool)
    for x0,y0,x1,y1 in boxes:cover|=(left[None,:]<x1)&(right[None,:]>x0)&(lowy[:,None]<y1)&(highy[:,None]>y0)
    return cover,dict(reason='PUBLIC_KINEMATIC_SOURCE_PART_AABB_AND_KERNEL',joint_intervals=intervals,source_boxes=boxes,cover_cells=int(cover.sum()),source_part_count=8,arbitrary_output_dilation=False,assumption='Body origin/camera and wheel anchors at public kinematic locations. All4 joints mechanically limited±.4; only left has currentHUD interval. Numerical position/limit residual and particles remain separate engineering uncertainty.')


def observed_connected_flank_component(image,asphalt,cover,obstacle,grass,runs,base_rows,slope):
    """Retain every connected current anchor window; fixed original gates."""
    info=dict(anchor_windows=[],matching_window_pairs=[],accepted=False)
    if not runs:return False,dict(info,reason='NO_RUNS')
    first,last=runs[0][0]-1,runs[-1][0]+1
    if not 0<=first<last<84 or first not in base_rows or last not in base_rows:return False,dict(info,reason='ORIGINAL_BRACKETS')
    if(last-first)/1.701*math.sqrt(1+(slope*1.701/1.3608)**2)>21/6:return False,dict(info,reason='ORIGINAL_TILE_SPAN')
    side=runs[0][1];samples=[];prev=None
    for i,(y,which,lo,hi)in enumerate(runs):
        if which!=side or side not in(0,1)or y!=first+1+i or y in base_rows or hi-lo!=2 or not 0<=lo<hi<=84:return False,dict(info,reason='RUN_STRUCTURE')
        if prev is not None and max(prev[0],lo)>=min(prev[1],hi):return False,dict(info,reason='RUN_DISCONNECTED')
        samples.extend((y,x)for x in range(lo,hi));prev=(lo,hi)
    def values_for(cells):
        yy=np.asarray([y for y,x in cells]);xx=np.asarray([x for y,x in cells]);values=image[yy,xx]
        okay=bool(np.all(asphalt[yy,xx])and np.all((values>.36)&(values<.47))and not np.any(cover[yy,xx])and not np.any(obstacle[yy,xx])and not np.any(grass[yy,xx]))
        return okay,values
    okay,blockvalues=values_for(samples)
    if not okay or np.ptp(blockvalues)>7.1/255:return False,dict(info,reason='CURRENT_BLOCK_MATERIAL')
    choices=[]
    for y,run in((first,runs[0]),(last,runs[-1])):
        lo,hi=run[2:4];left,right,a,b=base_rows[y];start,end=(left,a)if side==0 else(b,right+1);available=[]
        if end-start<3:return False,dict(info,reason='ORIGINAL_ANCHOR_LENGTH')
        for x in range(max(start,lo-1),min(end-1,hi)):
            # Strict overlap means4-connected; diagonal contact is insufficient.
            if max(x,lo)>=min(x+2,hi):continue
            okay,values=values_for([(y,x),(y,x+1)])
            compatible=bool(okay and np.ptp(np.r_[blockvalues,values])<=7.1/255)
            record=dict(row=y,lo=x,hi=x+2,gray=(values*255).tolist(),material_valid=okay,range_compatible=compatible)
            info['anchor_windows'].append(record)
            if compatible:available.append((x,values))
        choices.append(available)
    for x,firstvalues in choices[0]:
        for z,lastvalues in choices[1]:
            if np.ptp(np.r_[blockvalues,firstvalues,lastvalues])<=7.1/255:info['matching_window_pairs'].append(dict(first=[first,x,x+2],last=[last,z,z+2]))
    info['accepted']=bool(info['matching_window_pairs']);return info['accepted'],dict(info,reason='CONNECTED_CURRENT_ANCHOR_WINDOWS'if info['accepted']else'NO_MATCHING_ANCHOR_PAIR')


def observed_flank_component(image,asphalt,cover,obstacle_mask,grass,runs,base_rows,slope):
    """A current visible plateau bracketed by original corridor anchors.

    Sample availability is two-dimensional. The conditional road hypothesis,
    original anchor domain and existing one-tile continuation bound remain.
    No inferred row or historical pixel supplies a material sample.
    """
    if not runs:return False
    first,last=runs[0][0]-1,runs[-1][0]+1
    if not 0<=first<last<84 or first not in base_rows or last not in base_rows:return False
    distance=(last-first)/1.701*math.sqrt(1+(slope*1.701/1.3608)**2)
    if distance>21./6.:return False
    side=runs[0][1];samples=[];previous=None
    for i,(y,which,lo,hi) in enumerate(runs):
        if (which!=side or side not in (0,1) or y!=first+1+i or y in base_rows
            or hi-lo!=2 or not 0<=lo<hi<=84):return False
        if previous is not None and max(previous[0],lo)>=min(previous[1],hi):return False
        previous=(lo,hi);samples.extend((y,x) for x in range(lo,hi))
    for y,run in ((first,runs[0]),(last,runs[-1])):
        lo,hi=run[2:4];left,right,a,b=base_rows[y]
        start,end=(left,a) if side==0 else (b,right+1)
        if end-start<3 or lo<start or hi>end:return False
        samples.extend((y,x) for x in range(lo,hi))
    yy=np.asarray([p[0] for p in samples]);xx=np.asarray([p[1] for p in samples])
    values=image[yy,xx]
    return bool(np.all(asphalt[yy,xx]) and np.all((values>.36)&(values<.47))
        and not np.any(cover[yy,xx]) and not np.any(obstacle_mask[yy,xx])
        and not np.any(grass[yy,xx]) and np.ptp(values)<=7.1/255.)


def observed_extension_flank_bridge(image,asphalt,cover,obstacle,grass,rows,first,last,slope):
    """Bridge only between independently validated current plateau rows.

    Reuse the original connected-component gates on every two-column window
    of each original three-sample flank. Fits, width and tile-distance bounds
    remain the caller's original ones. No inferred pixels supply a sample.
    """
    if not rows:return False
    rows=sorted(rows,key=lambda r:r[0])
    for sy,l,r,a,b in (first,last):
        if not (0<=sy<84 and 3<=a and b+3<=84):return False
        for xs in (np.arange(a-3,a),np.arange(b,b+3)):
            values=image[sy,xs]
            if (not np.all(asphalt[sy,xs]) or np.any(cover[sy,xs])
                or np.any(obstacle[sy,xs]) or np.any(grass[sy,xs])
                or min(values)<=.36 or max(values)>=.47 or np.ptp(values)>7.1/255.):return False
    anchors={first[0]:first[1:],last[0]:last[1:]}
    for side in (0,1):
        paths=[[]]
        for sy,l,r,a,b in rows:
            start=a-3 if side==0 else b
            paths=[path+[(sy,side,x,x+2)] for path in paths for x in (start,start+1)]
        valid=0
        for path in paths:
            accepted,_=observed_connected_flank_component(image,asphalt,cover,obstacle,grass,path,anchors,slope)
            valid+=int(accepted)
        if not valid:return False
    return True


def infer_local_road_support(image,asphalt,obstacle_mask,joint,initializing,speed,
                             cover_override=None,connected_anchors=False):
    """Conditioned connected-road hypothesis, never obstacle-clearance proof."""
    cover=vehicle_projection_mask(joint)if cover_override is None else np.asarray(cover_override,np.uint8)
    candidates=[];continuation_candidates={};wide_union_rows=set();fov_rows=set();deferred_rows=set()
    flatness_halo=cv2.dilate(cover,np.ones((3,3),np.uint8))
    visible_grass=coherent_grass_mask(image)
    # Output-pixel quantization plus public per-node normal change. This is a
    # conditioning tolerance, not a universal geometric uncertainty bound.
    nominal=2*(40./6.)
    tolerance=2/1.3608+nominal*(1/math.cos(.31)-1)
    for y in np.flatnonzero(np.any(cover,axis=1)):
        row=asphalt[y].astype(bool)&~cover[y].astype(bool)
        d=np.diff(np.pad(row,(1,1)).astype(np.int16));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)
        all_starts,all_ends=starts,ends
        good=ends-starts>=3;starts=starts[good];ends=ends[good]
        left=[i for i in range(len(starts)) if ends[i]<=math.ceil(IMAGE_ORIGIN_X)]
        right=[i for i in range(len(starts)) if starts[i]>=math.floor(IMAGE_ORIGIN_X)]
        deferred=False
        if (not left or not right) and connected_anchors and not initializing:
            # A two-sample current flank is pending component evidence only.
            # It never seeds a fit or supplies an independent strict bracket.
            good=all_ends-all_starts>=2;starts=all_starts[good];ends=all_ends[good]
            left=[i for i in range(len(starts)) if ends[i]<=math.ceil(IMAGE_ORIGIN_X)]
            right=[i for i in range(len(starts)) if starts[i]>=math.floor(IMAGE_ORIGIN_X)]
            deferred=True
        if not left or not right:continue
        l=max(left,key=lambda i:ends[i]);r=min(right,key=lambda i:starts[i])
        a,b=int(ends[l]),int(starts[r])
        if a>=b:continue
        missing=~asphalt[y,a:b].astype(bool)
        if np.any(missing & ~cover[y,a:b].astype(bool)) or np.any(obstacle_mask[y,a:b]) or np.any(visible_grass[y,a:b]):continue
        clipped=starts[l]==0 or ends[r]>=84
        if (starts[l]>0 and cover[y,starts[l]-1]) or (ends[r]<84 and cover[y,ends[r]]):continue
        entry=(int(y),int(starts[l]),int(ends[r]-1),a,b)
        if deferred:
            continuation_candidates[int(y)]=entry;deferred_rows.add(int(y))
        elif clipped:continuation_candidates[int(y)]=entry;fov_rows.add(int(y))
        else:candidates.append(entry)
    support=np.zeros((84,84),np.uint8)
    info=dict(road_support_inference_mode='spawn_conditioned' if initializing else 'visible_boundary_continuity',
        road_support_inferred_pixels=0,spawn_prior_used=False,occluded_obstacle_clearance_proved=False,
        local_connected_road_hypothesis=True)
    if len(candidates)<3 or (initializing and speed>3.):return support,info
    y=np.array([r[0] for r in candidates],float);matrix=np.column_stack((y-IMAGE_ORIGIN_Y,np.ones(len(y))))
    left=np.array([r[1] for r in candidates],float);right=np.array([r[2] for r in candidates],float)
    lc=np.linalg.lstsq(matrix,left,rcond=None)[0];rc=np.linalg.lstsq(matrix,right,rcond=None)[0]
    if not initializing:
        # The pavement union can be wider than a lane at a merge. Use the
        # more consistent observed flank only to seed a direction estimate;
        # wide rows constrain containment, not an exact local lane boundary.
        residuals=(max(abs(matrix@lc-left)),max(abs(matrix@rc-right)))
        direction_seed=lc[0] if residuals[0]<=residuals[1] else rc[0]
        projection=1.3608*math.sqrt(1+(direction_seed*1.701/1.3608)**2)
        broad=(right-left)/projection>nominal+tolerance
        if np.any(broad):
            anchors=[]
            for entry,is_broad in zip(candidates,broad):
                if is_broad:continuation_candidates[entry[0]]=entry;wide_union_rows.add(entry[0])
                else:anchors.append(entry)
            candidates=anchors
            if len(candidates)<3:return support,info
            y=np.array([r[0] for r in candidates],float);matrix=np.column_stack((y-IMAGE_ORIGIN_Y,np.ones(len(y))))
            left=np.array([r[1] for r in candidates],float);right=np.array([r[2] for r in candidates],float)
            lc=np.linalg.lstsq(matrix,left,rcond=None)[0];rc=np.linalg.lstsq(matrix,right,rcond=None)[0]
    info['road_support_wide_union_rows']=len(wide_union_rows)
    # A red/white curb mixture can cross the asphalt brightness threshold
    # outside the physical edge. Treat that visible flank as a pixel interval
    # spanning the public curb width, rather than as an exact boundary sample.
    allowances=[]
    for side,coefficient in ((1,lc),(2,rc)):
        extra=(8./6.)*1.3608*math.sqrt(1+(coefficient[0]*1.701/1.3608)**2)
        limits=[]
        for row in candidates:
            sy,index=row[0],row[side]
            ys=slice(max(0,sy-1),min(84,sy+2));xs=slice(max(0,index-3),min(84,index+4))
            visible=(cover[ys,xs]==0)&~obstacle_mask[ys,xs]
            patch=image[ys,xs][visible]
            painted=bool(np.any(patch>.75) or np.any(patch<.35))
            limits.append(1.+extra if painted else 1.)
        allowances.append(np.asarray(limits))
    interval_fit_failed=bool(np.any(abs(matrix@lc-left)>allowances[0]) or np.any(abs(matrix@rc-right)>allowances[1]))
    if initializing and interval_fit_failed:return support,info
    info['painted_flank_interval_rows']=int(np.sum((allowances[0]>1.)|(allowances[1]>1.)))
    if interval_fit_failed or abs(lc[0]-rc[0])*(max(y)-min(y))>2.:
        if initializing:return support,info
        # Painted flanks are intervals, not exact point samples. Determine
        # whether a common direction can satisfy all existing flank intervals
        # before discarding the whole observed vehicle corridor. Failure of
        # one least-squares line is not infeasibility of those intervals.
        lower=-float('inf');upper=float('inf')
        for values,limits in ((left,allowances[0]),(right,allowances[1])):
            for i in range(len(y)):
                for j in range(i+1,len(y)):
                    gap=y[j]-y[i]
                    lower=max(lower,(values[j]-limits[j]-values[i]-limits[i])/gap)
                    upper=min(upper,(values[j]+limits[j]-values[i]+limits[i])/gap)
        if lower>upper:return support,info
        common=float(np.clip((lc[0]+rc[0])*.5,lower,upper));offsets=[]
        for values,limits in ((left,allowances[0]),(right,allowances[1])):
            lo=float(np.max(values-limits-common*(y-IMAGE_ORIGIN_Y)))
            hi=float(np.min(values+limits-common*(y-IMAGE_ORIGIN_Y)))
            if lo>hi+1e-10:return support,info
            offsets.append(float(np.clip(np.mean(values-common*(y-IMAGE_ORIGIN_Y)),lo,hi)))
        lc=np.asarray([common,offsets[0]]);rc=np.asarray([common,offsets[1]])
        info['road_support_interval_parallel_used']=True
        info['road_support_common_slope']=common
    slope=(lc[0]+rc[0])*.5
    normal_width=(right-left)/1.3608/math.sqrt(1+(slope*1.701/1.3608)**2)
    if initializing:
        if np.max(abs(normal_width-nominal))>tolerance:return support,info
    else:
        # Carry the already established paint-edge intervals through the
        # width test too. One common width must satisfy all anchor rows.
        spread=(allowances[0]+allowances[1])/1.3608/math.sqrt(1+(slope*1.701/1.3608)**2)
        lower=max(nominal-tolerance,float(max(normal_width-spread)))
        upper=min(nominal+tolerance,float(min(normal_width+spread)))
        if lower>upper:return support,info
        info['road_support_width_interval_used']=bool(np.max(abs(normal_width-nominal))>tolerance)
    if initializing:
        # Spawn centering/orientation is never assumed after the first action.
        if abs((lc[1]+rc[1])*.5-IMAGE_ORIGIN_X)>1. or abs(slope*1.701/1.3608)>math.tan(.31):return support,info
        info['spawn_prior_used']=True
    # Interior two-sample rows retain the original component recovery path.
    # Deferred continuation must not hide them from that independent pass.
    interior_deferred={sy for sy in deferred_rows if min(y)<=sy<=max(y)}
    for sy in interior_deferred:continuation_candidates.pop(sy)
    deferred_rows-=interior_deferred
    inference_rows=list(candidates);extension_rows=[]
    if not initializing:
        # Crop-limited or broader pavement gives an inclusion constraint.
        # Extend only a consecutive end of an already validated corridor,
        # within one public tile step and with real asphalt beside the car.
        limits=(float(max(allowances[0])),float(max(allowances[1])))
        for edge_row,direction in ((int(min(y)),-1),(int(max(y)),1)):
            anchor_entry=next(entry for entry in candidates if entry[0]==edge_row)
            sy=edge_row+direction
            while sy in continuation_candidates:
                distance=abs(sy-edge_row)/1.701*math.sqrt(1+(slope*1.701/1.3608)**2)
                if distance>21./6.:break
                entry=continuation_candidates[sy];_,l,r,a,b=entry
                left_safe=lc[0]*(sy-IMAGE_ORIGIN_Y)+lc[1]+limits[0]
                right_safe=rc[0]*(sy-IMAGE_ORIGIN_Y)+rc[1]-limits[1]
                if left_safe>a or right_safe<b-1 or l>left_safe or r<right_safe:break
                plateaus=(image[sy,a-3:a],image[sy,b:b+3])
                if sy in deferred_rows or any(len(v)!=3 or min(v)<=.36 or max(v)>=.47 or np.ptp(v)>7.1/255. for v in plateaus):
                    if not connected_anchors:break
                    pending=[entry];probe=sy+direction;next_anchor=None
                    while probe in continuation_candidates:
                        distance=abs(probe-edge_row)/1.701*math.sqrt(1+(slope*1.701/1.3608)**2)
                        if distance>21./6.:break
                        following=continuation_candidates[probe];_,pl,pr,pa,pb=following
                        ls=lc[0]*(probe-IMAGE_ORIGIN_Y)+lc[1]+limits[0]
                        rs=rc[0]*(probe-IMAGE_ORIGIN_Y)+rc[1]-limits[1]
                        if ls>pa or rs<pb-1 or pl>ls or pr<rs:break
                        values=(image[probe,pa-3:pa],image[probe,pb:pb+3])
                        if probe not in deferred_rows and all(len(v)==3 and min(v)>.36 and max(v)<.47 and np.ptp(v)<=7.1/255. for v in values):
                            next_anchor=following;break
                        pending.append(following);probe+=direction
                    if next_anchor is None or not observed_extension_flank_bridge(
                        image,asphalt,cover,obstacle_mask,visible_grass,pending,anchor_entry,next_anchor,slope):break
                    for added in pending+[next_anchor]:
                        inference_rows.append(added);extension_rows.append(added[0])
                    anchor_entry=next_anchor;sy=probe+direction
                    continue
                inference_rows.append(entry);extension_rows.append(sy);anchor_entry=entry;sy+=direction
    info['road_support_fov_extension_rows']=sum(sy in fov_rows for sy in extension_rows)
    info['road_support_union_extension_rows']=len(extension_rows)
    info['road_support_merge_extension_rows']=sum(sy in wide_union_rows for sy in extension_rows)
    # A conservative fringe can leave a narrow but continuously observed
    # flank. Validate its CURRENT 2D component atomically, rather than treating
    # every row as independent material evidence or adding isolated-row cases.
    # Original fits and anchors never depend on these recovered rows.
    interior_rows=[];component_count=0
    if not initializing:
        base_rows={entry[0]:entry[1:] for entry in candidates}
        occupied={entry[0] for entry in inference_rows}|set(continuation_candidates)
        current=(image>.36)&(image<.47)
        width_lower,width_upper=lower,upper
        denominator=1.3608*math.sqrt(1+(slope*1.701/1.3608)**2)
        proposals=[]
        for sy in range(min(base_rows)+1,max(base_rows)):
            if sy in occupied:continue
            row=current[sy]&~cover[sy].astype(bool)
            edges=np.diff(np.pad(row,(1,1)).astype(np.int16))
            starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
            left=[i for i in range(len(starts)) if ends[i]<=math.ceil(IMAGE_ORIGIN_X) and ends[i]-starts[i]>=2]
            right=[i for i in range(len(starts)) if starts[i]>=math.floor(IMAGE_ORIGIN_X) and ends[i]-starts[i]>=2]
            if not left or not right:continue
            l=max(left,key=lambda i:ends[i]);r=min(right,key=lambda i:starts[i])
            lengths=(int(ends[l]-starts[l]),int(ends[r]-starts[r]))
            if not ((lengths[0]==2 and lengths[1]>=3) or (lengths[1]==2 and lengths[0]>=3)):continue
            short=l if lengths[0]==2 else r
            a,b=int(ends[l]),int(starts[r]);outer_left=int(starts[l]);outer_right=int(ends[r]-1)
            if a>=b or outer_left==0 or ends[r]>=84:continue
            if cover[sy,outer_left-1] or cover[sy,outer_right+1]:continue
            if (np.any((~current[sy,a:b])&~cover[sy,a:b].astype(bool)) or
                np.any(obstacle_mask[sy,a:b]) or np.any(visible_grass[sy,a:b])):continue
            limits=[]
            for index,coefficient in ((outer_left,lc),(outer_right,rc)):
                ys=slice(sy-1,sy+2);xs=slice(max(0,index-3),min(84,index+4))
                visible=(cover[ys,xs]==0)&~obstacle_mask[ys,xs]
                patch=image[ys,xs][visible]
                painted=bool(np.any(patch>.75) or np.any(patch<.35))
                extra=(8./6.)*1.3608*math.sqrt(1+(coefficient[0]*1.701/1.3608)**2)
                limits.append(1.+extra if painted else 1.)
            if (abs(lc[0]*(sy-IMAGE_ORIGIN_Y)+lc[1]-outer_left)>limits[0] or
                abs(rc[0]*(sy-IMAGE_ORIGIN_Y)+rc[1]-outer_right)>limits[1]):continue
            width=(outer_right-outer_left)/denominator;spread=sum(limits)/denominator
            proposals.append(((sy,outer_left,outer_right,a,b),
                (sy,0 if short==l else 1,int(starts[short]),int(ends[short])),
                width-spread,width+spread))
        groups=[]
        for proposal in proposals:
            if not groups or proposal[0][0]!=groups[-1][-1][0][0]+1:groups.append([])
            groups[-1].append(proposal)
        for group in groups:
            runs=[proposal[1] for proposal in group]
            if connected_anchors:
                accepted,_=observed_connected_flank_component(image,asphalt,cover,obstacle_mask,
                    visible_grass,runs,base_rows,slope)
            else:
                accepted=observed_flank_component(image,asphalt,cover,obstacle_mask,visible_grass,
                    runs,base_rows,slope)
            if not accepted:continue
            lo=max(width_lower,max(proposal[2] for proposal in group))
            hi=min(width_upper,min(proposal[3] for proposal in group))
            if lo>hi:continue
            width_lower,width_upper=lo,hi;component_count+=1
            interior_rows.extend(proposal[0] for proposal in group)
        inference_rows.extend(interior_rows)
    info['road_support_flank_component_rows']=len(interior_rows)
    info['road_support_flank_components']=component_count
    for sy,l,r,a,b in inference_rows:
        support[sy,a:b]=cover[sy,a:b]
        # The 3x3 flatness test loses one pixel beside an opaque object. Within
        # the already conditioned corridor, preserve actual asphalt samples in
        # that operator's halo; do not infer any additional hidden pixels.
        support[sy,l:r+1]|=asphalt[sy,l:r+1]&flatness_halo[sy,l:r+1]
    # Flatness is a2D operator: accepted car support also conditions its
    # vertical halo. Preserve only already visible asphalt there; no extra
    # opaque pixel is inferred outside the accepted corridor.
    conditioned=cv2.dilate(support&cover,np.ones((3,3),np.uint8))
    accepted_rows=np.zeros(84,bool);accepted_rows[[r[0] for r in inference_rows]]=True
    accepted_rows[max(0,min(r[0] for r in inference_rows)-1)]=True
    accepted_rows[min(83,max(r[0] for r in inference_rows)+1)]=True
    conditioned[~accepted_rows]=0  # Never carry support across an internal rejected row.
    support|=asphalt&conditioned&flatness_halo
    support[obstacle_mask]=0
    info['road_support_inferred_pixels']=int(np.sum(support&~asphalt.astype(bool)))
    if connected_anchors:
        info['current_two_flank_rows']=[list(v) for v in inference_rows if v[0] not in deferred_rows]
    return support,info


def coherent_grass_mask(image):
    """Grass-coloured plateaus, including a one-output-pixel raster fringe.

    A lone grey sample can also be a red/white paint mixture. Only a visible
    flat2x2 grass-colour patch supplies material evidence here. Thin unseen
    grass and overlapping road branches remain an unresolved ambiguity.
    """
    grass=(image>=156/255.)&(image<=184/255.)
    plateau=np.zeros((84,84),np.uint8)
    low=np.minimum.reduce((image[:-1,:-1],image[1:,:-1],image[:-1,1:],image[1:,1:]))
    high=np.maximum.reduce((image[:-1,:-1],image[1:,:-1],image[:-1,1:],image[1:,1:]))
    flat=(low>=156/255.)&(high<=184/255.)&(high-low<=3/255.)
    for dy in (0,1):
        for dx in (0,1):plateau[dy:83+dy,dx:83+dx]|=flat
    return grass&(cv2.dilate(plateau,np.ones((3,3),np.uint8))>0)


def extend_reference_contour(image,points,center,blocked):
    """Follow actual plain edge pixels with a local predictor, for reference only.

    A coarse circle may miss an otherwise visible variable-curvature edge.
    Local predictions are search locations only; only successful road/grass
    pixel observations are retained. Geometry allowances remain untouched.
    """
    points=np.asarray(points,np.float64);center=np.asarray(center,np.float64)
    angles=np.arctan2(points[:,1]-center[1],points[:,0]-center[0])
    anchor=math.atan2(float(np.mean(np.sin(angles))),float(np.mean(np.cos(angles))))
    angles=anchor+(angles-anchor+math.pi)%(2*math.pi)-math.pi
    chain=points[np.argsort(angles)]
    keep=np.r_[True,np.linalg.norm(np.diff(chain,axis=0),axis=1)>1/(2.7*6.)]
    chain=chain[keep];step=(21./6.)/4;window=2*(21./6.)
    limit=int(math.ceil(math.hypot(84/1.3608,84/1.701)/step));added=0
    for direction in (-1,1):
        sequence=chain[::-1].copy() if direction<0 else chain.copy()
        for _ in range(limit):
            arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(sequence,axis=0),axis=1))]
            distance=arc-arc[-1];selected=distance>=-window
            if int(np.sum(selected))<7 or -min(distance[selected])<21./6.:break
            z=distance[selected]/window;matrix=np.column_stack((np.ones(len(z)),z,z*z))
            if np.linalg.cond(matrix)>100.:break
            coef=np.linalg.lstsq(matrix,sequence[selected],rcond=None)[0]
            if np.max(np.linalg.norm(matrix@coef-sequence[selected],axis=1))>.35:break
            length=float(np.linalg.norm(coef[1]))
            if length<1.:break
            normal=np.array([coef[1,1],-coef[1,0]])/length
            if float(normal@(sequence[-1]-center))<0:normal=-normal
            advance=step/window;guess=sequence[-1]+advance*coef[1]+advance*advance*coef[2]
            observed=observe_outer_edge(image,guess,normal,blocked,reference=True)
            if observed is None:break
            if min(np.linalg.norm(sequence-observed,axis=1))<.5*step:break
            candidate=np.vstack((sequence,observed));theta=np.arctan2(candidate[:,1]-center[1],candidate[:,0]-center[0])
            theta=anchor+(theta-anchor+math.pi)%(2*math.pi)-math.pi
            if max(theta)-min(theta)>math.pi:break
            sequence=candidate;added+=1
        chain=sequence[::-1].copy() if direction<0 else sequence
    return chain,added


def offset_observed_contour(points,center,radius):
    """Local quadratic tangents, then the public width offset; no circle offset.

    The coarse circle supplies only a monotone parameter and observed-edge
    search rays. Every local fit uses actual visible contour samples on both
    sides. Residual/chord/raster allowances are engineering priors, not bounds.
    """
    points=np.asarray(points,np.float64);center=np.asarray(center,np.float64)
    angles=np.arctan2(points[:,1]-center[1],points[:,0]-center[0])
    anchor=math.atan2(float(np.mean(np.sin(angles))),float(np.mean(np.cos(angles))))
    angles=anchor+(angles-anchor+math.pi)%(2*math.pi)-math.pi
    order=np.argsort(angles);angles=angles[order];points=points[order]
    step=21./6.;half_window=2*step;nominal=2*(40./6.)
    contour=[];residuals=[];centres=[]
    for angle in np.arange(float(min(angles)),float(max(angles)),.05):
        distance=(angles-angle)*radius;selected=abs(distance)<=half_window
        if int(np.sum(selected))<7:continue
        q=distance[selected]
        both_sides=min(q)<=-step and max(q)>=step
        z=q/half_window;matrix=np.column_stack((np.ones(len(z)),z,z*z))
        if np.linalg.cond(matrix)>100.:continue
        coefficients=np.linalg.lstsq(matrix,points[selected],rcond=None)[0]
        residual=float(np.max(np.linalg.norm(matrix@coefficients-points[selected],axis=1)))
        if residual>.35:continue
        tangent=coefficients[1];length=float(np.linalg.norm(tangent))
        if length<1.:continue
        normal=np.array([tangent[1],-tangent[0]])/length
        if float(normal@(coefficients[0]-center))<0:normal=-normal
        # A one-sided endpoint tangent can turn the offset reference backward
        # even with a small fit residual. Require the same observed +/-step
        # bracket for reference targets and robust contour geometry.
        if not both_sides:continue
        centre=coefficients[0]-.5*nominal*normal
        centres.append((float(centre[0]),float(centre[1]),float(angle)))
        uncertainty=residual+nominal*(1-math.cos(.31/2))+1/(2.7*6.)
        inner=coefficients[0]-(nominal-uncertainty)*normal
        outer_safe=coefficients[0]-uncertainty*normal
        contour.append((float(inner[0]),float(inner[1]),float(angle),float(outer_safe[0]),float(outer_safe[1])));residuals.append(residual)
    return contour,residuals,centres


def observed_reference_edge_normals(points,center):
    """Local normals of actual observations, retained for next-frame matching."""
    points=np.asarray(points,np.float64)
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    kept=[];normals=[];window=2*(21./6.)
    for i,point in enumerate(points):
        distance=arc-arc[i];selected=abs(distance)<=window
        if int(sum(selected))<7:continue
        z=distance[selected]/window;matrix=np.column_stack((np.ones(len(z)),z,z*z))
        if np.linalg.cond(matrix)>100.:continue
        coef=np.linalg.lstsq(matrix,points[selected],rcond=None)[0]
        if max(np.linalg.norm(matrix@coef-points[selected],axis=1))>.35:continue
        tangent=coef[1];length=float(np.linalg.norm(tangent))
        if length<1.:continue
        normal=np.array([tangent[1],-tangent[0]])/length
        if normal@(point-center)<0:normal=-normal
        kept.append(point);normals.append(normal)
    return np.asarray(kept).reshape(-1,2),np.asarray(normals).reshape(-1,2)


def reobserve_reference_chain(image,seed,blocked):
    """Current edge correspondence can supply order without a global circle.

    History supplies search locations and outward signs only. Fit actual current
    observations in measured arc length with the existing local-fit guards.
    This reference-only path contributes no road or footprint support.
    """
    points=[];signs=[];runs=[]
    for point,normal in zip(seed['edge_points'],seed['edge_normals']):
        current=observe_outer_edge(image,point,normal,blocked,reference=True)
        if current is None:
            if points:runs.append((points,signs));points=[];signs=[]
            continue
        if points and np.linalg.norm(current-points[-1])<1/(2.7*6.):continue
        points.append(current);signs.append(normal)
    if points:runs.append((points,signs))
    curves=[];window=2*(21./6.)
    for points,signs in runs:
        if len(points)<7:continue
        points=np.asarray(points);signs=np.asarray(signs)
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        centres=[];kept=[];normals=[]
        for i,point in enumerate(points):
            distance=arc-arc[i];selected=abs(distance)<=window
            if int(sum(selected))<7:continue
            z=distance[selected]/window;matrix=np.column_stack((np.ones(len(z)),z,z*z))
            if np.linalg.cond(matrix)>100.:continue
            coef=np.linalg.lstsq(matrix,points[selected],rcond=None)[0]
            if max(np.linalg.norm(matrix@coef-points[selected],axis=1))>.35:continue
            length=float(np.linalg.norm(coef[1]))
            if length<1.:continue
            normal=np.array([coef[1,1],-coef[1,0]])/length
            if normal@signs[i]<0:normal=-normal
            centre=coef[0]-(40./6.)*normal
            centres.append((float(centre[0]),float(centre[1]),float(arc[i])))
            kept.append(point);normals.append(normal)
        if len(centres)>=3:
            curves.append(dict(outer_side=seed['outer_side'],points=centres,
                edge_points=np.asarray(kept),edge_normals=np.asarray(normals),
                current_edge_matches=len(points),current_edge_new_observations=0,
                current_near_edge_observations=0,reference_parameter='current observed edge arc'))
    return curves


def near_vehicle_reference_edges(image,asphalt,blocked):
    """Follow the vehicle's near corridor forward, not a merge's far midpoint.

    Actual near-car exterior pixels constrain the reference only. Starting
    from the forward road union's midpoint can select the other leg of a bend.
    """
    contours=[[],[]];anchor=IMAGE_ORIGIN_X
    for y in range(68,54,-1):
        d=np.diff(np.pad(asphalt[y],(1,1)).astype(np.int16));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)
        good=ends-starts>=8;starts=starts[good];ends=ends[good]
        if not len(starts):continue
        outside=np.maximum(starts-anchor,0)+np.maximum(anchor-ends,0)
        j=int(np.argmin(3*outside+.1*abs((starts+ends-1)*.5-anchor)))
        if outside[j]>8:break
        left,right=int(starts[j]),int(ends[j]-1);anchor=(left+right)*.5
        for side,index,direction in ((0,left,1),(1,right,-1)):
            ids=index+direction*np.arange(-3,5)
            if min(ids)<0 or max(ids)>=84 or np.any(blocked[y,ids]):continue
            if not 156/255.<=float(np.mean(image[y,ids[:2]]))<=184/255.:continue
            edge=recover_pixel_edge(image,y,index,direction,blocked,max_row=69)
            if edge is not None:contours[side].append(((edge-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-y)/1.701))
    return contours


def infer_painted_road_band(image,asphalt,blocked,geometry_bands=None,observed_curb_bands=None,near_blocked=None,forward_band_ids=None,reference_seeds=None):
    """Piecewise fixed-width road hypothesis from a clean opposite contour.

    Coarse circles guide visible contour sampling only. Local tangents allow
    variable curvature. Visible grass, blocked pixels and unseen sectors veto
    support; the reference path and existing inset are unchanged.
    """
    grass_evidence=coherent_grass_mask(image)
    contours=[[],[]];rows=[];anchor=IMAGE_ORIGIN_X
    for y in range(54,4,-1):
        d=np.diff(np.pad(asphalt[y],(1,1)).astype(np.int16));s=np.flatnonzero(d==1);e=np.flatnonzero(d==-1)
        good=e-s>=8;s=s[good];e=e[good]
        if not len(s):
            if rows:break
            continue
        outside=np.maximum(s-anchor,0)+np.maximum(anchor-e,0)
        j=int(np.argmin(3*outside+.1*abs((s+e-1)*.5-anchor)))
        if outside[j]>8:break
        a,b=int(s[j]),int(e[j]-1);anchor=(a+b)*.5;rows.append((y,a,b))
        if y>=55:continue
        for side,index,direction in [(0,a,1),(1,b,-1)]:
            ids=index+direction*np.arange(-3,5)
            if min(ids)<0 or max(ids)>=84:continue
            # Curb-free exterior observations, not a second painted contour.
            if not 156/255.<=float(np.mean(image[y,ids[:2]]))<=184/255.:continue
            edge=recover_pixel_edge(image,y,index,direction,blocked)
            if edge is not None:contours[side].append(((edge-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-y)/1.701))
    near_counts=[0,0]
    if near_blocked is not None and any(len(points)<8 for points in contours):
        # The old blanket crop hid visible road outside the actual vehicle.
        # Supplement only a deficient contour, using the public silhouette
        # plus obstacle veto and the unchanged measured road/grass edge test.
        deficient=[len(points)<8 for points in contours]
        near_anchor=(rows[0][1]+rows[0][2])*.5 if rows else IMAGE_ORIGIN_X
        for y in range(55,69):
            d=np.diff(np.pad(asphalt[y],(1,1)).astype(np.int16));ss=np.flatnonzero(d==1);ee=np.flatnonzero(d==-1)
            good=ee-ss>=8;ss=ss[good];ee=ee[good]
            if not len(ss):continue
            outside=np.maximum(ss-near_anchor,0)+np.maximum(near_anchor-ee,0)
            j=int(np.argmin(3*outside+.1*abs((ss+ee-1)*.5-near_anchor)))
            if outside[j]>8:continue
            a,b=int(ss[j]),int(ee[j]-1);near_anchor=(a+b)*.5
            for side,index,direction in ((0,a,1),(1,b,-1)):
                if not deficient[side]:continue
                ids=index+direction*np.arange(-3,5)
                if min(ids)<0 or max(ids)>=84 or np.any(near_blocked[y,ids]):continue
                if not 156/255.<=float(np.mean(image[y,ids[:2]]))<=184/255.:continue
                edge=recover_pixel_edge(image,y,index,direction,near_blocked,max_row=69)
                if edge is not None:
                    contours[side].append(((edge-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-y)/1.701));near_counts[side]+=1
        contours=[sorted(points,key=lambda p:p[1]) if deficient[side] else points for side,points in enumerate(contours)]
    support=np.zeros((84,84),np.uint8);fits=[];updates={};reference_curves=[];near_reference_curves=0;nominal=2*(40./6.)
    for side,points in enumerate(contours):
        if len(points)<8:continue
        p=np.asarray(points,np.float64)
        best=None
        for first in range(len(p)-7):
            sample=p[first:];mean=sample.mean(axis=0);scale=float(np.sqrt(np.mean(np.sum((sample-mean)**2,axis=1))))
            if scale<1.:continue
            z=(sample-mean)/scale;matrix=np.column_stack((2*z,np.ones(len(z))))
            if np.linalg.cond(matrix)>100.:continue
            answer=np.linalg.lstsq(matrix,np.sum(z*z,axis=1),rcond=None)[0]
            rad2=answer[2]+float(answer[:2]@answer[:2])
            if rad2<=0:continue
            center=mean+scale*answer[:2];radius=scale*math.sqrt(rad2)
            if radius<=nominal or radius>1000.:continue
            # The centre must be on the inward side of this outer contour.
            if (side==1 and center[0]>=sample[:,0].mean()) or (side==0 and center[0]<=sample[:,0].mean()):continue
            residual=float(np.max(abs(np.linalg.norm(sample-center,axis=1)-radius)))
            angles=np.unwrap(np.arctan2(sample[:,1]-center[1],sample[:,0]-center[0]));span=float(max(angles)-min(angles))
            if residual>.35 or span<.4 or span>math.pi:continue
            score=span/max(residual,1/(2.7*6.))
            if best is None or score>best[0]:best=(score,center,radius,residual,float(min(angles)),float(max(angles)),sample.copy())
        if best is None:continue
        _,center,radius,residual,low,high,observed_points=best
        # Extend only when actual2D edge pixels confirm the next angular sector;
        # a fitted circle alone is never evidence for an unseen continuation.
        verified=0
        for direction in (-1,1):
            for step in range(1,math.ceil(math.pi/.05)+1):
                angle=(low if direction<0 else high)+direction*.05;radial=np.array([math.cos(angle),math.sin(angle)])
                point=center+radius*radial;observed=observe_outer_edge(image,point,radial,blocked)
                if observed is None:break
                candidate=np.vstack((observed_points,observed));mean=candidate.mean(axis=0)
                scale=float(np.sqrt(np.mean(np.sum((candidate-mean)**2,axis=1))));z=(candidate-mean)/scale
                matrix=np.column_stack((2*z,np.ones(len(z))))
                if np.linalg.cond(matrix)>100.:break
                answer=np.linalg.lstsq(matrix,np.sum(z*z,axis=1),rcond=None)[0];rad2=answer[2]+float(answer[:2]@answer[:2])
                if rad2<=0:break
                new_center=mean+scale*answer[:2];new_radius=scale*math.sqrt(rad2)
                new_residual=float(np.max(abs(np.linalg.norm(candidate-new_center,axis=1)-new_radius)))
                if new_radius<=nominal or new_residual>.35:break
                midpoint=(low+high)/2;angles=np.arctan2(candidate[:,1]-new_center[1],candidate[:,0]-new_center[0])
                angles=midpoint+(angles-midpoint+math.pi)%(2*math.pi)-math.pi
                if max(angles)-min(angles)>math.pi:break
                center,radius,residual=new_center,new_radius,new_residual
                low,high=float(min(angles)),float(max(angles));observed_points=candidate
                verified+=1
        # The tracer adds actual visible contour samples. Safety geometry
        # and reference must consume the same observed support; all original
        # two-sided fit guards, uncertainty and material vetoes still apply.
        reference_observations,reference_extensions=extend_reference_contour(image,observed_points,center,blocked)
        # Near-car observations may seed the proposal, but safety offsets
        # still use only the existing forward, unoccluded sampling region.
        # The unchanged local quadratic requires7 actual samples and support
        # on both sides; no near-car width extrapolation is promoted.
        geometry_observations=reference_observations
        if near_counts[side]:
            geometry_observations=np.asarray([p for p in reference_observations
                if IMAGE_ORIGIN_Y-1.701*p[1]<=54.])
        inner_points,local_residuals,_=offset_observed_contour(geometry_observations,center,radius) if len(geometry_observations)>=7 else ([],[],[])
        baseline_inner_points=inner_points
        mixed_updates=0;mixed_records=[];corrected=[];mixed_angles=set()
        for x,y,angle,ox,oy in inner_points:
            outward=np.asarray([ox-x,oy-y]);length=float(np.linalg.norm(outward))
            if length<1.:corrected.append((x,y,angle,ox,oy));continue
            outward/=length;old_allowance=(nominal-length)*.5
            physical=np.asarray([x,y])-old_allowance*outward
            observed=observe_mixed_curb_edge(image,physical,-outward,blocked,grass_evidence)
            if observed is None:observed=observe_white_curb_inner(image,physical,-outward,blocked,grass_evidence)
            if observed is None:corrected.append((x,y,angle,ox,oy));continue
            measured,fit=observed
            allowance=(21./6.)*(1-math.cos(.31/2))+1/(2.7*6.)
            safe=measured+allowance*outward
            if float(np.linalg.norm(safe-physical))>(8./6.)+math.hypot(1/1.3608,1/1.701):
                corrected.append((x,y,angle,ox,oy));continue
            corrected.append((float(safe[0]),float(safe[1]),angle,ox,oy));mixed_updates+=1;mixed_records.append(fit);mixed_angles.add(angle)
        curb_inner_points=corrected;inner_points=baseline_inner_points
        # A changing vertical row crop can lose an otherwise visible outer
        # contour. Prior observations supply correspondence search locations
        # only. Every added point must be observed again in CURRENT pixels;
        # these matches never enter road support or safety geometry above.
        matched=0;novel=0;near_novel=0;observed=list(reference_observations)
        # Supplement the reference even when enough forward samples exist.
        # The original geometry sampling above is deliberately unchanged.
        if near_blocked is not None:
            for point in near_vehicle_reference_edges(image,asphalt,near_blocked)[side]:
                if min(np.linalg.norm(np.asarray(observed)-point,axis=1))<.5*(21./6.)/4:continue
                observed.append(point);near_novel+=1
        if reference_seeds is not None:
            for seed in reference_seeds:
                if seed['outer_side']!=side:continue
                for point,normal in zip(seed['edge_points'],seed['edge_normals']):
                    current=observe_outer_edge(image,point,normal,blocked,reference=True)
                    if current is None:continue
                    matched+=1
                    if min(np.linalg.norm(np.asarray(observed)-current,axis=1))<.5*(21./6.)/4:continue
                    observed.append(current);novel+=1
        if novel or near_novel:
            observed=np.asarray(observed)
            theta=np.arctan2(observed[:,1]-center[1],observed[:,0]-center[0])
            anchor=math.atan2(float(np.mean(np.sin(theta))),float(np.mean(np.cos(theta))))
            theta=anchor+(theta-anchor+math.pi)%(2*math.pi)-math.pi
            if max(theta)-min(theta)<=math.pi:reference_observations=observed[np.argsort(theta)]
        _,_,centres=offset_observed_contour(reference_observations,center,radius)
        edge_points,edge_normals=observed_reference_edge_normals(reference_observations,center)
        if len(centres)>=3:
            reference_curves.append(dict(outer_side=side,points=centres,edge_points=edge_points,edge_normals=edge_normals,
                current_edge_matches=matched,current_edge_new_observations=novel,current_near_edge_observations=near_novel))
            if near_counts[side]:near_reference_curves+=1
        if len(inner_points)<2:continue
        white=cv2.dilate((image>.75).astype(np.uint8),np.ones((3,9),np.uint8))>0
        red=cv2.dilate((image<.35).astype(np.uint8),np.ones((3,9),np.uint8))>0
        grass=grass_evidence
        reach=math.ceil(((8./6.)+math.hypot(1/1.3608,1/1.701))*1.3608)
        added_before=int(support.sum());edge_count=0
        for row,a,b in rows:
            world_y=(IMAGE_ORIGIN_Y-row)/1.701;candidates=[]
            for first,last in zip(inner_points,inner_points[1:]):
                if last[2]-first[2]>.051:continue
                if first[1]==last[1] or (first[1]-world_y)*(last[1]-world_y)>0:continue
                weight=(world_y-first[1])/(last[1]-first[1])
                world_x=first[0]+weight*(last[0]-first[0]);pixel_x=IMAGE_ORIGIN_X+1.3608*world_x
                eligible=(a-reach<=pixel_x<a) if side==1 else (b<pixel_x<=b+reach)
                if eligible and 1.<=pixel_x<=82.:
                    candidates.append(float(pixel_x))
            if not candidates:continue
            pixel_x=max(candidates) if side==1 else min(candidates)
            lo=max(0,int(math.floor(pixel_x if side==1 else b)))
            hi=min(83,int(math.ceil(a if side==1 else pixel_x)))
            if np.any(blocked[row,lo:hi+1]) or np.any(grass[row,lo:hi+1]):continue
            index=max(0,min(83,int(round(pixel_x))))
            # Each public curb tile is red OR white; a junction is optional.
            if not (white[row,index] or red[row,index]):continue
            updates[(side,row)]=pixel_x;edge_count+=1
            if side==1:support[row,int(math.ceil(pixel_x)):a]=1
            else:support[row,b+1:int(math.floor(pixel_x))+1]=1
        if observed_curb_bands is not None:
            for first,last in zip(curb_inner_points,curb_inner_points[1:]):
                if last[2]-first[2]>.051 or first[2] not in mixed_angles or last[2] not in mixed_angles:continue
                patch=np.asarray([[first[0],first[1]],[first[3],first[4]],
                                  [last[3],last[4]],[last[0],last[1]]])
                for inner,outer in ((0,1),(3,2)):
                    normal=patch[outer]-patch[inner];normal/=np.linalg.norm(normal)
                    inset=.35*abs(float(normal[0]));patch[inner]+=inset*normal;patch[outer]-=inset*normal
                observed_curb_bands.append(patch)
        # Paint can occlude a whole inner cap between two row intervals.
        # Restrict recovery to the conservative observed2D road band rather
        # than a selected row's left/right prefix. No unseen curve is added.
        for first,last in zip(inner_points,inner_points[1:]):
            if last[2]-first[2]>.051:continue
            polygon=np.asarray([[first[0],first[1]],[first[3],first[4]],
                                [last[3],last[4]],[last[0],last[1]]])
            if geometry_bands is not None:
                geometry_bands.append(polygon)
                if near_counts[side] and forward_band_ids is not None:forward_band_ids.add(id(polygon))
            px=IMAGE_ORIGIN_X+1.3608*polygon[:,0];py=IMAGE_ORIGIN_Y-1.701*polygon[:,1]
            x0=max(1,int(math.ceil(min(px))));x1=min(82,int(math.floor(max(px))))
            y0=max(5,int(math.ceil(min(py))));y1=min(54,int(math.floor(max(py))))
            if x0>x1 or y0>y1:continue
            yy,xx=np.indices((y1-y0+1,x1-x0+1));xx=xx+x0;yy=yy+y0
            wx=(xx-IMAGE_ORIGIN_X)/1.3608;wy=(IMAGE_ORIGIN_Y-yy)/1.701
            cross=[]
            for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
                cross.append((b[0]-a[0])*(wy-a[1])-(b[1]-a[1])*(wx-a[0]))
            cross=np.asarray(cross);inside=np.all(cross>=0,axis=0)|np.all(cross<=0,axis=0)
            eligible=inside&(white[yy,xx]|red[yy,xx]|asphalt[yy,xx].astype(bool))&~grass[yy,xx]&~blocked[yy,xx]
            support[yy[eligible],xx[eligible]]=1
        fits.append(dict(outer_side=side,observations=len(points),forward_safety_observations=len(geometry_observations),radial_residual_m=residual,
            mixed_curb_updates=mixed_updates,mixed_curb_fit_records=mixed_records,
            angular_support_rad=high-low,added_pixels=int(support.sum())-added_before,
            verified_2D_extensions=verified,local_offset_points=len(inner_points),
            local_offset_edges=edge_count,reference_observed_edge_extensions=reference_extensions,local_max_residual_m=max(local_residuals),
            offset_method='local quadratic tangent + public width; circle used only for observed sampling'))
    if reference_seeds is not None:
        represented={curve['outer_side'] for curve in reference_curves}
        for seed in reference_seeds:
            if seed['outer_side'] not in represented:
                reference_curves.extend(reobserve_reference_chain(image,seed,blocked))
    return support,dict(near_vehicle_contour_samples=near_counts,near_vehicle_reference_curves=near_reference_curves,painted_band_added_pixels=int(np.sum(support&~asphalt.astype(bool))),painted_band_fits=fits,
        painted_band_bound_universally_validated=False),updates,reference_curves


def observed_reference_run_direction(points,previous):
    """Direction correspondence to own-motion transported observation memory.

    Return None when there are too few correspondences, zero for contradictory
    ones, or the current run's signed direction along the previous observation.
    Memory never contributes coordinates to the returned reference.
    """
    if previous is None or len(previous)<3:return None
    previous=np.asarray(previous,np.float64);points=np.asarray(points,np.float64)
    delta=np.diff(previous,axis=0);squared=np.sum(delta*delta,axis=1)
    valid=np.flatnonzero(squared>1e-12)
    arc=np.r_[0.,np.cumsum(np.sqrt(squared))];matches=[]
    for i,point in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        length=float(np.linalg.norm(tangent))
        if length<1e-6:continue
        tangent/=length
        fraction=np.clip(np.sum((point-previous[:-1])*delta,axis=1)/np.maximum(squared,1e-12),0.,1.)
        projected=previous[:-1]+fraction[:,None]*delta
        candidates=[j for j in valid
            if abs(float(delta[j]@tangent))/math.sqrt(float(squared[j]))>=math.cos(.31)
            and float(np.linalg.norm(projected[j]-point))<=math.hypot(1/1.3608,1/1.701)]
        if not candidates:continue
        if any(float(delta[j]@tangent)*float(delta[k]@tangent)<0.
               for j in candidates for k in candidates):return 0
        j=min(candidates,key=lambda k:float(np.linalg.norm(projected[k]-point)))
        if (j==valid[0] and fraction[j]==0.) or (j==valid[-1] and fraction[j]==1.):continue
        station=float(arc[j]+fraction[j]*math.sqrt(float(squared[j])))
        direction=1 if float(delta[j]@tangent)>0. else -1
        matches.append((station,direction,j,float(fraction[j]),point))
    if len(matches)<3:return None
    direction=matches[0][1]
    if any(match[1]!=direction for match in matches):return 0
    def internal_vertex(match):
        _,_,j,fraction,_=match
        vertex=j if fraction==0. else j+1 if fraction==1. else -1
        return vertex if 0<vertex<len(previous)-1 else -1
    for first,second in zip(matches,matches[1:]):
        advance=direction*(second[0]-first[0])
        if advance>0.:continue
        if advance<0.:return 0
        # Dense current samples can both clamp to one coarse internal vertex.
        # That equality is not a reversal when the actual current displacement
        # advances along both matched directed segments. No localization slack
        # or old coordinates are inserted into the current reference.
        vertex=internal_vertex(first)
        displacement=second[4]-first[4]
        if (vertex<0 or vertex!=internal_vertex(second) or
            any(direction*float(displacement@delta[match[2]])<=0.
                for match in (first,second))):return 0
    if direction*(matches[-1][0]-matches[0][0])<=0.:return 0
    return direction


def reference_from_observed_width(raw_points,curves,asphalt,blocked,previous=None,road_occlusion_patches=()):
    """Visible outer contour plus public half-width, with an observed join.

    This estimates a reference, not a new planner or a geometry certificate.
    A short gap between samples of the same contour may be joined only on
    visible pavement. This changes the reference proposal, never road support.
    Do not continue a row-midpoint path beyond the observed centreline.
    """
    raw=np.asarray(raw_points,np.float64);best=None;backward_joins=0;ambiguous_runs=0
    # These are the existing CURRENT closed-ring road patches, not collision
    # clearance. Lane geometry may pass under an object before the unchanged
    # obstacle deformation and hard collision checks are applied.
    occlusion_patches=[tuple(tuple(float(v) for v in point) for point in patch)
        for patch in road_occlusion_patches]
    def supported(point):
        x=IMAGE_ORIGIN_X+1.3608*point[0];y=IMAGE_ORIGIN_Y-1.701*point[1]
        # _map includes row69. Values just below69 already round to that
        # pixel, so rejecting its exact centre breaks a valid near-edge join.
        if not 1<=x<=82 or not 5<=y<=69:return False
        ix=int(round(x));iy=int(round(y))
        return (bool(asphalt[iy,ix]) and not bool(blocked[iy,ix])) or any(
            core.inside(tuple(point[:2]),patch) for patch in occlusion_patches)
    def visible_join(first,last):
        first=np.asarray(first[:2]);last=np.asarray(last[:2])
        gap=float(np.linalg.norm(last-first))
        if gap>21./6.:return False
        n=max(2,int(math.ceil(gap*1.701))+1)
        return all(supported((1-t)*first+t*last) for t in np.linspace(0.,1.,n))
    for curve in curves:
        runs=[];run=[]
        for point in curve['points']:
            if not supported(point) or (run and point[2]-run[-1][2]>.051 and not visible_join(run[-1],point)):
                if len(run)>=3:runs.append(run)
                run=[]
            if supported(point):run.append(point)
        if len(run)>=3:runs.append(run)
        for run in runs:
            points=np.asarray(run,np.float64)[:,:2]
            direction=observed_reference_run_direction(points,previous)
            if direction==0:ambiguous_runs+=1;continue
            if direction==-1 or (direction is None and np.linalg.norm(points[-1])<np.linalg.norm(points[0])):
                points=points[::-1]
            outgoing=points[1]-points[0];joins=[]
            for j in range(len(raw)):
                join=points[0]-raw[j];gap=float(np.linalg.norm(join))
                if gap>21./6.:continue
                if not all(supported(point) for point in raw[:j+1]):continue
                incoming=raw[j]-raw[j-1] if j else raw[1]-raw[0]
                # Nearest position is not enough: a prefix that has already
                # passed this contour start would introduce a backward chord.
                if float(incoming@outgoing)<0. or (gap>1e-6 and
                    (float(incoming@join)<0. or float(join@outgoing)<0.)):
                    backward_joins+=1;continue
                if visible_join(raw[j],points[0]):joins.append((gap,j))
            if not joins:continue
            gap,j=min(joins)
            candidate=np.vstack((raw[:j+1],points));ds=np.linalg.norm(np.diff(candidate,axis=0),axis=1)
            candidate=candidate[np.r_[True,ds>1e-6]]
            length=float(np.sum(np.linalg.norm(np.diff(candidate,axis=0),axis=1)))
            score=length-gap
            if best is None or score>best[0]:best=(score,candidate,len(points),gap)
    if best is None:return raw,dict(reference_source='visible row midpoints',observed_width_reference_used=False,
        reference_backward_joins_rejected=backward_joins,reference_ambiguous_direction_runs=ambiguous_runs,
        reference_current_road_occlusion_patches=len(occlusion_patches))
    _,points,count,gap=best
    return points,dict(reference_source='observed clean outer contour + public half-width',
        observed_width_reference_used=True,observed_centerline_points=count,
        observed_reference_join_m=gap,reference_unseen_suffix_extrapolated=False,
        reference_backward_joins_rejected=backward_joins,reference_ambiguous_direction_runs=ambiguous_runs,
        reference_is_an_estimate_not_a_certificate=True,
        reference_current_road_occlusion_patches=len(occlusion_patches))


def road_union_boundary(roads):
    """Exterior of convex observed patches; no closing edges across gaps.

    Clip every patch edge by the other patches. Shared interfaces cancel;
    coincident exterior edges retain one copy. Unobserved holes remain holes.
    This changes only the representation, never the core margin semantics.
    """
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    patches=[]
    for polygon,_ in roads:
        polygon=[tuple(p) for p in polygon]
        area=sum(cross(a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1]))
        if area<0:polygon.reverse()
        patches.append(polygon)
    boxes=[(min(p[0] for p in poly),max(p[0] for p in poly),
            min(p[1] for p in poly),max(p[1] for p in poly)) for poly in patches]
    boundary=[];tol=1e-10
    for i,polygon in enumerate(patches):
        for first,last in zip(polygon,polygon[1:]+polygon[:1]):
            delta=(last[0]-first[0],last[1]-first[1])
            if delta==(0.,0.):continue
            pieces=[(0.,1.)]
            x0,x1=sorted((first[0],last[0]));y0,y1=sorted((first[1],last[1]))
            for j,other in enumerate(patches):
                if i==j:continue
                bx0,bx1,by0,by1=boxes[j]
                if x1<bx0-tol or x0>bx1+tol or y1<by0-tol or y0>by1+tol:continue
                lo,hi=0.,1.;valid=True
                for a,b in zip(other,other[1:]+other[:1]):
                    edge=(b[0]-a[0],b[1]-a[1])
                    value=cross(edge,(first[0]-a[0],first[1]-a[1]));slope=cross(edge,delta)
                    if abs(slope)<tol:
                        if value< -tol:valid=False;break
                    elif slope>0:lo=max(lo,-value/slope)
                    else:hi=min(hi,-value/slope)
                    if hi<=lo+tol:valid=False;break
                if not valid:continue
                mid=(lo+hi)*.5;point=(first[0]+mid*delta[0],first[1]+mid*delta[1])
                interior=all(cross((b[0]-a[0],b[1]-a[1]),(point[0]-a[0],point[1]-a[1]))>tol
                    for a,b in zip(other,other[1:]+other[:1]))
                outward=any(cross(delta,(p[0]-first[0],p[1]-first[1]))< -tol for p in other)
                if not (interior or outward or j<i):continue
                kept=[]
                for a,b in pieces:
                    if hi<=a or lo>=b:kept.append((a,b));continue
                    if a<lo:kept.append((a,lo))
                    if hi<b:kept.append((hi,b))
                pieces=kept
                if not pieces:break
            for a,b in pieces:
                if b-a>tol:
                    start=first if a==0. else (first[0]+a*delta[0],first[1]+a*delta[1])
                    end=last if b==1. else (first[0]+b*delta[0],first[1]+b*delta[1])
                    boundary.append((start,end))
    return boundary


def strip_union_mesh(rows,grip):
    """Union of observed row strips, with only exposed interval boundaries.

    Preserve disjoint branches and holes. Horizontal shared interfaces are
    cancelled by interval difference, never passed as physical road borders.
    FOV caps stay at the existing first/last observed row centres.
    """
    def difference(intervals,other):
        result=[]
        for left,right in intervals:
            pieces=[(left,right)]
            for a,b in other:
                next_pieces=[]
                for x,y in pieces:
                    if b<=x or a>=y:next_pieces.append((x,y));continue
                    if x<a:next_pieces.append((x,min(y,a)))
                    if b<y:next_pieces.append((max(x,b),y))
                pieces=next_pieces
            result.extend(pieces)
        return result
    normalized=[]
    for y,intervals in rows:
        merged=[]
        for a,b in sorted((a,b) for a,b in intervals if b>a):
            if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(merged[-1][1],b))
            else:merged.append((a,b))
        normalized.append((y,merged))
    # Follow one-to-one observed flanks continuously. At a split/merge,
    # intersect actual intervals instead of drawing a cross-branch chord.
    roads=[];boundary=[];slabs=[]
    for (y,intervals),(z,following) in zip(normalized,normalized[1:]):
        bottom=[];top=[]
        for a,b in intervals:
            matches=[(c,d) for c,d in following if max(a,c)<min(b,d)]
            for c,d in matches:
                unique=len(matches)==1 and sum(max(c,x)<min(d,w) for x,w in intervals)==1
                if unique:lo,hi,up_lo,up_hi=a,b,c,d
                else:lo=up_lo=max(a,c);hi=up_hi=min(b,d)
                roads.append((((lo,y),(hi,y),(up_hi,z),(up_lo,z)),grip))
                boundary.extend([((lo,y),(up_lo,z)),((hi,y),(up_hi,z))])
                bottom.append((lo,hi));top.append((up_lo,up_hi))
        slabs.append((y,z,bottom,top))
    for i,(y,z,bottom,top) in enumerate(slabs):
        previous=slabs[i-1][3] if i else []
        following=slabs[i+1][2] if i+1<len(slabs) else []
        for a,b in difference(bottom,previous):boundary.append(((a,y),(b,y)))
        for a,b in difference(top,following):boundary.append(((a,z),(b,z)))
    return roads,boundary


def transport_road_evidence(frames):
    """Carry only actual visible road; no registration means no old evidence."""
    unique=[]
    for frame in frames:
        if not unique or not np.array_equal(frame,unique[-1]):unique.append(frame)
    frames=unique
    road=visible_road_evidence(frames[0]);age=np.zeros((84,84),np.uint8)
    accepted=0;rejected=0
    for previous,current in zip(frames,frames[1:]):
        if np.array_equal(previous,current):continue
        transform=register_road_frames(previous,current)
        if transform is None:
            road=np.zeros((84,84),np.uint8);age[:]=0;rejected+=1
        else:
            road=cv2.warpAffine(road,transform,(84,84),flags=cv2.INTER_NEAREST,borderValue=0)
            age=cv2.warpAffine(age,transform,(84,84),flags=cv2.INTER_NEAREST,borderValue=0)+1
            road=cv2.erode(road,np.ones((3,3),np.uint8),iterations=1)
            road[age>7]=0;accepted+=1
        seen=visible_road_evidence(current);age[seen>0]=0;road|=seen
    vehicle=vehicle_occluded_pixels(frames[-1])
    return road&vehicle,dict(registered_pairs=accepted,rejected_pairs=rejected,
        transported_vehicle_pixels=int(np.sum(road&vehicle)),unique_frames=len(frames),
        registration_bounds_universally_validated=False)

class _TickCounter(list):
    def __init__(self):super().__init__([0]);self.limit=core.MAX_MODEL_TICKS
    def __setitem__(self,index,value):
        if value>self.limit:raise RuntimeError('ADAPTER_MODEL_TICK_BUDGET')
        super().__setitem__(index,value)


def _mass_properties(poly,density):
    p=np.asarray(poly,np.float64);q=np.roll(p,-1,axis=0)
    cross=p[:,0]*q[:,1]-q[:,0]*p[:,1]
    area=float(np.sum(cross)/2.)
    center=np.sum((p+q)*cross[:,None],axis=0)/(6*area)
    inertia=abs(float(np.sum(cross*(np.sum(p*p,axis=1)+np.sum(p*q,axis=1)+np.sum(q*q,axis=1)))/12.))*density
    return abs(area)*density,center,inertia


class Agent:
    def __init__(self):
        # Generic analytic public vehicle dimensions/densities, not a snapshot.
        hull=[_mass_properties(np.asarray(p)*core.SIZE,1.) for p in (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4)]
        self.hull_mass=sum(m for m,c,i in hull)
        self.hull_com=sum(m*c for m,c,i in hull)/self.hull_mass
        wheel_poly=[(-.28,-.54),(.28,-.54),(.28,.54),(-.28,.54)]
        wm,wc,wi=_mass_properties(wheel_poly,.1)
        self.wheel_inertia=wi
        wheel_positions=np.asarray(core.WHEELPOS)*core.SIZE
        self.mass=self.hull_mass+4*wm
        self.com=(self.hull_mass*self.hull_com+wm*np.sum(wheel_positions,axis=0))/self.mass
        self.levers=wheel_positions-self.com
        self.inertia=sum(i for m,c,i in hull)+sum(wi+wm*float(p@p) for p in wheel_positions)-self.mass*float(self.com@self.com)
        self.counter=_TickCounter()
        self.calls=0
        self.diagnostics={}
        self.reset(None)

    def reset(self,observation):
        # Submission execution counts belong to this episode. Research quotas
        # are accumulated independently by the external evaluation worker.
        self.counter[0]=0
        self.speed=0.;self.yaw=0.;self.joint=0.;self.previous_joint=0.
        self.distance=0.;self.previous_action=np.zeros(3,np.float32)
        self.predicted_wheels=None;self.predicted_hull_speed=None;self.calls=0
        self.predicted_hull_velocity_body=None
        self.predicted_joints=None;self.predicted_joint_rates=None;self.predicted_yaw=None;self.predicted_average_hull_velocity_body=None;self.predicted_average_yaw=None;self.joint_rate=0.
        self.road_frames=[];self.reference_seeds=[];self.reference_lattice=[];self.obstacle_tracks=[]
        self.history=[0,0];self.last_root=None;self.last_path=None
        self.grip_prior=1.;self.engine_prior=1.;self.steering_prior=1.
        self.uncertainty={};self.diagnostics={}

    def _state_estimates(self,obs):
        image=obs[-1]
        speed,yaw,speed_interval,yaw_interval=decode_motion_hud(image,self.predicted_hull_speed,self.predicted_yaw)
        # Include the full raster support of the public green indicator.
        prior=None if self.predicted_joints is None else self.predicted_joints[0]
        joint,joint_interval=decode_joint_hud(image,prior)
        self.previous_joint=self.joint;self.joint=joint
        self.joint_rate=(float(np.clip((joint-self.previous_joint)/.08,-3.,3.)) if self.predicted_joint_rates is None
                         else float(self.predicted_joint_rates[0]))
        self.joint_observed_interval=joint_interval
        # Missing optical flow is not evidence of zero side slip in a turn.
        lateral_speed=(0. if self.predicted_hull_velocity_body is None else
                       float(np.clip(self.predicted_hull_velocity_body[0],-10.,10.)))
        flow_confidence=0.
        a=np.rint(obs[-2]*255).astype(np.uint8);b=np.rint(image*255).astype(np.uint8)
        mask=np.zeros((84,84),np.uint8);mask[8:69,2:82]=255;mask[54:69,35:49]=0
        points=cv2.goodFeaturesToTrack(a,64,.02,4,mask=mask)
        if points is not None and len(points)>=8:
            next_points,status,errors=cv2.calcOpticalFlowPyrLK(a,b,points,None,winSize=(15,15),maxLevel=2)
            if next_points is not None:
                valid=status.ravel().astype(bool)&(errors.ravel()<20.)
                if np.sum(valid)>=8:
                    p=points[valid,0,:].astype(np.float64);q=next_points[valid,0,:].astype(np.float64)
                    for z in (p,q):z[:,0]=(z[:,0]-IMAGE_ORIGIN_X)/1.3608;z[:,1]=(IMAGE_ORIGIN_Y-z[:,1])/1.701
                    affine,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=.4,maxIters=100,confidence=.95)
                    if affine is not None and inliers is not None:
                        scale=math.hypot(affine[0,0],affine[1,0]);flow_confidence=float(np.mean(inliers))
                        if .97<scale<1.03 and flow_confidence>.6:
                            visual_speed=math.hypot(float(affine[0,2]),float(affine[1,2]))/.08
                            visual_yaw=math.atan2(affine[0,1],affine[0,0])/.08
                            observed_average=np.array([-affine[0,2]/.08,-affine[1,2]/.08])
                            if self.predicted_average_hull_velocity_body is not None:
                                # Flow is an interval average in the ending camera
                                # frame; transport its innovation to the endpoint.
                                aligned=np.asarray(self.predicted_hull_velocity_body)+observed_average-np.asarray(self.predicted_average_hull_velocity_body)
                                lateral_speed=float(np.clip(aligned[0],-10.,10.))
                                visual_speed=float(np.linalg.norm(aligned))
                                visual_yaw+=self.predicted_yaw-self.predicted_average_yaw
                            else:lateral_speed=float(np.clip(observed_average[0],-10.,10.))
                            if abs(visual_speed-speed)<8.:
                                speed=.7*speed+.3*max(0.,visual_speed)
                                if speed_interval is not None:speed=float(np.clip(speed,*speed_interval))
                            if abs(visual_yaw-yaw)<1.:
                                yaw=.7*yaw+.3*visual_yaw
                                if yaw_interval is not None:yaw=float(np.clip(yaw,*yaw_interval))
        if self.predicted_hull_speed is not None and self.predicted_hull_speed-speed>8.:
            # A possible impact or loss of traction, not observed damage truth.
            self.grip_prior=.6;self.engine_prior=.8;self.steering_prior=.8
        self.speed=float(np.clip(speed,0.,100.));self.yaw=float(np.clip(yaw,-5.,5.))
        self.distance+=self.speed*.08 if self.last_root is not None else 0.
        self.uncertainty=dict(speed_interval_m_s=[max(0.,self.speed-3.),self.speed+3.],
            public_speed_HUD_bin_m_s=speed_interval,public_yaw_HUD_bin_rad_s=yaw_interval,
            HUD_prior_time='own action propagated exactly4 raw ticks to latest0.08s observation',
            flow_time_alignment='interval-average innovation transported to endpoint by own dynamics',
            intervals_are_unvalidated_engineering_priors=True,
            joint_HUD_interval_rad=None if joint_interval is None else list(joint_interval),joint_rate_source='own-action end prediction; finite difference only at bootstrap',
            visual_motion_confidence=flow_confidence,lateral_speed_assumption='visual estimate or own-action prediction; initial zero prior',
            wheel_contact_frictions_and_clip_history='model-estimated, NOT observed',
            damage='not observed; multiplier priors may reduce after motion residual',
            wheel_omega=('rolling-speed initial prior' if self.predicted_wheels is None else
                         'own-action model propagation; wheel slip error unresolved'))
        return lateral_speed

    def _map(self,image,transported=None):
        asphalt=((image>.36)&(image<.47)).astype(np.uint8)
        obstacles,obstacle_blocked=detect_observed_obstacles(image)
        visible_obstacles=obstacles.copy()
        object_road_patches=[];object_collision_envelopes=[];object_road_records=[]
        for center,radius in visible_obstacles:
            recovered=observed_object_road_patch(image,center,self.joint)
            if recovered is not None:
                patch,collision,record=recovered
                object_road_patches.append(patch)
                # Union of full-cell covers retains every compatible center
                # without adding the empty space of one global bounding ball.
                object_collision_envelopes.extend(record['collision_cell_disks'])
                object_road_records.append(record)
        blocked=obstacle_blocked.copy()
        blocked[55:70,34:51]=True
        self.obstacle_tracks,obstacle_counts=update_observed_obstacles(image,obstacles,self.obstacle_tracks,self.joint)
        obstacles=[(tuple(track['center']),track['radius']) for track in self.obstacle_tracks]
        self.uncertainty['obstacle_correspondence']=obstacle_counts
        self.uncertainty['hidden_obstacles_are_own_action_estimates']=True
        # Known object footprints veto inference even during a partial crop;
        # memory never fills any unseen or opaque road support.
        yy,xx=np.indices(image.shape)
        for center,radius in obstacles:
            px=IMAGE_ORIGIN_X+1.3608*center[0];py=IMAGE_ORIGIN_Y-1.701*center[1]
            footprint=((xx-px)/1.3608)**2+((yy-py)/1.701)**2<=radius**2
            blocked[footprint]=True;obstacle_blocked[footprint]=True
        # Never fill opaque pixels. The wider blocked window is only a veto on
        # subpixel recovery, not a reason to erase directly visible asphalt.
        if transported is not None:
            # Provenance is observed earlier pixels, never an inferred hole fill.
            transported=transported.copy();transported[obstacle_blocked]=0
            asphalt|=transported.astype(np.uint8)
        inferred,support_info=infer_local_road_support(image,asphalt,obstacle_blocked,self.joint,
            self.calls==0 and self.last_root is None,self.speed)
        asphalt|=inferred
        self.uncertainty.update(support_info)
        # Keep the pixel/reference-material inputs separate from geometry.
        # Only CURRENT visible samples validate this conditioned corridor. The
        # old inference and all material/width/turn/distance gates stay intact.
        joint_geometry=np.zeros_like(asphalt)
        joint_cover,joint_cover_info=source_bbox_vehicle_cover(self.joint_observed_interval)
        joint_info={}
        if joint_cover is not None and not (self.calls==0 and self.last_root is None):
            direct=((image>.36)&(image<.47)).astype(np.uint8)
            refined,joint_info=infer_local_road_support(image,direct,obstacle_blocked,self.joint,
                False,self.speed,cover_override=joint_cover,connected_anchors=True)
            joint_geometry=refined&~inferred
        self.uncertainty['raster_kernel_geometry_pixels']=int(joint_geometry.sum())
        self.uncertainty['raster_kernel_geometry_cover_cells']=joint_cover_info.get('cover_cells',0)
        self.uncertainty['raster_kernel_geometry_component_rows']=joint_info.get('road_support_flank_component_rows',0)
        self.uncertainty['raster_kernel_geometry_reference_separate']=True
        self.uncertainty['raster_kernel_geometry_kinematic_anchor_assumption']=True
        def observed_run(y,anchor,data=None):
            data=asphalt if data is None else data
            edges=np.diff(np.pad(data[y,1:83],(1,1)).astype(np.int16));starts=np.flatnonzero(edges==1)+1;ends=np.flatnonzero(edges==-1)+1
            good=ends-starts>=3;starts=starts[good];ends=ends[good]
            if not len(starts):return None
            center=(starts+ends-1)*.5
            outside=np.maximum(starts-anchor,0)+np.maximum(anchor-ends,0)
            j=int(np.argmin(3*outside+.1*np.abs(center-anchor)))
            if outside[j]>8:return None
            return int(starts[j]),int(ends[j])
        rows=[];pixels=[];anchor=IMAGE_ORIGIN_X
        self.uncertainty['reference_current_two_flank_rows']=0
        self.uncertainty['reference_current_two_flank_is_estimate']=True
        for y in range(69,4,-2):
            run=observed_run(y,anchor)
            if run is None:
                if len(rows)<3:continue
                break
            start,end=run
            left=(float(start)-IMAGE_ORIGIN_X)/1.3608+.35
            right=(float(end-1)-IMAGE_ORIGIN_X)/1.3608-.35
            if right-left<2.5:break
            anchor=(start+end-1)*.5
            # The selected raw run can be one visible fragment beside the car.
            # A CURRENT two-flank validation supplies a reference midpoint
            # estimate, without filling raw pixels or changing geometry runs.
            current_flanks=[v for v in joint_info.get('current_two_flank_rows',[]) if v[0]==y]
            if np.any(joint_geometry[y]) and len(current_flanks)==1:
                _,flank_left,flank_right,_,_=current_flanks[0]
                left=(float(flank_left)-IMAGE_ORIGIN_X)/1.3608+.35
                right=(float(flank_right)-IMAGE_ORIGIN_X)/1.3608-.35
                self.uncertainty['reference_current_two_flank_rows']=self.uncertainty.get('reference_current_two_flank_rows',0)+1
            rows.append((left,right,(IMAGE_ORIGIN_Y-y)/1.701));pixels.append((y,start,end))
        if len(rows)<8:raise RuntimeError('OBSERVED_ROAD_SUPPORT_INSUFFICIENT')
        geometry_bands=[];observed_curb_bands=[];forward_band_ids=set()
        painted,painted_info,band_edges,reference_curves=infer_painted_road_band(image,asphalt,blocked,geometry_bands,observed_curb_bands,
            obstacle_blocked|vehicle_projection_mask(self.joint).astype(bool),forward_band_ids,self.reference_seeds)
        self.reference_seeds=[dict(outer_side=curve['outer_side'],edge_points=curve['edge_points'],edge_normals=curve['edge_normals']) for curve in reference_curves]
        self.uncertainty['reference_current_edge_matches']=sum(curve['current_edge_matches'] for curve in reference_curves)
        self.uncertainty['reference_current_edge_new_observations']=sum(curve['current_edge_new_observations'] for curve in reference_curves)
        self.uncertainty['reference_current_near_edge_observations']=sum(curve['current_near_edge_observations'] for curve in reference_curves)
        geometry_veto=coherent_grass_mask(image)|blocked.astype(bool)
        # A lone asphalt-grey sample may be a red/white curb mixture. Flat
        # public road shades, registered evidence, conditioned vehicle gaps,
        # and the conservative fixed-width band supply geometric support.
        high=cv2.dilate(image,np.ones((3,3),np.uint8));low=cv2.erode(image,np.ones((3,3),np.uint8))
        flat=high-low<=(5.1+2)/255.
        geometry_asphalt=(asphalt.astype(bool)&flat)|painted.astype(bool)|inferred.astype(bool)
        adjacent=object_adjacent_asphalt(image,asphalt,flat,visible_obstacles)
        geometry_asphalt|=adjacent
        self.uncertainty['raster_object_adjacent_asphalt_pixels']=int(np.sum(adjacent))
        if transported is not None:geometry_asphalt|=transported.astype(bool)
        geometry_asphalt|=joint_geometry.astype(bool)
        geometry_asphalt=geometry_asphalt.astype(np.uint8)
        self.uncertainty.update(painted_info)
        # Geometry has its own topology. Do not join one selected run across
        # a split/merge; retain every supported interval and every empty row.
        geometry_rows=[];refined=unresolved=curb_refined=band_refined=raw_anchor_refined=0
        # Existing paint evidence/halo: a red curb blurred into road shades
        # must not be interpreted as a newly exposed plain road boundary.
        paint_near=cv2.dilate(((image<.35)|(image>.75)).astype(np.uint8),np.ones((3,9),np.uint8))>0
        reach=math.ceil(((8./6.)+math.hypot(1/1.3608,1/1.701))*1.3608)
        for sy in range(pixels[0][0],pixels[-1][0]-1,-1):
            edges=np.diff(np.pad(geometry_asphalt[sy,1:83],(1,1)).astype(np.int16))
            starts=np.flatnonzero(edges==1)+1;ends=np.flatnonzero(edges==-1)+1;intervals=[]
            for ss,se in zip(starts,ends):
                ss,se=int(ss),int(se)
                if se-ss<3:continue
                lane_rows=[v for v in joint_info.get('current_two_flank_rows',[]) if v[0]==sy]
                lane=(lane_rows[0][1],lane_rows[0][2]+1) if len(lane_rows)==1 else observed_run(sy,IMAGE_ORIGIN_X,asphalt)
                near_lane=(joint_cover is not None and 54<=sy<=68 and lane is not None
                    and max(ss,lane[0])<min(se,lane[1]))
                # Same eight CURRENT samples and material guards. A blanket
                # near-car rectangle cannot veto an actually visible flank.
                edge_blocked=(obstacle_blocked|joint_cover.astype(bool)) if near_lane else blocked
                edge_max_row=69 if near_lane else 55
                a=recover_pixel_edge(image,sy,ss,1,edge_blocked,max_row=edge_max_row) if se-ss>=8 and not (near_lane and paint_near[sy,ss]) else None
                b=recover_pixel_edge(image,sy,se-1,-1,edge_blocked,max_row=edge_max_row) if se-ss>=8 and not (near_lane and paint_near[sy,se-1]) else None
                # Flat interior support can start several pixels inside a
                # perfectly visible edge. Inversion at that eroded anchor
                # misses its exterior plateau. Re-anchor to the enclosing
                # observed run, retaining the same monotone two-colour test
                # and flank inset; no unseen/material-filled pixels are added.
                # Flatness erosion and an object's hole can make this geometry
                # fragment narrow while the RAW observed plateau is complete.
                # Test the actual raw ray support, not the eroded run's width.
                if (a is None or b is None) and (sy<54 or near_lane):
                    raw=observed_run(sy,(ss+se-1)*.5,asphalt)
                    if raw is not None and raw[0]<=ss and raw[1]>=se:
                        for side,index,direction in ((0,raw[0],1),(1,raw[1]-1,-1)):
                            if (a if side==0 else b) is not None:continue
                            measured=recover_plain_run_edge(image,sy,index,direction,edge_blocked,paint_near,raw,max_row=edge_max_row)
                            raw_anchor_refined+=int(measured is not None)
                            if side==0:a=measured
                            else:b=measured
                if (a is None or b is None) and se-ss>=8 and 2<=sy<54:
                    before=observed_run(sy-1,(ss+se-1)*.5,geometry_asphalt)
                    after=observed_run(sy+1,(ss+se-1)*.5,geometry_asphalt)
                    if before is not None and after is not None and max(ss,before[0],after[0])<min(se,before[1],after[1]):
                        if a is None:
                            a=recover_curb_edge(image,sy,ss,1,(after[0]-before[0])*.5,blocked);curb_refined+=int(a is not None)
                        if b is None:
                            b=recover_curb_edge(image,sy,se-1,-1,(after[1]-before[1])*.5,blocked);curb_refined+=int(b is not None)
                if a is None and (1,sy) in band_edges and 0<ss-band_edges[(1,sy)]<=reach:
                    a=band_edges[(1,sy)];band_refined+=1
                if b is None and (0,sy) in band_edges and 0<band_edges[(0,sy)]-(se-1)<=reach:
                    b=band_edges[(0,sy)];band_refined+=1
                refined+=int(a is not None)+int(b is not None);unresolved+=int(a is None)+int(b is None)
                a=float(ss) if a is None else a;b=float(se-1) if b is None else b
                left=(a-IMAGE_ORIGIN_X)/1.3608+.35;right=(b-IMAGE_ORIGIN_X)/1.3608-.35
                if right>left:intervals.append((left,right))
            world_y=(IMAGE_ORIGIN_Y-sy)/1.701
            # Retain the continuous observed band instead of quantizing it to
            # pixel centres a second time. Same flank inset, visible vetoes,
            # and topology-aware strip construction still apply.
            band_intervals=[]
            for polygon in geometry_bands:
                # Newly seeded geometry is supported only in the original
                # forward observation domain. Do not project it behind that
                # domain into a vehicle-adjacent unobserved opposite flank.
                if id(polygon) in forward_band_ids and sy>54:continue
                crossings=[]
                for first,last in zip(polygon,np.roll(polygon,-1,axis=0)):
                    if first[1]==last[1] or (first[1]-world_y)*(last[1]-world_y)>0:continue
                    weight=(world_y-first[1])/(last[1]-first[1])
                    crossings.append(float(first[0]+weight*(last[0]-first[0])))
                if len(crossings)<2:continue
                band_intervals.append((min(crossings),max(crossings)))
            merged_bands=[]
            for left,right in sorted(band_intervals):
                if merged_bands and left<=merged_bands[-1][1]+1e-9:
                    merged_bands[-1]=(merged_bands[-1][0],max(merged_bands[-1][1],right))
                else:merged_bands.append((left,right))
            for left,right in merged_bands:
                lo=max(1,int(math.ceil(IMAGE_ORIGIN_X+1.3608*left)))
                hi=min(82,int(math.floor(IMAGE_ORIGIN_X+1.3608*right)))
                if lo>hi or np.any(geometry_veto[sy,lo:hi+1]):continue
                left+=.35;right-=.35
                if right>left:intervals.append((left,right))
            geometry_rows.append((world_y,intervals))
        roads,boundary=strip_union_mesh(geometry_rows,self.grip_prior)
        # Row topology closes a split/merge at an integer sample row. The
        # existing continuous width-conditioned band can support road between
        # those rows even when no direct curb fit is possible. Retain that
        # same evidence only where it actually crosses an interior mesh cap.
        caps=[edge for edge in boundary if abs(edge[0][1]-edge[1][1])<1e-10
              and geometry_rows[0][0]<edge[0][1]<geometry_rows[-1][0]]
        closure_patches=0
        for polygon in geometry_bands:
            patch=polygon.copy()
            for inner,outer in ((0,1),(3,2)):
                normal=patch[outer]-patch[inner];normal/=np.linalg.norm(normal)
                inset=.35*abs(float(normal[0]));patch[inner]+=inset*normal;patch[outer]-=inset*normal
            if not any(min(patch[:,1])<edge[0][1]<max(patch[:,1]) and core.polygon_distance(patch,edge)==0. for edge in caps):continue
            observed_curb_bands.append(patch);closure_patches+=1
        self.uncertainty['continuous_band_cap_proposals']=closure_patches
        accepted_patches=0
        for patch in observed_curb_bands:
            # Patches use adjacent direct curb fits or the existing two-sided
            # width-conditioned contour. Coherent grass, obstacles and opaque
            # support veto the whole patch; no observation gap is bridged.
            turns=[]
            for aa,bb,cc in zip(patch,np.roll(patch,-1,axis=0),np.roll(patch,-2,axis=0)):
                turns.append(float(np.cross(bb-aa,cc-bb)))
            if not (min(turns)>0 or max(turns)<0):continue
            px=IMAGE_ORIGIN_X+1.3608*patch[:,0];py=IMAGE_ORIGIN_Y-1.701*patch[:,1]
            x0,x1=int(math.ceil(min(px))),int(math.floor(max(px)))
            y0,y1=int(math.ceil(min(py))),int(math.floor(max(py)))
            if x0<1 or x1>82 or y0<5 or y1>54 or x0>x1 or y0>y1:continue
            yy,xx=np.indices((y1-y0+1,x1-x0+1));xx+=x0;yy+=y0
            wx=(xx-IMAGE_ORIGIN_X)/1.3608;wy=(IMAGE_ORIGIN_Y-yy)/1.701;signs=[]
            for aa,bb in zip(patch,np.roll(patch,-1,axis=0)):
                signs.append((bb[0]-aa[0])*(wy-aa[1])-(bb[1]-aa[1])*(wx-aa[0]))
            signs=np.asarray(signs);inside=np.all(signs>=0,axis=0)|np.all(signs<=0,axis=0)
            if not np.any(inside) or np.any(geometry_veto[yy[inside],xx[inside]]):continue
            roads.append((tuple(tuple(float(v) for v in point) for point in patch),self.grip_prior));accepted_patches+=1
        # Pavement inference and collision exclusion are independent. Existing
        # obstacle disks remain; compatible silhouette envelopes can only add
        # collision exclusion. These patches never enter the reference pixels.
        # A separate four-flank inset can leave a visible plateau seam
        # between this inferred patch and the row mesh. Reuse its CURRENT
        # explained ROI; no object fit or hidden-pixel inference is repeated.
        connector_mesh=tuple(roads);object_plateau_connectors=[]
        connector_opaque=vehicle_projection_mask(self.joint).astype(bool)
        for patch,record in zip(object_road_patches,object_road_records):
            object_plateau_connectors.extend(observed_object_plateau_connectors(
                image,patch,record['observed_roi_pixels'],connector_mesh,connector_opaque))
            roads.append((tuple(tuple(float(v) for v in point) for point in patch),self.grip_prior))
        for patch in object_plateau_connectors:
            roads.append((tuple(tuple(float(v) for v in point) for point in patch),self.grip_prior))
        self.uncertainty['object_current_plateau_connectors']=len(object_plateau_connectors)
        collision_obstacles=obstacles.copy()
        for center,radius in object_collision_envelopes:
            if not any(np.linalg.norm(np.asarray(center)-p)+radius<=r for p,r in obstacles):
                collision_obstacles.append((center,radius))
        self.uncertainty['object_road_support_inference']=object_road_records
        self.uncertainty['existing_collision_obstacles_preserved']=True
        self.uncertainty['object_collision_envelopes_added']=len(collision_obstacles)-len(obstacles)
        boundary=road_union_boundary(roads)
        self.uncertainty['continuous_observed_curb_patches']=accepted_patches
        self.uncertainty['mesh_source']='union of all supported row intervals; shared interfaces excluded'
        points=np.asarray([((a+b)*.5,y) for a,b,y in rows],np.float64)
        points,reference_info=reference_from_observed_width(points,reference_curves,asphalt,obstacle_blocked,self.reference_lattice,
            road_occlusion_patches=object_road_patches)
        self.uncertainty.update(reference_info)
        observed_reference=points.copy();source_stations=None;lattice_info={}
        if reference_info['observed_width_reference_used']:
            # Public centreline nodes are generated at21/6m. Pixel-dense fits
            # and coarser row samples must not enter curvature derivatives on
            # different spatial scales. Resample the estimated geometry only;
            # keep the original speed-profile formula and certification gates.
            points,lattice_info=observed_reference_lattice(points,self.reference_lattice)
            self.uncertainty.update(lattice_info)
            if lattice_info['reference_lattice_used']:
                source_stations=lattice_info['reference_lattice_phase_m']+(21./6.)*np.arange(len(points))
        else:
            points[:,0]=cv2.GaussianBlur(points[:,0].reshape(1,-1),(5,1),1.).ravel()
            observed_reference=points.copy()
        past,derivative_info=observed_reference_derivative_support(points,self.reference_lattice,
            lattice_info,image,obstacle_blocked,vehicle_projection_mask(self.joint).astype(bool))
        self.uncertainty.update(derivative_info)
        self.reference_lattice=points.copy() if source_stations is not None else []
        if source_stations is None:source_stations=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        points,curvature=deform_reference_with_derivative_support(points,observed_reference,source_stations,obstacles,past)
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        current=observed_reference_progress(points,arc,self.com)
        def reference(budget,max_speed):
            q=np.minimum(max_speed**2,budget/np.maximum(curvature,1e-6));q[-1]=0.
            for i in range(len(q)-2,-1,-1):q[i]=min(q[i],q[i+1]+2*45.*(arc[i+1]-arc[i]))
            q=np.minimum(q,2*core.REAR*np.maximum(0.,self.distance+arc-current))
            return dict(points=points.tolist(),arcs=arc.tolist(),ds=np.diff(arc).tolist(),length=float(arc[-1]),
                launch_squared=q.tolist(),periodic_squared=q[:-1].tolist(),observed_open=True)
        self.uncertainty.update(map='finite visible boundaries + explicitly conditioned local road inference',
            observation_support_m=[float(arc[0]),float(arc[-1])],global_map_available=False,
            raster_edges_refined=refined,raster_edges_unresolved=unresolved,
            raster_raw_anchor_edges_refined=raw_anchor_refined,
            raster_curb_edges_refined=curb_refined,
            raster_band_edges_refined=band_refined,
            subpixel_bound_universally_validated=False,obstacle_pixels_filled=False,
            obstacles='visible grayscale detections with0.4m radius inflation; unseen obstacles unknown')
        return core.Scene(roads,boundary,collision_obstacles),reference(153.,90.),reference(100.,80.),current

    def _root(self,scene,lateral_speed):
        yaw=self.yaw;rate=self.joint_rate
        center=tuple(float(x) for x in self.com)
        delta=self.com-self.hull_com
        lateral_speed=float(np.clip(lateral_speed,-self.speed,self.speed))
        # HUD speed is hull velocity magnitude, not its forward component.
        forward_speed=math.sqrt(max(0.,self.speed**2-lateral_speed**2))
        velocity=(lateral_speed-yaw*float(delta[1]),forward_speed+yaw*float(delta[0]))
        joints=(self.joint,self.joint,0.,0.);rates=(rate,rate,0.,0.)
        contacts=tuple(core.indexed_contacts(core.rectangle((center[0]+r[0],center[1]+r[1]),q),scene.roads,scene.index,.02) for r,q in zip(self.levers,joints))
        wheels=[]
        for i,(r,q) in enumerate(zip(self.levers,joints)):
            friction=max([240.*self.grip_prior,*[400.*scene.roads[j][1] for j in contacts[i]]])
            # Only the first observation uses a rolling prior. Later observations
            # retain wheel spin/throttle integrated from our own previous action;
            # camera-frame geometry and observable body estimates are rebuilt.
            omega,gas=((self.speed/.54,0.) if self.predicted_wheels is None else self.predicted_wheels[i])
            # Original _dynamics_tick stores the new yaw with the PREVIOUS
            # raw-tick lever. Rebase that velocity level into the current
            # camera frame; current geometric levers remain unchanged.
            angle=-core.DT*yaw;co,si=math.cos(angle),math.sin(angle)
            old_x=co*float(r[0])-si*float(r[1]);old_y=si*float(r[0])+co*float(r[1])
            wheels.append(core.Wheel(omega,gas,q,friction,(-yaw*old_y,yaw*old_x)))
        linear=core.State(velocity,tuple(wheels),self.mass,self.engine_prior)
        momentum=self.inertia*yaw+sum(self.wheel_inertia*r for r in rates)
        planar=core.Planar(linear,tuple(tuple(float(v) for v in r) for r in self.levers),self.inertia,momentum,yaw,0.,joints,rates,(self.wheel_inertia,)*4,-float(self.previous_action[0]),self.steering_prior)
        return core.Geometry(planar,center,scene.roads,contacts,240.*self.grip_prior,.02)

    def act(self,observation):
        obs=np.asarray(observation,np.float32)
        if obs.shape!=(4,84,84) or not np.isfinite(obs).all():raise ValueError('OBSERVATION_CONTRACT')
        lateral=self._state_estimates(obs)
        # The stack is actual history only where consecutive images differ.
        # At reset tiled copies contribute exactly one observation.
        frames=[]
        for frame in obs:
            if not frames or not np.array_equal(frame,frames[-1]):frames.append(frame.copy())
        if self.road_frames:
            matches=[i for i,frame in enumerate(frames) if np.array_equal(frame,self.road_frames[-1])]
            if matches:self.road_frames.extend(frames[matches[-1]+1:])
            else:self.road_frames=frames
        else:self.road_frames=frames
        self.road_frames=self.road_frames[-8:]
        transported,temporal=transport_road_evidence(self.road_frames)
        self.uncertainty.update(temporal)
        scene,high,low,progress=self._map(obs[-1],transported)
        root=self._root(scene,lateral)
        controller=core.Controller(high,low,scene)
        controller.model=self.counter
        self.calls+=1;before=self.counter[0]
        self.diagnostics=dict(runtime598_calls=self.calls,model_ticks_total=self.counter[0],
            input_kind='estimated_observation_only',true_state_certificate=False,
            prefix39_replacement='original feedback chooser from first decision; no saved commands',
            finite_path_change='no modulo/closing chord on observed_open path',
            uncertainty=dict(self.uncertainty),estimated_speed=self.speed,
            estimated_wheel_omega=[w.omega for w in root.planar.linear.wheels],
            wheel_state_propagated=self.predicted_wheels is not None)
        # Exact per-act memoization of the unchanged static contact function.
        # Forecast branches often repeat identical wheel polygons. Physics,
        # force evaluation and every model tick still execute normally.
        contact_function=core.indexed_contacts;contact_cache={};contact_hits=0;contact_misses=0
        contact_indices={id(scene.index):scene.index}
        def contacts(footprint,roads,index,skin):
            nonlocal contact_hits,contact_misses
            if roads is not scene.roads:return contact_function(footprint,roads,index,skin)
            if id(index) not in contact_indices:
                if index!=scene.index:return contact_function(footprint,roads,index,skin)
                contact_indices[id(index)]=index
            key=(tuple(tuple(v) for v in footprint),skin)
            if key in contact_cache:contact_hits+=1;return contact_cache[key]
            contact_misses+=1;value=contact_function(footprint,roads,index,skin)
            if len(contact_cache)<5000:contact_cache[key]=value
            return value
        core.indexed_contacts=contacts
        try:action,report=controller.select(root,progress,40,self.history,self.history)
        finally:core.indexed_contacts=contact_function
        self.diagnostics.update(geometry_contact_cache_hits=contact_hits,
            geometry_contact_cache_misses=contact_misses,geometry_contact_cache_entries=len(contact_cache))
        self.diagnostics.update(model_ticks_total=self.counter[0],decision_model_ticks=self.counter[0]-before,
            original_chooser_reason=report['mode'],estimated_admission=action is not None)
        trial_reports=report.get('trials',report.get('reports',[]))
        reasons=[q['reason'] for q in trial_reports]
        self.diagnostics['estimated_report_reasons']={reason:reasons.count(reason) for reason in set(reasons)}
        if action is None:raise RuntimeError('NO_ESTIMATED_INPUT_ADMISSIBLE_ACTION')
        self.previous_action=action.copy();self.last_root=root
        # History is explicitly model-predicted, not actual clipped-wheel truth.
        r=root
        for i in range(4):
            r=core.replace(r,planar=core.replace(r.planar,steer=-float(action[0])))
            forces=core.force_rows(r,action)
            self.history[0]+=sum(f['clipped'] for f in forces);self.history[1]+=4
            r=core.tick(r,float(action[1]),float(action[2]),scene.index,self.counter)
        self.predicted_wheels=tuple((w.omega,w.gas) for w in r.planar.linear.wheels)
        self.predicted_joints=r.planar.joints;self.predicted_joint_rates=r.planar.rates;self.predicted_yaw=r.planar.yaw
        velocity=core.hull_pose(r)[1];angle=r.planar.angle
        self.predicted_hull_speed=math.hypot(*velocity)
        self.predicted_hull_velocity_body=(math.cos(angle)*velocity[0]+math.sin(angle)*velocity[1],
            -math.sin(angle)*velocity[0]+math.cos(angle)*velocity[1])
        before_origin=core.hull_pose(root)[0];after_origin=core.hull_pose(r)[0]
        dx,dy=((after_origin[j]-before_origin[j])/.08 for j in range(2))
        self.predicted_average_hull_velocity_body=(math.cos(angle)*dx+math.sin(angle)*dy,-math.sin(angle)*dx+math.cos(angle)*dy)
        self.predicted_average_yaw=(r.planar.angle-root.planar.angle)/.08
        # Correspondence seeds, not retained road support: exact own-action
        # endpoint pose takes current observed edges into the next camera.
        rotation=np.array([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
        self.reference_seeds=[dict(outer_side=seed['outer_side'],
            edge_points=(seed['edge_points']-np.asarray(after_origin))@rotation.T,
            edge_normals=seed['edge_normals']@rotation.T) for seed in self.reference_seeds]
        self.reference_lattice=(np.asarray(self.reference_lattice)-np.asarray(after_origin))@rotation.T if len(self.reference_lattice) else []
        for track in self.obstacle_tracks:
            track['center']=((np.asarray(track['center'])-np.asarray(after_origin))@rotation.T).tolist()
        self.diagnostics['model_ticks_total']=self.counter[0]
        return action

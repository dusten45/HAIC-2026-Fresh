"""Image-only proposal features for the public local tile grammar.

Only numpy/cv2/math are used. These are engineering proposals, not material,
geometry or alias-coverage certificates. No hidden pixels are filled. A caller
must validate proposed geometry against current observations and all admission
gates. Stored node normal and generator heading are deliberately distinguished.
"""
import math

import cv2
import numpy as np

STEP=21./6.
HALF_WIDTH=40./6.
TURN=.31
SX=84./1000.*16.2
SY=84./800.*16.2
ORIGIN_X=(500.+.5)*84./1000.-.5
ORIGIN_Y=(599.+.5)*84./800.-.5


def _raw(point):
    x,y=point
    return [(x+.5)*1000./84.-.5,799.5-(y+.5)*800./84.]


def _body(point):
    return [(point[0]-ORIGIN_X)/SX,(ORIGIN_Y-point[1])/SY]


def _line(points):
    p=np.asarray(points,float)
    matrix=np.column_stack((p[:,1],np.ones(len(p))))
    coefficient=np.linalg.lstsq(matrix,p[:,0],rcond=None)[0]
    residual=matrix@coefficient-p[:,0]
    return dict(slope=float(coefficient[0]),intercept=float(coefficient[1]),
        y_min=float(p[:,1].min()),y_max=float(p[:,1].max()),
        SSE=float(residual@residual),points=len(p))


def _segments(points):
    """Retain several discrete one-kink fits rather than one best geometry."""
    if len(points)<3:return [],[]
    ordered=sorted(points,key=lambda p:p[1]);single=_line(ordered);fits=[]
    for split in range(3,len(ordered)-2):
        first,second=_line(ordered[:split]),_line(ordered[split:])
        fits.append(dict(first=first,second=second,SSE=first['SSE']+second['SSE'],
            break_y_interval=[ordered[split-1][1],ordered[split][1]]))
    fits=sorted(fits,key=lambda p:p['SSE'])[:4]
    corners=[]
    for fit in fits:
        a,b=fit['first'],fit['second'];gap=a['slope']-b['slope']
        if abs(gap)<=np.finfo(float).eps:continue
        y=(b['intercept']-a['intercept'])/gap
        low,high=fit['break_y_interval']
        if not low-1<=y<=high+1:continue
        corners.append(dict(point=[a['slope']*y+a['intercept'],y],SSE=fit['SSE'],
            first=a,second=b,break_y_interval=fit['break_y_interval']))
    segments=[single]
    for fit in fits:segments.extend((fit['first'],fit['second']))
    return segments,corners


def _node(left,right,kind,score,support,extra=None):
    p,q=np.asarray(left,float),np.asarray(right,float)
    if p[0]>=q[0]:return None
    dx,dy=(q[0]-p[0])/SX,-(q[1]-p[1])/SY
    width=math.hypot(dx,dy)
    # Same public-width/raster conditioning tolerance as the baseline helper.
    tolerance=2/SX+2*HALF_WIDTH*(1/math.cos(TURN)-1)
    if abs(width-2*HALF_WIDTH)>tolerance:return None
    center=((p+q)*.5).tolist();normal=math.atan2(dy,dx)
    result=dict(kind=kind,center_image=center,center_raw=_raw(center),
        center_body=_body(center),normal_angle=normal,width_m=width,
        left_point=p.tolist(),right_point=q.tolist(),proposal_score=float(score),
        observed_support_points=int(support),phase_aliases=list(range(6)),
        mechanical_heading_relation=[normal-TURN/2,normal+TURN/2])
    if extra:result.update(extra)
    return result


def extract_tile_initializers(image,vehicle_mask,*,observed_mask=None,maximum_node_candidates=32):
    """Propose current flank/corner/shade-seam nodes and two-node generators.

    ROI is derived from the vehicle mask and public lane width/tile spacing.
    Gray100/102/105 labels are public pinned-pipeline plateau signatures, not a
    proof of road material. Phase/contact/border alternatives remain unresolved.
    Candidate ranking/caps only control seed work and NEVER imply completeness.
    """
    image=np.asarray(image)
    if not isinstance(maximum_node_candidates,int) or maximum_node_candidates<1:
        raise ValueError('Positive node candidate cap required')
    if image.shape!=(84,84) or np.asarray(vehicle_mask).shape!=image.shape:
        raise ValueError('84x84 image and vehicle mask required')
    if image.dtype==np.uint8:gray=image
    elif np.issubdtype(image.dtype,np.floating) and np.all(np.isfinite(image)):
        if np.any(image<0) or np.any(image>1):raise ValueError('Normalized gray outside0..1')
        gray=np.rint(image*255).astype(np.uint8)
    else:raise ValueError('uint8 or normalized floating gray required')
    cover=np.asarray(vehicle_mask,bool)
    visible=np.ones_like(cover) if observed_mask is None else np.asarray(observed_mask,bool)
    if visible.shape!=gray.shape:raise ValueError('Observed mask shape mismatch')
    visible=visible & ~cover
    cy,cx=np.nonzero(cover)
    if not len(cx):raise ValueError('Nonempty vehicle mask required for derived ROI')
    padx=math.ceil(2*HALF_WIDTH*SX);forward=math.ceil(2*STEP*SY);backward=math.ceil(STEP*SY)
    x0,x1=max(1,int(cx.min())-padx),min(83,int(cx.max())+padx+1)
    y0,y1=max(5,int(cy.min())-forward),min(70,int(cy.max())+backward+1)
    roi=np.zeros_like(cover);roi[y0:y1,x0:x1]=True;visible &= roi
    asphalt=visible & (gray>.36*255) & (gray<.47*255)
    flanks=[[],[]];row_records=[]
    for y in range(y0,y1):
        row=asphalt[y];edge=np.diff(np.pad(row,(1,1)).astype(np.int16));starts=np.flatnonzero(edge==1);ends=np.flatnonzero(edge==-1)
        near=[i for i,(a,b) in enumerate(zip(starts,ends)) if a<=ORIGIN_X<b]
        if near:
            i=max(near,key=lambda i:ends[i]-starts[i]);left,right=int(starts[i]),int(ends[i])
        else:
            ls=[i for i in range(len(starts)) if ends[i]<=math.ceil(ORIGIN_X)]
            rs=[i for i in range(len(starts)) if starts[i]>=math.floor(ORIGIN_X)]
            if not ls or not rs:continue
            l=max(ls,key=lambda i:ends[i]);r=min(rs,key=lambda i:starts[i]);left,right=int(starts[l]),int(ends[r])
        if left==x0 or right==x1:continue
        horizontal_width=(right-left)/SX
        raster_width_slack=2/SX+2*HALF_WIDTH*(1/math.cos(TURN)-1)
        if not 2*HALF_WIDTH-raster_width_slack<=horizontal_width<=2*HALF_WIDTH/math.cos(TURN)+raster_width_slack:
            continue
        flanks[0].append([left-.5,float(y)]);flanks[1].append([right-.5,float(y)])
        row_records.append(dict(y=y,left=left-.5,right=right-.5))
    segments=[];corners=[]
    for points in flanks:
        s,c=_segments(points);segments.append(s);corners.append(c)
    candidates=[]
    for left in corners[0]:
        for right in corners[1]:
            node=_node(left['point'],right['point'],'flank_corner_pair',
                -(left['SSE']+right['SSE']),left['first']['points']+left['second']['points']+
                right['first']['points']+right['second']['points'])
            if node:candidates.append(node)
    # Label-to-label transitions must have actual visible samples on both sides.
    # Hough finds proposals only; complete source-cell material is NOT asserted.
    labels=np.full(gray.shape,-1,np.int16)
    plateau=visible & (gray>=100) & (gray<=105)
    # Downsampling mixes neighboring tile shades before gray quantization.
    # Nearest plateau codes propose seam locations; they certify no material.
    distances=np.abs(gray.astype(np.int16)[:,:,None]-np.array([100,102,105]))
    labels[plateau]=np.argmin(distances,axis=2)[plateau]
    seam_points=[]
    for y in range(y0,y1-1):
        for x in range(x0,x1-1):
            if labels[y,x]<0:continue
            for dx,dy in ((1,0),(0,1)):
                other=labels[y+dy,x+dx]
                if other>=0 and other!=labels[y,x]:
                    seam_points.append((x+dx*.5,y+dy*.5,tuple(sorted((int(labels[y,x]),int(other))))))
    seam_records=[]
    for pair in ((0,1),(1,2),(0,2)):
        points=np.asarray([[x,y] for x,y,p in seam_points if p==pair],float)
        if len(points)<3:continue
        binary=np.zeros((84,84),np.uint8)
        for x,y in points:binary[int(round(y)),int(round(x))]=255
        minimum=max(3,int(2*HALF_WIDTH*SX/5))
        lines=cv2.HoughLinesP(binary,1,np.pi/180,threshold=minimum,
            minLineLength=minimum,maxLineGap=1)
        line_proposals=[] if lines is None else list(lines[:,0,:])
        # Resampling can leave a genuine shade seam disconnected in the
        # integer Hough bitmap. Actual half-pixel transition coordinates still
        # supply line proposals without filling any unobserved image sample.
        point_lines={}
        for i in range(len(points)):
            for j in range(i+1,len(points)):
                delta=points[j]-points[i];length=np.linalg.norm(delta)
                if length<minimum:continue
                direction=delta/length
                distance=np.abs((points[:,0]-points[i,0])*direction[1]-(points[:,1]-points[i,1])*direction[0])
                ids=tuple(np.flatnonzero(distance<=1.))
                if len(ids)>=3:point_lines.setdefault(ids,np.r_[points[i],points[j]])
        line_proposals.extend(value for _,value in sorted(point_lines.items(),key=lambda kv:len(kv[0]),reverse=True)[:12])
        for raw_line in line_proposals:
            p=raw_line[:2].astype(float);v=raw_line[2:].astype(float)-p;length=np.linalg.norm(v)
            if length==0:continue
            v/=length
            if v[0]<0:v=-v
            residual=np.abs((points[:,0]-p[0])*v[1]-(points[:,1]-p[1])*v[0])
            inliers=points[residual<=1.]
            if len(inliers)<3:continue
            center=inliers.mean(axis=0);_,_,vh=np.linalg.svd(inliers-center,full_matrices=False);v=vh[0]
            if v[0]<0:v=-v
            if abs(v[0])<np.finfo(float).eps:continue
            record=dict(point=center.tolist(),direction=v.tolist(),support=len(inliers),
                palette_pair=[(100,102,105)[i] for i in pair])
            seam_records.append(record)
            for left in segments[0]:
                for right in segments[1]:
                    intersections=[]
                    for edge in (left,right):
                        denominator=v[0]-edge['slope']*v[1]
                        if abs(denominator)<np.finfo(float).eps:break
                        t=(edge['slope']*center[1]+edge['intercept']-center[0])/denominator
                        point=center+t*v
                        if not edge['y_min']-1<=point[1]<=edge['y_max']+1:break
                        intersections.append(point)
                    if len(intersections)!=2:continue
                    node=_node(*intersections,'shade_seam',len(inliers)/(1+left['SSE']+right['SSE']),len(inliers),
                        dict(palette_pair=record['palette_pair']))
                    if node:candidates.append(node)
    candidates.sort(key=lambda p:(p['observed_support_points'],p['proposal_score']),reverse=True)
    # Near-duplicate seed removal is computational only, not an alias proof.
    unique=[]
    for candidate in candidates:
        if any(np.linalg.norm(np.asarray(candidate['center_image'])-u['center_image'])<.25 and
                abs(candidate['normal_angle']-u['normal_angle'])<.01 for u in unique):continue
        unique.append(candidate)
        if len(unique)>=maximum_node_candidates:break
    links=[]
    for first in unique:
        for second in unique:
            a,b=np.asarray(first['center_body']),np.asarray(second['center_body']);delta=b-a
            if delta[1]<=0:continue
            distance=float(np.linalg.norm(delta))
            if abs(distance-STEP)>2*math.hypot(1/SX,1/SY):continue
            tangent=math.atan2(-delta[0],delta[1]);beta0,beta1=first['normal_angle'],second['normal_angle']
            d0,d1=2*(tangent-beta0),2*(beta1-tangent)
            if max(abs(d0),abs(d1))>TURN:continue
            links.append(dict(center_raw_xy=first['center_raw'],generator_heading=2*beta0-tangent,
                turn_updates=[d0,d1],estimated_node_distance_m=distance,
                first_kind=first['kind'],second_kind=second['kind'],phase_aliases=list(range(6))))
    kink_seeds=[]
    for corner in (p for p in unique if p['kind']=='flank_corner_pair'):
        far=[p for p in unique if p['kind']=='shade_seam' and
            p['center_body'][1]>corner['center_body'][1]+STEP]
        bottom_segments=[edge for side in segments for edge in side if
            edge['y_max']>=corner['center_image'][1]-1 and edge['points']>=3]
        bottom_segments.sort(key=lambda edge:edge['SSE']/edge['points'])
        for edge in bottom_segments[:2]:
            heading=math.atan(edge['slope']*SY/SX)
            for upper in far[:4]:
                raw_turn=2*(corner['normal_angle']-heading)
                turn0=max(-TURN,min(TURN,raw_turn))
                turn1=upper['normal_angle']-heading-turn0
                if abs(turn1)>TURN:continue
                kink_seeds.append(dict(center_raw_xy=corner['center_raw'],generator_heading=heading,
                    turn_updates=[turn0,turn1],phase_aliases=list(range(6)),
                    seed_kind='corner_far_flank_projection',
                    unconstrained_turn0=raw_turn,public_turn_projection=turn0!=raw_turn,
                    limits='Engineering initializer only: noisy flank/corner estimates projected into public turn bounds; no state or safety constraint changed.'))
    return dict(status='ENGINEERING_FEATURE_PROPOSALS_ONLY',roi_xyxy=[x0,y0,x1,y1],
        visible_flank_points=flanks,row_flanks=row_records,flank_segments=segments,
        flank_corners=corners,shade_seams=seam_records,node_candidates=unique,
        shade_transition_points=[dict(point=[x,y],palette_pair=[(100,102,105)[i] for i in pair]) for x,y,pair in seam_points],
        generator_pair_seeds=links,kink_to_straight_seeds=kink_seeds,all_phase_aliases=list(range(6)),
        full_render_zero_verified=False,parameter_coverage_proved=False,
        limits='Raster thresholds/Hough/segmented fits only generate seeds. No hidden road support, phase/contact uniqueness, geometry completeness or admission is inferred.')

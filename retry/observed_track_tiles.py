"""Public ordinary-track tile/paint hypotheses; no track or simulator access.

The local generator reproduces step/normal timing and ordered polygon formulas
in core/vendor/car_racing.py. It does not solve destination-checkpoint dynamics,
global closure, unseen tile continuation, border history or scene completeness.
Actual-frame fitting/parameter coverage is a separate caller responsibility.
"""
import math

STEP=21./6.
TURN=.31
WIDTH=40./6.
BORDER=8./6.
GRASS_DIM=(2000./6.)/20.
PUBLIC_ZOOM=2.7*6.
CLIP_MARGIN=max(GRASS_DIM,WIDTH,STEP)*math.sqrt(2)*PUBLIC_ZOOM
GRASS_BACKGROUND_BOUNDS=((102,204,102),(102,230,102))


def local_nodes(center_raw_xy,generator_heading,turn_updates,*,zoom=PUBLIC_ZOOM):
    """First node center is supplied; N updates produce N stored track nodes.

    Stored normal is (heading_before+heading_after)/2. The next center advances
    STEP along the tangent of heading_after, NOT the stored average normal.
    """
    turns=tuple(float(v) for v in turn_updates)
    if len(turns)<2:raise ValueError('At least2 node updates required')
    if len(center_raw_xy)!=2 or not all(math.isfinite(float(v)) for v in center_raw_xy):
        raise ValueError('Finite raw center pair required')
    if not math.isfinite(generator_heading) or not math.isfinite(zoom) or zoom<=0:
        raise ValueError('Finite heading and positive zoom required')
    if any(not math.isfinite(v) or abs(v)>TURN for v in turns):
        raise ValueError('Each generator turn must be within public .31rad bound')
    heading=float(generator_heading);x=y=0.;nodes=[]
    for i,turn in enumerate(turns):
        if i:x+=-math.sin(heading)*STEP;y+=math.cos(heading)*STEP
        before=heading;heading=before+turn
        normal=before*.5+heading*.5
        nodes.append(dict(body_center=(x,y),raw_center=(float(center_raw_xy[0])+zoom*x,float(center_raw_xy[1])+zoom*y),
            generator_before=before,generator_after=heading,normal_angle=normal,turn_update=turn))
    return nodes


def interior_border_flags(nodes):
    """Ordinary nonclosing border flags; missing lookbehind/lookahead -> None.

    A tile is painted if any of its next4 run-end flags marks four consecutive
    same-sign stored-normal changes exceeding .2*TURN. Full cyclic seam
    propagation is deliberately not inferred from a local node fragment.
    """
    beta=[n['normal_angle'] for n in nodes];flags=[]
    def run_end(j):
        if j<4 or j>=len(beta):return None
        changes=[beta[k]-beta[k-1] for k in range(j-3,j+1)]
        return all(abs(v)>TURN*.2 for v in changes) and (all(v>0 for v in changes) or all(v<0 for v in changes))
    for i in range(1,len(nodes)):
        possible=[run_end(j) for j in range(i,i+4)]
        flags.append(True if True in possible else False if all(v is False for v in possible) else None)
    return flags


def generate_tile_layers(center_raw_xy,generator_heading,turn_updates,*,index_phase6,
                         contact_reset_flags=None,border_flags=None,zoom=PUBLIC_ZOOM):
    """Return ordered integer original polygons and their unrounded geometry.

    index_phase6 is the first NODE's global index modulo6. Tile i joins node i
    to i-1 and shares one index for road shade modulo3 and paint parity modulo2.
    Contact flags: False original shade, True contact-reset102, None either.
    Border flags: True/False exact supplied activation, None optional. Omitted
    border flags use only locally decidable ordinary history, preserving unknown
    cases as optional. Nuisance choices must be enumerated for exact inversion;
    None yields a color/presence enclosure rather than a unique rendered scene.
    """
    if not isinstance(index_phase6,int) or not 0<=index_phase6<6:
        raise ValueError('index_phase6 must be integer0..5')
    nodes=local_nodes(center_raw_xy,generator_heading,turn_updates,zoom=zoom);count=len(nodes)-1
    contacts=[None]*count if contact_reset_flags is None else list(contact_reset_flags)
    borders=interior_border_flags(nodes) if border_flags is None else list(border_flags)
    if len(contacts)!=count or len(borders)!=count or any(v is not None and not isinstance(v,bool) for v in contacts+borders):
        raise ValueError('One Boolean-or-None flag per tile required')
    layers=[];tiles=[]
    def project(point):
        return (float(center_raw_xy[0])+zoom*point[0],float(center_raw_xy[1])+zoom*point[1])
    def layer(points,lo,hi,optional,kind,index):
        original=[project(point) for point in points]
        if not all(math.isfinite(v) and -32768<=v<=32767 for point in original for v in point):
            raise ValueError('Original projected vertices exceed safe Sint16 range')
        if not any(-CLIP_MARGIN<=x<=1000+CLIP_MARGIN and -CLIP_MARGIN<=y<=800+CLIP_MARGIN for x,y in original):
            return
        layers.append(dict(vertices=[(math.trunc(x),math.trunc(y)) for x,y in original],
            original_vertices=original,rgb_lo=lo,rgb_hi=hi,optional=optional,kind=kind,tile_index_phase=index%6))
    for i in range(1,len(nodes)):
        current,previous=nodes[i],nodes[i-1]
        n1=(math.cos(current['normal_angle']),math.sin(current['normal_angle']))
        n2=(math.cos(previous['normal_angle']),math.sin(previous['normal_angle']))
        p1,p2=current['body_center'],previous['body_center']
        offset=lambda p,n,d:(p[0]+d*n[0],p[1]+d*n[1])
        index=index_phase6+i;shade=int(102+.01*(index%3)*255)
        contact=contacts[i-1]
        low=102 if contact is not False else shade
        high=102 if contact is True else shade
        layer([offset(p1,n1,-WIDTH),offset(p1,n1,WIDTH),offset(p2,n2,WIDTH),offset(p2,n2,-WIDTH)],
            (low,)*3,(high,)*3,False,'road',index)
        difference=previous['normal_angle']-current['normal_angle']
        side=1 if difference>0 else -1 if difference<0 else 0
        if borders[i-1] is not False:
            color=(255,255,255) if index%2==0 else (255,0,0)
            layer([offset(p1,n1,side*WIDTH),offset(p1,n1,side*(WIDTH+BORDER)),
                offset(p2,n2,side*(WIDTH+BORDER)),offset(p2,n2,side*WIDTH)],
                color,color,borders[i-1] is None,'border',index)
        tiles.append(dict(local_tile=i,index_phase6=index%6,original_road_gray=shade,
            contact_reset=contact,border_present=borders[i-1],border_side=side))
    return dict(nodes=nodes,layers=layers,tiles=tiles,background_bounds=GRASS_BACKGROUND_BOUNDS,
        metadata=dict(local_ordinary_only=True,closing_seam_included=False,
            node_spacing_m=STEP,turn_update_bound_rad=TURN,
            contact_history_unknown=any(v is None for v in contacts),
            border_history_unknown=any(v is None for v in borders),
            grass_checkerboard_geometry='UNKNOWN: default background is a pointwise palette enclosure, not one exact checkerboard.',
            original_parameter_coverage_proved=False,scene_complete=False,
            generator_scope='Necessary public step/turn and exact road/paint polygon formulas; destination/checkpoint/global-closure constraints not solved.'))


def grass_checker_layers(*,world_to_body_angle,world_to_body_translation,
                         raw_origin=(500.,200.),zoom=PUBLIC_ZOOM):
    """Exact public checker polygons for an EXPLICIT hypothesized camera pose.

    This receives no environment state. The caller must enumerate camera
    angle/translation uncertainty. The official pattern is 20x20 isolated green
    squares, each GRASS_DIM wide on a2*GRASS_DIM period in both axes, over the
    light-green field (not a50%-area chessboard). Field/viewport edges remain a
    separate scene-completeness requirement.
    """
    values=(world_to_body_angle,*world_to_body_translation,*raw_origin,zoom)
    if not all(math.isfinite(v) for v in values) or zoom<=0:raise ValueError('Finite camera hypothesis required')
    c,s=math.cos(world_to_body_angle),math.sin(world_to_body_angle);tx,ty=world_to_body_translation
    layers=[]
    for x in range(-20,20,2):
        for y in range(-20,20,2):
            points=[(GRASS_DIM*x+GRASS_DIM,GRASS_DIM*y),(GRASS_DIM*x,GRASS_DIM*y),
                (GRASS_DIM*x,GRASS_DIM*y+GRASS_DIM),(GRASS_DIM*x+GRASS_DIM,GRASS_DIM*y+GRASS_DIM)]
            original=[(raw_origin[0]+zoom*(c*px-s*py+tx),raw_origin[1]+zoom*(s*px+c*py+ty)) for px,py in points]
            if not any(-CLIP_MARGIN<=px<=1000+CLIP_MARGIN and -CLIP_MARGIN<=py<=800+CLIP_MARGIN for px,py in original):continue
            if not all(-32768<=v<=32767 for point in original for v in point):raise ValueError('Checker vertex outside Sint16 range')
            layers.append(dict(vertices=[(math.trunc(px),math.trunc(py)) for px,py in original],
                original_vertices=original,rgb_lo=(102,230,102),rgb_hi=(102,230,102),optional=False,kind='grass_checker'))
    return layers

"""One fixed Hermite construction, profile, mapping and sampled-chain checks.
No dynamics, force kernel, optimizer, environment or participant imports.
"""
import bisect,math
import numpy as np
from retry.envelope500 import MASS,REAR


def endpoint(path,s):
    # Left segment at exact vertex, clamped first-lap interpolation.
    s=max(0.,min(float(s),path['length']));i=min(len(path['ds'])-1,bisect.bisect_left(path['arcs'][1:],s));f=(s-path['arcs'][i])/path['ds'][i]
    a=np.asarray(path['points'][i],float);b=np.asarray(path['points'][(i+1)%len(path['points'])],float);t=(b-a)/np.linalg.norm(b-a);k=(1-f)*path['curvature'][i]+f*path['curvature'][(i+1)%len(path['points'])]
    return a+f*(b-a),t,float(k),i,float(f)


def coefficients(p0,p1,d0,d1,a0,a1):
    c0=np.asarray(p0,float);c1=np.asarray(d0,float);c2=np.asarray(a0,float)/2
    A=np.asarray(p1,float)-c0-c1-c2;B=np.asarray(d1,float)-c1-2*c2;C=np.asarray(a1,float)-2*c2
    return np.asarray([c0,c1,c2,10*A-4*B+C/2,-15*A+7*B-C,6*A-3*B+C/2])


def evaluate(c,u,derivative=0):
    out=np.zeros(2)
    for i in range(5,derivative-1,-1):
        factor=math.prod(range(i-derivative+1,i+1))
        out=out*u+factor*c[i]
    return out


def signed_curvature(points):
    p=np.asarray(points,float);v=np.roll(p,-1,axis=0)-p;ds=np.linalg.norm(v,axis=1)
    if not np.all(np.isfinite(p)) or np.any(ds<=0):raise ValueError('NONFINITE_OR_ZERO_LENGTH_GEOMETRY')
    w=np.roll(v,1,axis=0);cross=w[:,0]*v[:,1]-w[:,1]*v[:,0];dot=np.sum(w*v,axis=1)
    return ds,np.arctan2(cross,dot)/((np.roll(ds,1)+ds)/2)


def construct(old):
    p0,t0,k0,_,_=endpoint(old,90.);p1,t1,k1,_,_=endpoint(old,220.);chord=p1-p0;L=float(np.linalg.norm(chord))
    if not L>0:raise ValueError('ZERO_ENDPOINT_CHORD')
    c=coefficients(p0,p1,L*t0,L*t1,L*L*k0*np.array([-t0[1],t0[0]]),L*L*k1*np.array([-t1[1],t1[0]]))
    u=np.arange(513,dtype=float)/512;curve=np.asarray([evaluate(c,x) for x in u]);d1=np.asarray([evaluate(c,x,1) for x in u]);d2=np.asarray([evaluate(c,x,2) for x in u]);norm=np.linalg.norm(d1,axis=1)
    # Pin exact endpoint position data against finite Horner endpoint roundoff.
    curve[0]=p0;curve[-1]=p1
    ak=np.divide(d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0],norm**3,out=np.full(513,np.nan),where=norm>0)
    left=[i for i,s in enumerate(old['arcs'][:-1]) if s<90.];right=[i for i,s in enumerate(old['arcs'][:-1]) if s>220.]
    pts=np.asarray([old['points'][i] for i in left]+curve.tolist()+[old['points'][i] for i in right]);sigma=np.asarray([old['arcs'][i] for i in left]+(90+130*u).tolist()+[old['arcs'][i] for i in right]);ds,k=signed_curvature(pts);arcs=np.r_[0.,np.cumsum(ds)]
    path=dict(points=pts.tolist(),ds=ds.tolist(),arcs=arcs.tolist(),length=float(arcs[-1]),curvature=k.tolist());start=len(left);end=start+512
    check_nodes=[(start-1)%len(pts),*range(start,end+1),(end+1)%len(pts)];old_nodes=[i for i,s in enumerate(old['arcs'][:-1]) if 90<=s<=220];li=left[-1];ri=right[0];old_nodes=[li,*old_nodes,ri]
    _,oldk=signed_curvature(old['points'])
    old_peak=float(np.max(np.abs(oldk[old_nodes])));new_peak=max(float(np.max(np.abs(k[check_nodes]))),float(np.nanmax(np.abs(ak))))
    return dict(path=path,oldstation=sigma.tolist(),coefficients=c.tolist(),curve=curve.tolist(),d1=d1.tolist(),analytic_curvature=ak.tolist(),new_start=start,new_end=end,diagnostics=dict(samples=513,chord_length_m=L,old_replaced_arc_m=130.,new_replaced_arc_m=float(sum(ds[start:end])),minimum_derivative_norm=float(norm.min()),minimum_forward_chord_derivative=float(np.min(d1@chord/L)),old_peak_abs_curvature=old_peak,new_peak_abs_curvature=new_peak,new_sampled_node_peak_abs_curvature=float(np.max(np.abs(k[check_nodes]))),new_analytic_peak_abs_curvature=float(np.nanmax(np.abs(ak))),peak_reduction=old_peak-new_peak,full_path_old_length_m=old['length'],full_path_new_length_m=path['length']))


def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def segment_intersects(a,b,c,d):
    o=[orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)]
    if o[0]*o[1]<0 and o[2]*o[3]<0:return True
    def on(p,q,r):return min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])
    return any(z==0 and on(p,q,r) for z,p,q,r in [(o[0],a,b,c),(o[1],a,b,d),(o[2],c,d,a),(o[3],c,d,b)])


def intersections(points,count,guard):
    p=np.asarray(points,float);q=np.roll(p,-1,axis=0);lo=np.minimum(p,q);hi=np.maximum(p,q);n=len(p);hits=[]
    for i in range(n):
        guard();ids=np.arange(i+2,n)
        if i==0:ids=ids[ids!=n-1]
        count('static_segment_AABB_pairs',len(ids));mask=np.all(hi[i]>=lo[ids],axis=1)&np.all(hi[ids]>=lo[i],axis=1)
        for j in ids[mask]:
            count('static_segment_exact_tests',1)
            if segment_intersects(p[i],q[i],p[j],q[j]):hits.append([i,int(j)])
    return hits


def interpolate_squared(path,s,launch):
    if launch:u=min(path['length'],max(0.,s));values=path['launch_squared']
    else:u=s%path['length'];values=path['periodic_squared']+[path['periodic_squared'][0]]
    i=min(len(path['ds'])-1,bisect.bisect_left(path['arcs'][1:],u));f=min(1.,max(0.,(u-path['arcs'][i])/path['ds'][i]));return values[i]+f*(values[i+1]-values[i])


def project(point,path,previous=None):
    L=path['length'];rows=[]
    for i,a in enumerate(path['points']):
        b=path['points'][(i+1)%len(path['points'])];v=np.asarray(b)-a;f=float(np.clip(np.dot(np.asarray(point)-a,v)/np.dot(v,v),0,1));pos=np.asarray(a)+f*v;s=path['arcs'][i]+f*path['ds'][i]
        if previous is None:s=s if s<=L/2 else s-L
        else:s+=round((previous-s)/L)*L
        if previous is None or previous-5<=s<=previous+30:rows.append(dict(s=s,distance=float(np.linalg.norm(np.asarray(point)-pos)),i=i,t=f))
    if not rows:raise ValueError('PROJECTION_CONTINUITY_DOMAIN')
    return min(rows,key=lambda z:z['distance'])


def retime(path,oldbackup,sigma,static,count,guard):
    # Exact549 branch ordering, using ONLY new geometric curvature.
    p=static['root']['planar'];mass=p['linear']['mass'];a=p['angle'];f=(-math.sin(a),math.cos(a));front=sum(sum(f[j]*r[j] for j in range(2)) for r in p['levers'][:2])/2;rear=-sum(sum(f[j]*r[j] for j in range(2)) for r in p['levers'][2:])/2;coeff=[mass*rear/(front+rear)/2]*2+[mass*front/(front+rear)/2]*2;mu=[w['friction'] for w in p['linear']['wheels']]
    if mu!=[400.]*4:raise ValueError('FROZEN_ROAD_FRICTION_DOMAIN')
    limit=[.999*z for z in mu];n=len(path['ds']);K=np.abs(path['curvature']);segment=[max(K[i],K[(i+1)%n]) for i in range(n)];cap=[]
    def charge():guard();count('analytic_profile_bound_evaluations',1)
    for i in range(n):
        charge();support=max(segment[i-1],segment[i]);cap.append(min(90.**2,min(limit[j]/(coeff[j]*max(support,1e-12)) for j in range(4))))
    def acc(q,k,braking):
        charge();lat=[c*q*k for c in coeff];available=[math.sqrt(max(0.,lim**2-z**2)) for lim,z in zip(limit,lat)]
        if braking:return min(80.,min(4*z/mass for z in available))
        return min(REAR,80000./(MASS*(math.sqrt(max(q,0.))+2.7)),min(2*z/mass for z in available[2:]))
    def restrict(current,other,k,ds,braking):
        if current<=other:return current
        if current-other<=2*acc(current,k,braking)*ds:return current
        lo=other;hi=current
        for _ in range(40):
            count('profile_bisection_updates',1);mid=(lo+hi)/2
            if mid-other<=2*acc(mid,k,braking)*ds:lo=mid
            else:hi=mid
        return lo
    q=cap.copy()
    for it in range(2*n):
        guard();before=q.copy()
        for i in range(n-1,-1,-1):q[i]=restrict(q[i],q[(i+1)%n],segment[i],path['ds'][i],True)
        for i in range(n):j=(i+1)%n;q[j]=restrict(q[j],q[i],segment[i],path['ds'][i],False)
        count('profile_periodic_passes',1)
        if q==before:break
    else:raise ValueError('FINITE_PROFILE_PASSES_EXHAUSTED')
    launch=[0.]
    for i,ds in enumerate(path['ds']):launch.append(restrict(q[(i+1)%n],launch[-1],segment[i],ds,False))
    peak=0.
    for values in [q+[q[0]],launch]:
        for i,ds in enumerate(path['ds']):
            charge();qmax=max(values[i:i+2]);a=(values[i+1]-values[i])/(2*ds);lat=[c*qmax*segment[i] for c in coeff];long=([0.,0.]+[mass*max(a,0)/2]*2) if a>=0 else [mass*abs(a)/4]*4;peak=max(peak,max(math.hypot(x,y)/z for x,y,z in zip(lat,long,mu)))
    if peak>.9990000001:raise ValueError('NOMINAL_PROFILE_BOUND_VALIDATION')
    high=dict(path,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=it+1)
    lowq=[min(q[i],80.**2,interpolate_squared(oldbackup,s,False)) for i,s in enumerate(sigma)];lowl=[min(launch[i],80.**2,interpolate_squared(oldbackup,s,True)) for i,s in enumerate([*sigma,oldbackup['length']])]
    return high,dict(path,periodic_squared=lowq,launch_squared=lowl),dict(nominal_peak_wheel_force_ratio=peak,cap90=True,backup_cap80=True,old_observed_curvature_used=False)

"""Exact sampled outer-box clearance to saved road union/edges and circles.

No native objects, force calls, integration, or road-normal distance surrogate.
"""
import numpy as np
from retry.line530_design import HALF_WIDTH,HALF_LENGTH,SHIFT
FRACTIONS=np.linspace(0.,1.,33)
TARGET=1.252  #1.25nominal plus.002numericalbuffer, nevera relaxedmargin.
KMAX=np.tan(.4)/3.24


def point_segment_distance(x,a,b):
    v=b-a;t=np.clip(((x-a)*v).sum(axis=-1)/np.maximum((v*v).sum(axis=-1),1e-20),0,1)
    return np.linalg.norm(x-a-t[...,None]*v,axis=-1)


class Geometry:
    def __init__(self,static,center):
        self.center=np.asarray(center);self.obstacles=static['obstacles'];self.edges=np.asarray(static['boundary']);self.roads=np.asarray([r[0] for r in static['roads']]);self.n=len(center);self.fractions=FRACTIONS;self.sample_cap=30000000
        midpoint=(self.center+np.roll(self.center,-1,axis=0))/2
        def nearby(items):
            lower=items.min(axis=1);upper=items.max(axis=1);ids=[]
            for pos in midpoint:
                distance=np.linalg.norm(np.maximum(np.maximum(lower-pos,pos-upper),0),axis=1);selected=np.where(distance<=12.)[0]
                if not len(selected):raise ValueError('EMPTY_LOCAL_GEOMETRY')
                ids.append(selected)
            count=max(map(len,ids));return np.array([np.pad(x,(0,count-len(x)),mode='edge') for x in ids])
        self.edge_ids=nearby(self.edges);self.road_ids=nearby(self.roads);self.calls=0;self.segment_samples=0

    def evaluate(self,points,segments=None,details=False):
        self.calls+=1;p=np.asarray(points);ids=np.arange(self.n) if segments is None else np.asarray(segments);v=p[(ids+1)%self.n]-p[ids];ds=np.linalg.norm(v,axis=1);t=v/ds[:,None];normal=np.c_[-t[:,1],t[:,0]]
        S=len(ids);F=len(self.fractions)
        if self.segment_samples+S*F>self.sample_cap:raise RuntimeError('GEOMETRY_SAMPLE_CAP')
        pos=p[ids,None,:]+self.fractions[None,:,None]*v[:,None,:]+SHIFT*t[:,None,:];self.segment_samples+=S*F
        poly=np.array([pos+a*HALF_LENGTH*t[:,None,:]+b*HALF_WIDTH*normal[:,None,:] for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]).transpose(1,2,0,3)
        edges=self.edges[self.edge_ids[ids]];ea=edges[:,:,0,:];eb=edges[:,:,1,:];aa=ea[:,None,:,:]-pos[:,:,None,:];bb=eb[:,None,:,:]-pos[:,:,None,:]
        ax=np.stack([(aa*t[:,None,None,:]).sum(-1),(aa*normal[:,None,None,:]).sum(-1)],axis=-1);bx=np.stack([(bb*t[:,None,None,:]).sum(-1),(bb*normal[:,None,None,:]).sum(-1)],axis=-1);half=np.array([HALF_LENGTH,HALF_WIDTH]);endpoint=np.minimum(np.linalg.norm(np.maximum(abs(ax)-half,0),axis=-1),np.linalg.norm(np.maximum(abs(bx)-half,0),axis=-1))
        cornerdist=point_segment_distance(poly[:,:,:,None,:],ea[:,None,None,:,:],eb[:,None,None,:,:]);distance=np.minimum(endpoint.min(axis=-1),cornerdist.min(axis=(-1,-2)))
        direction=bx-ax;lo=np.zeros(ax.shape[:-1]);hi=np.ones(ax.shape[:-1]);valid=np.ones(ax.shape[:-1],bool)
        for j,h in enumerate(half):
            parallel=abs(direction[...,j])<1e-14;valid &= ~parallel | (abs(ax[...,j])<=h);den=np.where(parallel,1.,direction[...,j]);z1=(-h-ax[...,j])/den;z2=(h-ax[...,j])/den
            lo=np.maximum(lo,np.where(parallel,-np.inf,np.minimum(z1,z2)));hi=np.minimum(hi,np.where(parallel,np.inf,np.maximum(z1,z2)))
        intersects=np.any(valid & (lo<=hi),axis=-1);distance=np.where(intersects,0.,distance)
        roads=self.roads[self.road_ids[ids]];edge=np.roll(roads,-1,axis=2)-roads;dv=poly[:,:,:,None,None,:]-roads[:,None,None,:,:,:];cross=edge[:,None,None,:,:,0]*dv[...,1]-edge[:,None,None,:,:,1]*dv[...,0];covered=np.any(np.all(cross>=-1e-8,axis=-1)|np.all(cross<=1e-8,axis=-1),axis=-1);inside=np.all(covered,axis=-1)
        # Signed outside-corner clearance supplies a restoration direction.
        outside_depth=np.max(np.where(~covered,cornerdist.min(axis=-1),0.),axis=-1);road=np.where(inside,distance,-outside_depth);margins=[road.min(axis=1)]
        obs_rows=[]
        for obstacle,radius in self.obstacles:
            delta=np.asarray(obstacle)-pos;xy=np.stack([abs((delta*t[:,None,:]).sum(-1))-HALF_LENGTH,abs((delta*normal[:,None,:]).sum(-1))-HALF_WIDTH],axis=-1);gap=np.linalg.norm(np.maximum(xy,0),axis=-1)+np.minimum(np.max(xy,axis=-1),0)-radius;margins.append(gap.min(axis=1));obs_rows.append(gap)
        result=np.stack(margins,axis=1)
        if not details:return result
        return result,dict(samples=S*F,min_road_margin_m=float(road.min()),min_obstacle_margin_m=float(min(x.min() for x in obs_rows)),minimum_outer_rectangle_margin_m=float(result.min()),outside_samples=int((~inside).sum()),intersecting_samples=int(intersects.sum()),max_sample_spacing_m=float(ds.max()/(len(self.fractions)-1)),road_filter_radius_m=12.,max_local_edges=self.edge_ids.shape[1],max_local_road_polys=self.road_ids.shape[1])


def shape(points):
    p=np.asarray(points);v=np.roll(p,-1,axis=0)-p;ds=np.linalg.norm(v,axis=1);u=np.roll(v,1,axis=0);k=np.arctan2(u[:,0]*v[:,1]-u[:,1]*v[:,0],(u*v).sum(axis=1))/((ds+np.roll(ds,1))/2)
    return ds,k


def geometric_constraints(geo,points):
    ds,k=shape(points)
    return np.r_[(geo.evaluate(points)-TARGET).ravel(),ds-2.,(KMAX-abs(k))*3.24**2]

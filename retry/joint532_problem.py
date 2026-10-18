"""Explicit path, periodic speed-square and launch speed-square NLP.

No friction-force calls or physics integration. All deployed profiles still
come from the unchanged528 generator, never from these design variables.
"""
import numpy as np
from scipy.sparse import csr_matrix
from retry.feasible531_geometry import Geometry,geometric_constraints,shape
from retry.line530_design import frames
from retry.line530_control import rebuild,scalar_clock
from retry.envelope500 import MASS,REAR
Q=6400.
EPS=1e-5


class Problem:
    def __init__(self,static,restored_points,guard=lambda:None):
        self.static=static;self.center=np.array([(p[2],p[3]) for p in static['track']]);self.normal=frames(self.center)[1];self.initial_points=np.array(restored_points);self.offset=((self.initial_points-self.center)*self.normal).sum(axis=1);n=self.n=len(self.center);arcs=np.r_[0,np.cumsum(np.linalg.norm(np.roll(self.center,-1,axis=0)-self.center,axis=1))];self.frozen=(arcs[:-1]<20)|(arcs[-1]-arcs[:-1]<20);self.free=np.where(~self.frozen)[0];self.k=len(self.free);self.size=self.k+2*n;self.guard=guard;self.geo=Geometry(static,self.center);self.A=.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass'];p=rebuild(self.initial_points,static);self.time_scale=scalar_clock(p);self.initial_profile=p;self.x0=np.r_[self.offset[self.free]/4,np.array(p['periodic_squared'])/Q,np.array(p['launch_squared'][1:])/Q];self.lower=np.r_[np.full(self.k,-1.),np.full(2*n,1e-8)];self.upper=np.ones(self.size);self.geometry_cache={};self.derivative_cache={};self.cost=dict(objective=0,gradient=0,constraints=0,jacobians=0,geometry_jacobians=0)

    def points(self,x):
        offset=self.offset.copy();offset[self.free]=4*x[:self.k]
        return self.center+offset[:,None]*self.normal

    def state(self,x):
        key=x[:self.k].tobytes()
        if self.geometry_cache.get('key')!=key:
            p=self.points(x);ds,kappa=shape(p);self.geometry_cache=dict(key=key,points=p,ds=ds,kappa=kappa,geometry=geometric_constraints(self.geo,p))
        d=self.geometry_cache;return d,x[self.k:self.k+self.n],np.r_[0.,x[self.k+self.n:]]

    def objective(self,x):
        self.guard();self.cost['objective']+=1
        if self.cost['objective']>4000:raise RuntimeError('OBJECTIVE_CAP')
        d,q,w=self.state(x);root=np.sqrt(np.maximum(w,1e-12));return float(np.sum(2*d['ds']/(80*(root[:-1]+root[1:])))/self.time_scale)

    def gradient(self,x):
        self.guard();self.cost['gradient']+=1;d,q,w=self.state(x);root=np.sqrt(np.maximum(w,1e-12));den=root[:-1]+root[1:];v=np.roll(d['points'],-1,axis=0)-d['points'];t=v/d['ds'][:,None];co=2/(80*self.time_scale*den);node_gradient=np.roll(co[:,None]*t,1,axis=0)-co[:,None]*t;out=np.zeros(self.size);out[:self.k]=4*(node_gradient*self.normal).sum(axis=1)[self.free];z=-d['ds']/(80*self.time_scale*den**2)
        out[self.k+self.n:]+=z/np.maximum(root[1:],1e-6)
        out[self.k+self.n:self.k+2*self.n-1]+=z[1:]/np.maximum(root[1:-1],1e-6)
        return out

    @staticmethod
    def power(q):
        root=np.sqrt(np.maximum(q,1e-12));return 80000/(MASS*(80*root+2.7))

    @staticmethod
    def power_derivative(q):
        root=np.sqrt(np.maximum(q,1e-12));return np.where(q>1e-12,-80000/MASS*40/(root*(80*root+2.7)**2),0.)

    def speed_constraints(self,d,q,w):
        ds=d['ds'];kap=d['kappa'];qn=np.roll(q,-1);wc=w[:-1];wn=w[1:]
        return np.r_[1-Q*q*kap/self.A,1+Q*q*kap/self.A,q-qn+2*REAR*ds/Q,q-qn+2*self.power(q)*ds/Q,qn-q+160*ds/Q,qn-wn,wc-wn+2*REAR*ds/Q,wc-wn+2*self.power(wc)*ds/Q,wn-wc+160*ds/Q]

    def constraints(self,x):
        self.guard();self.cost['constraints']+=1
        if self.cost['constraints']>4000:raise RuntimeError('CONSTRAINT_CAP')
        d,q,w=self.state(x);return np.r_[d['geometry'],self.speed_constraints(d,q,w)]

    def geometry_derivatives(self,x):
        d,q,w=self.state(x);key=d['key']
        if self.derivative_cache.get('key')==key:return self.derivative_cache
        self.cost['geometry_jacobians']+=1
        if self.cost['geometry_jacobians']>170:raise RuntimeError('GEOMETRY_JACOBIAN_CAP')
        n=self.n;k=self.k;J=np.zeros((9*n,k));D=np.zeros((n,k));K=np.zeros((n,k));base=d['geometry'];p=d['points']
        for col,j in enumerate(self.free):
            if col%16==0:self.guard()
            changed=p.copy();changed[j]+=EPS*self.normal[j];ids=np.array([(j-1)%n,j]);rows=(ids[:,None]*7+np.arange(7)).ravel();J[rows,col]=4*((self.geo.evaluate(changed,ids)-1.252).ravel()-base[rows])/EPS
            ds,kap=shape(changed);di=np.array([(j-1)%n,j]);ki=np.array([(j-1)%n,j,(j+1)%n]);D[di,col]=4*(ds[di]-d['ds'][di])/EPS;K[ki,col]=4*(kap[ki]-d['kappa'][ki])/EPS;J[7*n+di,col]=D[di,col];J[8*n+ki,col]=4*((np.tan(.4)/3.24-abs(kap[ki]))*3.24**2-base[8*n+ki])/EPS
        self.derivative_cache=dict(key=key,G=J,D=D,K=K);return self.derivative_cache

    def jacobian(self,x):
        self.guard();self.cost['jacobians']+=1;d,q,w=self.state(x);der=self.geometry_derivatives(x);n=self.n;k=self.k;J=np.zeros((18*n,self.size));J[:9*n,:k]=der['G'];ds=d['ds'];kap=d['kappa'];D=der['D'];K=der['K'];base=9*n;idx=np.arange(n);qi=k+idx;qn=k+(idx+1)%n;wn=k+n+idx;wc=k+n+idx-1
        J[base:base+n,:k]=-Q*q[:,None]*K/self.A;J[base+n:base+2*n,:k]=Q*q[:,None]*K/self.A;J[base+idx,qi]=-Q*kap/self.A;J[base+n+idx,qi]=Q*kap/self.A
        for group,acc in [(2,np.full(n,REAR)),(3,self.power(q)),(4,np.full(n,80.)),(6,np.full(n,REAR)),(7,self.power(w[:-1])),(8,np.full(n,80.))]:J[base+group*n:base+(group+1)*n,:k]=2*acc[:,None]*D/Q
        for group in (2,3):J[base+group*n+idx,qi]=1.;J[base+group*n+idx,qn]=-1.
        J[base+3*n+idx,qi]+=2*ds*self.power_derivative(q)/Q
        J[base+4*n+idx,qi]=-1.;J[base+4*n+idx,qn]=1.;J[base+5*n+idx,qn]=1.;J[base+5*n+idx,wn]=-1.
        for group in (6,7):J[base+group*n+idx,wn]=-1.;J[base+group*n+idx[1:],wc[1:]]=1.
        J[base+7*n+idx[1:],wc[1:]]+=2*ds[1:]*self.power_derivative(w[1:-1])/Q
        J[base+8*n+idx,wn]=1.;J[base+8*n+idx[1:],wc[1:]]=-1.
        return csr_matrix(J)

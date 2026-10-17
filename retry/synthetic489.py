"""Handmade synthetic gate only. Called inside the single timed489 worker."""
from fractions import Fraction
import time
import numpy as np
from retry import lattice489 as p
from retry import audit489 as a
from retry.quota489 import Quota,QuotaStop

def run(charge):
    tests=[]
    roads=[]
    for i in range(8):
        angle=i*np.pi/4;radial=np.array([np.cos(angle),np.sin(angle)]);tangent=np.array([-radial[1],radial[0]])
        quad=[20*radial+x*tangent+y*radial for x,y in [(-5,-2),(5,-2),(5,2),(-5,2)]]
        roads.append(dict(idx=i,fixture=dict(geometry=dict(vertices=np.array(quad).tolist()))))
    snapshot=dict(roads=roads,obstacles=[dict(body=dict(position=[100.+i,100.]),fixture=dict(radius=.1)) for i in range(6)])
    charge('producer_node_checks',8);charge('independent_audit_node_checks',8)
    for x,y in zip(p.source_geometry(snapshot),a.reconstruct(snapshot)):assert np.array_equal(x,y)
    tests+=['independent_source_geometry_and_arc']
    def equal_edge(P,Q,obs,r):
        charge('producer_edge_checks',len(P)*len(Q));charge('independent_audit_edge_checks',len(P)*len(Q))
        x,m=p.edge(P,Q,obs,r);y,n=a.edges(P,Q,obs,r)
        assert np.array_equal(x,y) and np.array_equal(m,n)
        for i,v in enumerate(P):
            for j,w in enumerate(Q):
                delta=w-v
                numerator=np.sum((obs-v)*delta,axis=1)
                denominator=max(np.sum(delta*delta),1e-9)
                f=np.clip(numerator/denominator,0,1)
                clear=np.linalg.norm(v+f[:,None]*delta-obs,axis=1)-(r+2.9+.25)
                assert m[i,j]==clear.min()
        return x,m
    def equal_triple(P,Q,R):
        count=len(P)*len(Q)*len(R)
        charge('producer_triple_checks',count);charge('independent_audit_triple_checks',count)
        x=p.triple(P,Q,R);y=a.triples(P,Q,R,p.TARGET);assert np.array_equal(x,y)
        # Independently apply the original scalar algebra at every triple.
        for i,v in enumerate(P):
            for j,w in enumerate(Q):
                for k,z in enumerate(R):
                    u=w-v;b=z-w;c=u+b
                    curvature=2*(u[0]*b[1]-u[1]*b[0])/max(np.linalg.norm(u)*np.linalg.norm(b)*np.linalg.norm(c),1e-9)
                    assert x[i,j,k]==(abs(curvature)<=p.TARGET and float(u@b)>0)
        return x
    obs=np.array([[0.,0.]]);rad=np.array([.1])
    P=np.array([[-4.,0.],[-4.,4.],[-4.,-4.]])
    Q=np.array([[4.,0.],[4.,4.],[4.,-4.]])
    valid,margin=equal_edge(P,Q,obs,rad)
    assert margin[0,0]<0 and valid[1,1] and valid[2,2]
    assert np.linalg.norm(P[0])>3.15 and np.linalg.norm(Q[0])>3.15
    tests+=['interior_segment_collision','both_bypass_signs']
    tri=equal_triple(np.array([[-2.,0.],[0.,-2.],[2.,0.]]),np.array([[0.,0.]]),np.array([[2.,0.],[0.,2.]]))
    assert tri[0,0,0] and not tri[1,0,0] and not tri[2,0,0]
    tests+=['incoming_pair_curvature','collinear_reversal_dot']
    # Exercise full21-rank broadcast shape and all6 obstacles before map use.
    ys=np.linspace(-4.5,4.5,21)
    left=np.c_[np.full(21,-10.),ys];mid=np.c_[np.zeros(21),ys];right=np.c_[np.full(21,10.),ys]
    obstacles=np.c_[np.arange(6.)+50.,np.full(6,50.)];radii=np.full(6,.2)
    charge('producer_edge_checks',21**2);charge('independent_audit_edge_checks',21**2)
    charge('producer_triple_checks',21**3);charge('independent_audit_triple_checks',21**3)
    before=time.process_time()
    ve,me=p.edge(left,mid,obstacles,radii);va,ma=a.edges(left,mid,obstacles,radii)
    vt=p.triple(left,mid,right);at=a.triples(left,mid,right,p.TARGET)
    vectorized_layer_CPU_s=time.process_time()-before
    assert np.array_equal(ve,va) and np.array_equal(me,ma) and np.array_equal(vt,at)
    tests+=['full21_rank_six_obstacle_broadcast']
    s=np.array([0.,5.,15.,25.,30.]);L=40.;center=np.c_[s,np.zeros(len(s))]
    points=np.repeat(center[:,None,:],3,axis=1);points[:,1,1]+=.01;points[:,2,1]+=5.
    charge('producer_node_checks',points.shape[0]*points.shape[1]);charge('independent_audit_node_checks',points.shape[0]*points.shape[1])
    x=p.tube(center,points,s,L);y=a.tube_eligible(center,points,s,L,p.B);assert np.array_equal(x,y)
    assert x[0].tolist()==[True,False,False] and x[1].tolist()==[True,False,False] and x[-1].tolist()==[True,False,False]
    assert x[2,1] and not x[2,2]
    assert p.taper(Fraction(15),Fraction(40))==p.taper(Fraction(25),Fraction(40))==1
    tests+=['taper_incident_min_and_midpoint_fold','closed_taper_boundary','exact_serialized_displacement']
    assert Fraction.from_float(1.)-Fraction.from_float(float(2**54))!=Fraction.from_float(1.-float(2**54))
    center=np.array([[-0.,0.],[1.,0.],[2.,0.],[3.,0.]])
    charge('producer_node_checks',4*21);charge('independent_audit_node_checks',4*21)
    normal=np.tile([0.,1.],(4,1));qs,nodes,dedup=p.points(center,normal,np.arange(4.),4.,np.ones(4))
    assert len(qs)==21 and (qs>0).sum()==10 and (qs<0).sum()==10
    for i in [0,1,3]:assert nodes[i,0].tobytes()==center[i].tobytes() and dedup[i].sum()==1
    tests+=['signed_zero_exact_copy_and_dedup','canonical_offset_ranks']
    reachable=np.ones((2,2),bool);triple=np.ones((2,2,2),bool);edge=np.ones((2,2),bool)
    reached,parent=p.advance(reachable,triple,edge);assert reached.all() and not parent.any()
    assert p.choose(reached,edge,triple,triple)==(0,0)
    triple_root=triple.copy();triple_root[:,0,0]=False
    assert p.choose(reached,edge,triple,triple_root) is None
    triple_last=triple.copy();triple_last[:,:,0]=False
    assert p.choose(reached,edge,triple_last,triple) is None
    edge_last=edge.copy();edge_last[:,0]=False
    assert p.choose(reached,edge_last,triple,triple) is None
    tests+=['minimum_predecessor_and_terminal_ties','root_last_and_closing_edge_required']
    # Pair merging deliberately omits nonlocal compatibility history.
    charge('max_nonadjacent_segment_pairs',6)
    assert p.compatibility(np.array([[0.,0.],[4.,4.],[0.,4.],[4.,0.]]))['nonadjacent_intersections']
    tests+=['nonlocal_compatibility_separate']
    q=Quota.__new__(Quota)
    q._validate({})
    for rows in ({str(i):(1,'x',False) for i in range(39)}, {'a':(2*1024**2+1,'x',False)}, {'result.json':(65537,'x',True)}):
        try:q._validate(rows)
        except QuotaStop:pass
        else:raise AssertionError('quota boundary accepted')
    tests+=['file_perfile_termination_reservation']
    return dict(passed=True,tests=tests,test_count=len(tests),map_read=False,map_searches=0,representative_vectorized_layer_CPU_s=vectorized_layer_CPU_s,representative_321_layers_CPU_s=321*vectorized_layer_CPU_s,projection_excludes_rational_DP_IO_and_is_not_completion_guarantee=True)

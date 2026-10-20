"""A past observed node supports derivatives, never current road/output."""
from pathlib import Path
import json,math,sys,time
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
import runtime598 as core


def profile(points,curvature):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    q=np.minimum(80.**2,100./np.maximum(curvature,1e-6));q[-1]=0.
    for i in range(len(q)-2,-1,-1):q[i]=min(q[i],q[i+1]+90*(arc[i+1]-arc[i]))
    return dict(points=points.tolist(),arcs=arc.tolist(),ds=np.diff(arc).tolist(),length=float(arc[-1]),
        launch_squared=q.tolist(),periodic_squared=q[:-1].tolist(),observed_open=True)


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    turns=np.array([.04,.25,.30,.30,.29,.26,.20,.10])
    heading=np.r_[0.,np.cumsum(turns)]
    base=np.vstack(([0.,0.],np.cumsum(3.5*np.c_[np.sin(heading),np.cos(heading)],axis=0)))
    assert max(turns)<=.31
    image=np.full((84,84),104./255.,np.float32);blocked=np.zeros((84,84),bool);opaque=blocked.copy()
    cases=[]
    for angle in (-.8,0.,.7,2.7):
        r=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
        translation=np.array([1.,8.]);previous=base@r.T+translation;dense=previous[1:]
        current,info=a.observed_reference_lattice(dense,previous)
        assert info['reference_lattice_correspondence']
        assert np.max(np.linalg.norm(current-dense,axis=1))<1e-10
        past,used=a.observed_reference_derivative_support(current,previous,info,image,blocked,opaque)
        assert past is not None and used['reference_past_derivative_support_used']
        assert np.max(abs(past-previous[0]))<1e-10
        for object_present in (False,True):
            normal=np.array([math.cos(heading[-3]),-math.sin(heading[-3])])
            object_center=(base[-3]+normal)@r.T+translation
            objects=[(object_center,1.6)] if object_present else []
            full,fk=a.deform_reference_with_derivative_support(previous,previous,3.5*np.arange(len(previous)),objects)
            before=current.copy()
            cropped,ck=a.deform_reference_with_derivative_support(current,dense,3.5*np.arange(len(current)),objects,past)
            assert np.array_equal(current,before)
            field_error=float(np.max(np.linalg.norm(cropped-full[1:],axis=1)))
            curvature_error=float(np.max(abs(ck-fk[1:])))
            assert field_error<1e-10 and curvature_error<1e-10,(angle,object_present,field_error,curvature_error)
            assert len(cropped)==len(current) and np.linalg.norm(cropped[-1]-full[-1])<1e-10
            oldpath=profile(full,fk);newpath=profile(cropped,ck)
            center=.5*(full[1]+full[2]);velocity=45*(full[2]-full[1])/np.linalg.norm(full[2]-full[1])
            root=SimpleNamespace(center=tuple(center),planar=SimpleNamespace(angle=angle,linear=SimpleNamespace(velocity=tuple(velocity))))
            old_s=core.project(root.center,oldpath)['s'];new_s=core.project(root.center,newpath)['s']
            old_ref=core.reference(old_s,oldpath);new_ref=core.reference(new_s,newpath)
            assert max(abs(np.array(old_ref)-new_ref))<1e-9
            assert max(abs(core.nominal(root,oldpath,old_s)-core.nominal(root,newpath,new_s)))<1e-7
            cases.append(dict(angle_rad=angle,object_present=object_present,object_field_error_m=field_error,
                curvature_error_per_m=curvature_error,reference_error=float(max(abs(np.array(old_ref)-new_ref)))))
    # Isolated public coordinates for negative and exact last-visible-row tests.
    previous=base.copy();current,info=a.observed_reference_lattice(base[1:],previous)
    def check(name,previous=previous,gate=info,img=image,obstacles=blocked,cover=opaque):
        past,reason=a.observed_reference_derivative_support(current,previous,gate,img,obstacles,cover)
        assert past is None,(name,reason);return dict(case=name,reason=reason['reference_past_derivative_support_reason'])
    negatives=[check('reset',previous=[]),check('unaccepted_phase',gate=dict(info,reference_lattice_correspondence=False)),
        check('too_few_matches',gate=dict(info,reference_lattice_matches=2))]
    distant=previous.copy();distant[0]-=[0.,20.];negatives.append(check('too_far_past',previous=distant))
    opposite=previous[::-1].copy();negatives.append(check('opposite_direction',previous=opposite))
    # Two opposite near branches remain ambiguous even if a caller supplies
    # otherwise accepted lattice metadata.
    ambiguous=np.array([[0.,0.],[0.,3.5],[0.,7.],[.2,7.],[.2,3.5],[.2,0.]])
    ambcurrent=np.array([[.1,3.5],[.1,5.],[.1,6.5]])
    past,reason=a.observed_reference_derivative_support(ambcurrent,ambiguous,info,image,blocked,opaque)
    assert past is None;negatives.append(dict(case='ambiguous_branch',reason=reason['reference_past_derivative_support_reason']))
    px=int(round(a.IMAGE_ORIGIN_X));py=int(round(a.IMAGE_ORIGIN_Y))
    grass=image.copy();grass[py-1:py+2,px-1:px+2]=.66
    negatives.append(check('visible_grass',img=grass))
    obstacle=blocked.copy();obstacle[py-1:py+2,px-1:px+2]=True
    negatives.append(check('visible_obstacle',obstacles=obstacle))
    cover=opaque.copy();cover[py-1:py+2,px-1:px+2]=True
    past,used=a.observed_reference_derivative_support(current,previous,info,grass,blocked,cover)
    assert past is not None and used['reference_past_derivative_current_hidden']
    assert not used['reference_past_derivative_is_current_road_evidence']
    # Pixel row69 is still visible, and current negative evidence vetoes it.
    row69_y=(a.IMAGE_ORIGIN_Y-69.)/1.701
    shift=np.array([0.,row69_y]);prior69=previous+shift;curr69=current+shift
    for material in ('grass','blocked'):
        img=image.copy();veto=blocked.copy()
        if material=='grass':img[69,:]=.66
        else:veto[69,:]=True
        past,reason=a.observed_reference_derivative_support(curr69,prior69,info,img,veto,opaque)
        assert past is None,(material,reason)
        negatives.append(dict(case='row69_'+material,reason=reason['reference_past_derivative_support_reason']))
    result=dict(status='PASS',cases=cases,negatives=negatives,opaque_past_not_current_road=True,
        output_node_count_and_terminal_unchanged=True,original_formula_and_coefficients=True,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        scope='Public synthetic3.5m grid, node turn<=.31, rigid transforms and current object field. No model rollout or safety claim.')
    assert result['CPU_s']<60.;out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()

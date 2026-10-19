"""Small analytic counterexamples for an observed convex-patch union."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
import runtime598 as c


def rect(x0,x1,y0,y1):return (((x0,y0),(x1,y0),(x1,y1),(x0,y1)),1.)
def signed(poly,roads,edges,obstacles=()):
    covered=all(any(c.inside(p,r) for r,_ in roads) for p in poly)
    distance=min(c.polygon_distance(poly,e) for e in edges)
    return min(distance if covered else -distance,c.obstacle_margin([poly],obstacles))

def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    rectangle=[rect(-10,10,-10,10)]
    overlap=[rect(-10,2,-10,10),rect(-2,10,-10,10)]
    concave=[rect(-10,10,-10,0),rect(-10,0,0,10)]
    branch=[rect(-10,-2,-10,10),rect(2,10,-10,10),rect(-10,10,2,10)]
    cases=[('rectangle',rectangle,rectangle),('overlapping_rectangle',overlap,rectangle),
           ('duplicate_rectangle',rectangle+rectangle,rectangle),('concave',concave,concave),
           ('branch_merge',branch,branch),
           ('disjoint_observation_gap',[rect(-10,-2,-10,10),rect(2,10,-10,10)],
            [rect(-10,-2,-10,10),rect(2,10,-10,10)])]
    from retry.union_geometry_check import exposed
    for name,roads,truth in cases:
        boundary=a.road_union_boundary(roads);assert exposed(roads,boundary),name
        # Independent analytic perimeter, without the union implementation.
        if name in ('rectangle','overlapping_rectangle','duplicate_rectangle'):
            perimeter=[((-10,-10),(10,-10)),((10,-10),(10,10)),((10,10),(-10,10)),((-10,10),(-10,-10))]
        elif name=='concave':
            vertices=[(-10,-10),(10,-10),(10,0),(0,0),(0,10),(-10,10)]
            perimeter=list(zip(vertices,vertices[1:]+vertices[:1]))
        elif name=='branch_merge':
            vertices=[(-10,-10),(-2,-10),(-2,2),(2,2),(2,-10),(10,-10),(10,10),(-10,10)]
            perimeter=list(zip(vertices,vertices[1:]+vertices[:1]))
        else:
            perimeter=[(p,q) for poly,_ in truth for p,q in zip(poly,poly[1:]+poly[:1])]
        count=0
        for x,y in [(-5.,-5.),(-5.,5.),(0.,-5.),(0.,5.),(5.,5.),(12.,0.)]:
            poly=rect(x-.25,x+.25,y-.25,y+.25)[0]
            for obstacles in [(),(((x+1.,y),.5),)]:
                got=signed(poly,roads,boundary,obstacles);expected=signed(poly,truth,perimeter,obstacles)
                assert abs(got-expected)<1e-10,(name,x,y,got,expected)
                count+=1
        # Full vehicle callback: exactly the original vertex-cover sign,
        # scalar polygon distances and obstacle minimum, including holes.
        scene=c.Scene(roads,boundary,[]);observer=a.Agent();root=observer._root(scene,0.)
        for x,y in [(-5.,-5.),(-5.,5.),(0.,-5.),(0.,5.),(5.,5.),(12.,0.)]:
            root=c.replace(root,center=(x,y));expected=min(signed(poly,truth,perimeter) for poly in c.polygons(root))
            assert abs(scene.margin(root)-expected)<1e-10
        records.append(dict(name=name,analytic_polygon_checks=count,callback_checks=6,all_edges_exposed=True))
    result=dict(status='PASS',records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()

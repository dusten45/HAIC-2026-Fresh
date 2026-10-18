"""Source polygon masses, spin inertia and COM force units; no world/integrator."""
import hashlib,json,math,time
from pathlib import Path
from dataclasses import replace
from core.vendor.car_dynamics import HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4,SIZE,WHEEL_R,WHEEL_W,WHEEL_MOMENT_OF_INERTIA,ENGINE_POWER,FRICTION_LIMIT
from retry.envelope500 import MASS
from retry.plan513_model import load_root
from retry.brake502_response import wheel_response
from retry.capacity522_control import lateral_budget
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response522-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/capacity522_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());root=load_root(static['root']);m=root.planar.linear.mass;I=WHEEL_MOMENT_OF_INERTIA;R=WHEEL_R*SIZE
    def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))*SIZE**2/2
    hull=sum(area(poly) for poly in (HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4));wheel=4*WHEEL_W*WHEEL_R*SIZE**2*.1
    analytic=hull+4*wheel;rolling_spin_mass=4*I/R**2;effective=m+rolling_spin_mass
    assert abs(analytic-m)<1e-6 and abs(effective-MASS)<1e-12
    assert I==1.6 and R==.54 and ENGINE_POWER==40000. and FRICTION_LIMIT==400.
    # Pure source force operation: aligned wheels, rolling longitudinally,
    # 1m/s side velocity. Spin inertia does not enter lateral COM F/m.
    rows=[]
    for w in root.planar.linear.wheels:
        w=replace(w,omega=60./R,gas=0.,heading=0.,offset=(0.,0.),friction=400.)
        after,force,extra=wheel_response(w,(1.,60.),0.,0.)
        assert abs(force[0]+82.)<1e-10 and abs(force[1])<1e-10 and abs(after.omega-w.omega)<1e-10
        rows.append(force)
    sumforce=sum(v[0] for v in rows);acceleration=sumforce/m;wrong=sumforce/effective
    out=dict(unit_check_pass=True,analytic_hull_fixture_mass_kg=hull,analytic_each_wheel_body_mass_kg=wheel,analytic_body_mass_sum_kg=analytic,saved_actual_assembly_mass_kg=m,body_mass_roundoff_kg=analytic-m,separate_wheel_spin_inertia_kg_m2=I,rolling_radius_m=R,longitudinal_ideal_rolling_spin_equivalent_mass_kg=rolling_spin_mass,longitudinal_ideal_rolling_effective_mass_kg=effective,steady_convention_mass_kg=MASS,steady_mass_difference=effective-MASS,saved_planar_yaw_inertia_kg_m2=root.planar.inertia,saved_wheel_body_yaw_inertias_kg_m2=list(root.planar.wheel_inertias),current_wheel_friction_limits_N=[w.friction for w in root.planar.linear.wheels],sum_current_friction_limits_N=sum(w.friction for w in root.planar.linear.wheels),candidate_lateral_budget_m_s2=lateral_budget(static),lateral_source_force_fixture=dict(velocity_m_s=[1.,60.],sum_lateral_force_N=sumforce,COM_acceleration_m_s2=acceleration,incorrect_isotropic_rolling_mass_acceleration_m_s2=wrong),source_force_evaluations=4,model_integrator_ticks=0,native_worlds=0,native_actions=0,native_resets=0,explanation='Body translation uses sum external tyre forces / actual assembly mass.29.24979=7.30192+4*1.6/.54^2 is an ideal straight rolling longitudinal energy/torque convention; it is not isotropic actual mass. Wheel omega spin inertia1.6 is separate from planar body/yaw inertias. In a turn rolling constraints/steering/yaw/finite slip couple directions; Ftotal/m is only a loose COM force-norm bound, not achievable lateral acceleration.70% is arbitrary fixed reserve requiring dynamic falsification, not calibration or optimum.',units='Source-consistent world m,s,kg: tyre forces from82*(velocity slip), F/m gives m/s^2, spin torque uses I=1.6kgm^2, engine40000 is source power constant divided by |omega|+5. Stylized model; no real-vehicle accuracy claim.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<10 and out['wall_s']<15
    with (G/'retry/capacity522_units.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()

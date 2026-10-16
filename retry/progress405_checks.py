"""Pure algebraic design contrasts, not vehicle/model/candidate-control evaluation."""
import datetime,json,sys,time
from pathlib import Path

def run(root):
 d=root/'stage405';assert not(d/'design-checks.json').exists();p=d/'design-check-plan.json';p.write_text(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Syntheticprogresssequencesonly,notvehicleforecasts. Verifyfixedpositivegoalrejectsstasis,signeddeficitdistinguishespostgoalprogresswhereclippeddeficitties,andfixedslotreplacementdoesnotgrowK.',H=13,dt=.08,goal=3.24,new_native_actor_model_learning_SEALED=0),indent=2)+'\n');p.chmod(0o600);start,cpu=time.perf_counter(),time.process_time();H=13;dt=.08;g=3.24
 stationary=[0.]*H;early=[g*min(k/8,1) for k in range(1,H+1)];delayed=[g*max((k-3)/10,0) for k in range(1,H+1)];plateau=[g*min(k/4,1) for k in range(1,H+1)];continuing=[g*k/4 for k in range(1,H+1)]
 signed=lambda seq:sum((g-s)*dt for s in seq);clipped=lambda seq:sum(max(g-s,0)*dt for s in seq)
 assert stationary[-1]<g and early[-1]>=g and delayed[-1]>=g and signed(early)<signed(delayed)
 assert clipped(plateau)==clipped(continuing) and signed(continuing)<signed(plateau)
 slots=list(range(6));slots[5]='retained_model_suffix';assert len(slots)==6
 x=dict(stationary_fails_positive_goal=True,earlier_progress_preferred_to_delayed=True,clipped_plateau_tie=True,signed_continuing_progress_preferred=True,slot_count_remains6=True,values=dict(early_signed=signed(early),delayed_signed=signed(delayed),plateau_clipped=clipped(plateau),continuing_clipped=clipped(continuing),plateau_signed=signed(plateau),continuing_signed=signed(continuing)),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,new_native_actor_model_learning_SEALED=0,scope='Algebraonly,no feasibility/safety/actualbehaviorclaim.')
 p=d/'design-checks.json';p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');p.chmod(0o600);print(json.dumps(x,ensure_ascii=False))
if __name__=='__main__':run(Path(sys.argv[1]))

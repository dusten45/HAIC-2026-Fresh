"""Repair only288 endpointarc; missingstored candidates require twoactualTRAIN runs."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage289';assert not D.exists();D.mkdir(mode=0o700);p=read(R/'stage288/plan.json');p.update(stage=289,research_available=29045,candidate='288unchangedsourceGT/corridor/path/H/search/pedals/tie; replace monotonefrontier projection withconnected-local-branch endpointprojection allowingdecrease',objective_optimizer_source=str(G/'retry/endpoint289_objective.py'),progress='Trackadjacent segment localdistance descent frompathstart; distance tiesretaincurrentbranch; finalarc directcoordinate, no max/cumulative/nonnegativeincrement',repair_only=True,no_hyperparameter_changes=True,stored288_candidate_poses_and_U_missing=True,stored288_complete_selection_invariance_unknown=True,actual_repair_runs=['O0','N0'],no_baseline_or288_replay=True)
 sources=[G/'retry/endpoint289_prepare.py',G/'retry/endpoint289_run.py',G/'retry/endpoint289_control.py',G/'retry/endpoint289_objective.py',G/'retry/progress288_worker.py',G/'retry/source_vehicle_transition.py',Path(p['base']['archive_path']),R/'project-effective-budget-v294.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0));save(D/'model-budget.json',dict(world_build_attempts=0,clone_initializations=0,physics_ticks=0,clone_build_wall_s=0.,integration_wall_s=0.));print('289endpoint-only repair fixed;native4000/sourcephysics2560000',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())

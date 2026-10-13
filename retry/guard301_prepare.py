"""Preregisterexact296 gasguard, original300 pairedpilot andtotal6000cap."""
import argparse,zipfile,hashlib
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage301';assert not D.exists(),'Existing301: do notduplicate';D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v308.json');assert v['research_remaining']==9433 and v['actual_cumulative_wrapper_actions']==1136567;old=read(R/'stage299/plan.json');base=old['baseline296'];cfg=dict(base['config']);source=cfg['archive_path'];archive=D/'guard301.zip'
 with zipfile.ZipFile(source) as z:members={n:z.read(n) for n in z.namelist()}
 members['retry/guard301_base.py']=members['agent.py'];members['agent.py']=(G/'retry/guard301_agent.py').read_bytes()
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 archive.chmod(0o600);cfg.update(archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(G/'retry/guard301_worker.py'),worker_sha256=sha(G/'retry/guard301_worker.py'));save(D/'candidate-config.json',cfg);candidate=dict(label='near_nominalzero_gasguard',theta=base['theta'],config=cfg)
 p300=read(R/'stage300/plan.json');pilot=['T2950','T2954'];refs=[read(R/'stage300'/(road+'_296')/'result.json') for road in pilot];assert refs[0]['actual_DNF'] and refs[1]['completed'];save(D/'previous-current-champion.json',read(R/'current-champion.json'));names=['guard301_prepare.py','guard301_run.py','guard301_episode.py','guard301_worker.py','guard301_agent.py','guard301_close.py'];sources=[G/'retry'/n for n in names]+[Path(source),archive,R/'project-effective-budget-v308.json']+[R/'stage300'/(r+'_296')/'result.json' for r in pilot]
 p=dict(stage=301,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=base,candidate=candidate,cases=old['cases'],initial_observations=old['initial_observations'],pilot=pilot,pilot_baseline=refs,extension=[r for r in old['roads'] if r not in pilot],roads=old['roads'],sandbox_path=old['sandbox_path'],phase_caps=dict(training=6000),research_available=9433,rule='Onlyfeature8==1 andfeature14==0 => returnedgas0 afteroriginal296 finalclip; no otheraction/state/parameter changes',pilot_gate='Againstexact300296 pair: greatercompletioncount, orsamecountstrictlyfastercommonmean; otherwise stop. Allofficialoutcomes required.',stop='Totalnative6000, deadline, technical/censor; preserveunknown notDNF. Nochampionchange/DEV/HOLDOUT/SEALED/adoption.',hashes={str(q):sha(q) for q in sources});save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,training=0));print('301new registered;guardonly;T2950/T2954 gate->16remainingTRAIN;totalcap6000',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())

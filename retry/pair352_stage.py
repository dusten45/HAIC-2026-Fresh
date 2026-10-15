"""Register one400+400actualO0pair of the two unchanged349archives."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage352';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage352';assert not D.exists();D.mkdir(mode=0o700)
    q=read(R/'stage349/plan.json');assert read(R/'stage351/final-report-verification.json')['passed'];assert read(R/'stage350/final-report-verification.json')['passed']
    A=q['configs']['baseline'];B=q['configs']['candidate']
    assert {k:v for k,v in A.items() if k not in ['archive_path','archive_sha256','members_sha256']}=={k:v for k,v in B.items() if k not in ['archive_path','archive_sha256','members_sha256']}
    for c in [A,B]:assert sha(c['archive_path'])==c['archive_sha256'] and sha(c['worker_path'])==c['worker_sha256']
    job=read(R/'stage306/collection/O0/job.json');assert job['road']=='O0';v=read(R/'project-effective-budget-v364.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1284297,1746,84000,0,1370043)
    files=[G/'retry/pair352_stage.py',G/'retry/pair352_run.py',G/'retry/package349_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/pedal331_run.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/probe338_stage.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py',R/'stage349/plan.json',R/'stage351/summary-private.json',R/'stage351/final-report-verification.json',R/'stage350/plan.json',R/'stage350/summary-private.json',R/'stage350/final-report-verification.json',R/'stage306/collection/O0/job.json',R/'stage306/collection/O0/observations-actions-private.npz',R/'project-effective-budget-v364.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',Path(A['archive_path']),Path(B['archive_path']),Path(A['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
    p=dict(stage=352,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=job['case'],observer_rng_seed=read(R/'stage350/plan.json')['observer_rng_seed'],configs=dict(A=A,B=B),sandbox_path=q['sandbox_path'],order=['A','B'],per_arm_cap=400,total_cap=800,reset_cap=2,
        authorization='Explicitparent352: oneactualO0A/Bcomparison,400each800total, samefixed349artifacts/runtime. No newgrant, nativecache, auxiliaryrun, retry, thirdarm, tuning, protectedsplit orpromotion.',
        identity='349baseline334ON/H1versus349samepolicy+fixed342routingrule. Sameworker/assets/constants/models/runtime/environment/case/init/accessRNG; only two approved archive metadata/filter additions differ. No296baseline substitution; source306O0usedonlyknowncase/resetpixel, neverforcedtrajectory.',
        gates='351evidence reused; no newcacheactors. Independent freshsamecase resets, exactinitialpixels/fullphysics/evaluatorRNG/originalpolicystateprojection. ForBcompare eachprebranchinputstack/prestate/physics/accessRNGandreturnedcommands withA. Firstsemanticbranch is firstroute/features/control/normalstateprojectiondifference; requireactivefixedroutingfilter. Addedcandidate metadata/fullpickle differences excluded explicitly. Afterbranch ownobservations/fullreturnedcontrols/normalmemory.',
        comparison='Naturalfirstbranch only; do not force181birth or190cachedprefix. If no semanticbranch, allactualcommands/pixels/originalstate/physics/RNG/rawticks mustmatch throughnormalstop. Source/gate/interface/leak/technical mismatch stops qualification and no further arm. Aprotocolcensor orDNFwithouttechnicalerror permits registeredB, neither authorizesextension.',
        stops='Officialfinish/retirement/officialtruncation first, otherwise400protocolcensor perarm, total800orapprovaldeadline. Underlyingrawlimit2038doesnotextend400cap. No postterminalsteps.',
        metrics='Separate completion,actualDNF,protocol/technicalcensor. Bothfinishonly: officialretroactivecenterlap minus postresetstart, exactBminusA. ReportDNFprogress/contact/damage jointly, neverdamage-onlyrank orcensorassafety. PositiveBminusAlap is oneobservedregression, no tunedtolerance.',
        N2='Reuse historical350292actionofficialfinish/lap23320and337233DNFonly as separateknownTRAINcondition. Neither rerun nor charged/relabelled as new352.',
        budget=dict(research_before=1746,reserved_maximum=800,research_after_maximum=946,additional_research=0,actor_act_calls_cap=800,actor_resets_cap=2,new_native_auxiliary=0,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'native-budget.json',dict(actions=0,resets=0,actor_act_calls=0,actor_resets=0,total_cap=800,reset_cap=2,arms=dict(A=0,B=0),actor_arms=dict(A=0,B=0)))
    save(D/'reservation.json',p['budget']);print('352registered A400+B400 total800/reset2; research1746/reserve84000; no grant.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())

"""Preregister the authorized1805 grant and one unchanged349 actual episode."""
import ast
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage350';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.package349_stage import verify as previous
    q=previous(R);D=R/'stage350';assert not D.exists();D.mkdir(mode=0o700)
    assert read(R/'stage349/final-report-verification.json')['passed'] and read(R/'stage349/precommit-verification.json')['passed']
    cfg=q['configs']['candidate'];assert sha(cfg['archive_path'])==cfg['archive_sha256']=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208'
    assert sha(cfg['worker_path'])==cfg['worker_sha256'];prior=read(R/'stage340/plan.json');assert q['configs']['baseline']['archive_sha256']==prior['config']['archive_sha256']
    v=read(R/'project-effective-budget-v361.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1284005,233,84000,0)
    # Preserve source evidence for the accessible-RNG no-draw invariant.
    rng_sites=[]
    for name in ['core/vendor/car_racing.py','core/vendor/car_dynamics.py','env_wrapper.py','damage.py']:
        tree=ast.parse((G/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                for call in ast.walk(node):
                    if isinstance(call,ast.Call) and ('random' in ast.unparse(call.func)):
                        rng_sites.append(dict(file=name,function=node.name,line=call.lineno,call=ast.unparse(call.func)))
    assert not any(s['function'] in ['step','_render','_render_road','_render_indicators'] for s in rng_sites)
    save(D/'rng-source-audit.json',dict(sites=rng_sites,no_step_render_random_calls=True,limit='Static source audit plus live accessible-RNG invariant; historical340env RNG snapshots after127 were not stored. Hidden solver/OpenCV RNG is not directly captured.'))
    files=[G/'retry/episode350_stage.py',G/'retry/episode350_run.py',G/'retry/package349_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/probe338_stage.py',G/'retry/pedal331_run.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path']),R/'stage349/plan.json',R/'stage349/final-report-verification.json',R/'stage349/candidate/records-private.jsonl',R/'stage349/candidate/reset-private.json',R/'stage340/plan.json',R/'stage340/B/trace-private.jsonl',R/'stage340/B/frames-actions-private.npz',R/'stage340/B/initial-scene-private.json',R/'stage340/B/result.json',R/'stage337/B/result.json',R/'stage335/B/first-divergence-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v361.json',R/'research-deadline-current.json',D/'rng-source-audit.json']+list((G/'core').rglob('*.py'))
    p=dict(stage=350,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,case=prior['case'],observer_rng_seed=prior['observer_rng_seed'],sandbox_path=q['sandbox_path'],episode_cap=2000,total_native_cap=2038,reset_cap=1,actor_act_cap=2000,
        authorization='Parent explicitly allocates1805additional research, existing233=>2038total. Exactly one fresh349candidate N2episode. User explicitly stops at officialfinish/retirement/default2000actions, whichever first;2038is total accounting ceiling including any replay overhead, not permission to pass2000or add another arm.',
        identity='Unmodified private349current334ON/H1+fixed342general-rule archive AND observer hash. Same340environmentcode, case/init/RNG.296context separate and champion preserved. No fresh baseline;337and340are historical data only, never relabeled as new runs.',
        gates='349native0package equivalence is reused, no new cache actor. In fresh episode verify340commands/pixels234stacks/tracker/features/path/audit/nominalmemory/original state projection/pre-postphysics for233actions. Also exact full packaged349replay state and metadata. Stop immediately on mismatch, leak, interface or technical failure; no retry/extra arm/tuning.',
        RNG='Actor accessibleRNG compared through all233via saved340policy and349fullstate. Evaluator env/Python/numpy compare constant historical335reference validated by old340through127; record newpre/postRNGallsteps. After127 historical340separate envRNG snapshots absent: use unchanged no-draw source invariant plus exactphysics/pixels, never claim newly recovered historical snapshots or hidden solver/OpenCVstate.',
        contract='Fresh reset, only official grayscale stacks inactor. Every returned fullcontrol executed unchanged with own normalmemory; no stored continuation or GTselection. GT measurements evaluator-only. Prefix is part of the single actualepisode/actioncap.',
        stops='Officialfinish/retirement/otherofficialtruncation first, then2000protocolcap or deadline; source/gate/technical failure stops. No newexperiment or automaticextension afterdeadline.',
        outcomes='Finishfirst; officialretroactivecenter lap minus postreset start; unique progress, contact fixture/timing/damage/retirement jointly.2000withoutfinish is protocolcensor even though underlying rawTimeLimit would allow2038. Single knownTRAINcase only; no promotion/generalization/occlusion safety claim.',
        budget=dict(additional_research=1805,research_before=233,research_after_grant=2038,total_native_cap=2038,actual_episode_cap=2000,planned_auxiliary_native=0,minimum_unused_if2000=38,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    grant=dict(stage=350,additional_research_actions=1805,existing_research=233,research_after_grant=2038,total_native_cap=2038,episode_cap=2000,final_reserve_change=0,authorization=p['authorization']);save(D/'budget-extension.json',grant)
    v.update(version=362,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v361.json'),prior_budget_sha256=sha(R/'project-effective-budget-v361.json'),B_increment=1805,B_operating_cap=1370043,research_remaining=2038,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'));assert not (R/'project-effective-budget-v362.json').exists();save(R/'project-effective-budget-v362.json',v)
    save(D/'native-budget.json',dict(actions=0,resets=0,actor_act_calls=0,actor_resets=0,total_cap=2038,episode_cap=2000,reset_cap=1,actor_act_cap=2000))
    print('350 grant1805registered before native; research2038; actualepisode2000cap; finalreserve84000unchanged.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())

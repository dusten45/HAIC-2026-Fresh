"""Reuse qualified actualA, unchanged334 archive, and register one72-action B."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage335';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage335';assert not D.exists();D.mkdir(mode=0o700)
    v334=read(R/'stage334/independent-verification.json');assert v334['passed'] and v334['all_optical_outputs_equal_when_both_have_points'] and v334['algebra_validation']['passed'];assert read(R/'stage334/saved-evidence-verification.json')['passed']
    p334=read(R/'stage334/plan.json');assert sha(R/'stage334/plan.json')==(R/'stage334/plan.sha256').read_text().strip()
    for f,h in p334['source_hashes'].items():assert sha(f)==h,f
    cfg=read(R/'stage334/configs-private.json')['ON'];assert read(R/'stage334/N2_330_A/OFF-receipt.json')['stored_actor_calls']==72
    a=np.load(R/'stage331/A/raw-pixels-actions-private.npz');old=np.load(R/'stage330/evaluation/N2/raw-pixels-actions-private.npz');assert np.array_equal(a['observations'],old['observations']) and np.array_equal(a['actions'],old['actions']) and len(a['actions'])==72
    ar=read(R/'stage331/A/result.json');assert ar['reference330_exact'] and ar['reference_steps_matched']==72 and not ar['technical_error'] and ar['actual_terminal'] and ar['retire_reason']=='crash'
    assert read(R/'stage331/independent-verification.json')['passed']
    x=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];y=[json.loads(s) for s in (R/'stage330/evaluation/N2/trace-private.jsonl').read_text().splitlines()]
    for r,s in zip(x,y):
        assert r['executed']==s['action'] and r['features']==s['features'] and r['audit']==s['audit'] and r['nominal_memory']==s['memory']
        for k in ['collision','damage','terminal']:assert r[k]==s[k]
    prior335=read(R/'stage333/plan.json');reference335=np.load(R/'stage333/B/raw-pixels-actions-private.npz');assert np.array_equal(reference335['actions'][:65],a['actions'][:65]) and np.array_equal(reference335['observations'][:66],a['observations'][:66])
    for mode in ['OFF','ON']:
        c=cfg[mode];assert sha(c['archive_path'])==c['archive_sha256'] and sha(c['worker_path'])==c['worker_sha256']
    assert [n for n,h in cfg['OFF']['members_sha256'].items() if h!=cfg['ON']['members_sha256'][n]]==['retry/temporal_agent.py']
    inputs=[R/'stage334/plan.json',R/'stage334/configs-private.json',R/'stage334/independent-verification.json',R/'stage334/saved-evidence-verification.json',R/'stage334/summary-private.json',R/'stage331/A/result.json',R/'stage331/A/trace-private.jsonl',R/'stage331/A/raw-pixels-actions-private.npz',R/'stage331/A/boundary-private.json',R/'stage331/independent-verification.json',R/'stage330/evaluation/N2/trace-private.jsonl',R/'stage330/evaluation/N2/raw-pixels-actions-private.npz',R/'stage333/plan.json',R/'stage333/B/raw-pixels-actions-private.npz',R/'stage333/B/trace-private.jsonl',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v342.json',R/'research-deadline-current.json',G/'retry/closed335_stage.py',G/'retry/closed335_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/pedal331_run.py',G/'retry/diagnose.py',G/'retry/source_vehicle_transition.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    for mode in ['OFF','ON']:inputs.extend([Path(cfg[mode]['archive_path']),Path(cfg[mode]['worker_path'])])
    p=dict(stage=335,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=prior335['case'],observer_rng_seed=prior335['observer_rng_seed'],sandbox_path=prior335['sandbox_path'],configs=cfg,
        question='Does fixed334fallback-only tracker improve local contact persistence on its own visited states?',
        design='One newB fromreset, every action is unchanged334 ON archive returned steer/gas/brake. No stored-command overrides, no single66intervention. Existing full exact330/331A reused after fresh cachedOFF72 qualification; ambiguousA stops before native, no automatic newA/144.',
        gates='334coordinate/time/reset/optical/information gates passed. Fresh paired cache OFF/ON onA storedpixels to bind states. During actual common-command prefix require exact inputpixels and available measured physical state/RNG; policy state must match same-input cachedON, while expected controlled differences fromOFF are recorded. First difference is observed, never forced at66. After physical divergence follow actualONpixels, ownmemory and returnedcommands.',
        reference_scope='A actual fullpixels/actions/state and captured physics64+. Earlier basic pose comparison uses independent333B measured commonprefix0-65, whose pixels/commands matchA; not fabricated originalAearlyGT. RNG compared to measured64 state with unchanged postreset source step contract. HiddenOpenCV RNG andBox2D solver state not directly measurable.',
        stop='Officialterminal,72cap,contractmismatch orauthorizationdeadline. No reseed/retry/sweep/horizon expansion. No fit, sourcephysicsrollout orprotectedsplit. GT evaluatoronly.',
        interpretation='Compare commoninterval firstcontact/fixtures/persistence/damage/terminal/progress/pose/speed/steer/pedals/memory. Damageincrease notindependentautomaticveto.72survival notcompletion/generalization. Actualocclusion remainsunverified; preserve334rawnearestworsening andsubsetimprovement. Nochampionpromotion.',
        method='Parent full24chapters/appliedplan reread08:04:07-08:04:43UTC; suppliedproblemcontract,resource/split,smallfalsification principles applied; originals notcopied.',cap=72,additional_research=72,final_reserved_actions=84000,source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'A-qualification.json',dict(passed=True,actual_A72_exact330_331=True,OFF334_72_reproduced=True,new_A_actions=0,archive_unchanged334=True))
    prior=R/'project-effective-budget-v342.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282127 and v['research_remaining']==0 and v['B_operating_cap']==1366127 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    grant=dict(stage=335,additional_research_actions=72,reason='Explicitparent/usermeasuredminimumclosedlooponeB72; existingactualAqualified. NoautonewA144.',native_cap=72,final_reserve_change=0)
    save(D/'budget-extension.json',grant);v.update(version=343,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=72,B_operating_cap=1366199,research_remaining=72,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v343.json').exists();save(R/'project-effective-budget-v343.json',v);save(D/'native-budget.json',dict(cap=72,actions=0));print('335oneB72registered; B1366199; reserve84000untouched; noAduplication',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage335';p=verify(R);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()));z=np.load(R/'stage331/A/raw-pixels-actions-private.npz');actual=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];receipts=[];allrecords={}
    for mode in ['OFF','ON']:
        frozen=[json.loads(s) for s in (R/'stage334/N2_330_A'/(mode+'-private.jsonl')).read_text().splitlines()];w=prepare(p['configs'][mode],D/'cache'/mode/'cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();records=[]
        try:
            reset,_=w.call('reset',z['observations'][0]);save(D/'cache'/(mode+'-reset-private.json'),reset)
            for i in range(72):
                r,_=w.call('act',z['observations'][i]);assert r['action']==frozen[i]['action'] and r['features']==frozen[i]['features'] and r['tracker_record']==frozen[i]['tracker'] and r['pixel_path']==frozen[i]['pixel_path']
                c,_=w.call('commit',z['actions'][i]);assert c['memory']==frozen[i]['nominal_memory']
                if mode=='OFF':assert r['action']==actual[i]['calculated330'] and r['features']==actual[i]['features'] and r['delta_audit']==actual[i]['audit'] and c['state']==actual[i]['policy'] and c['memory']==actual[i]['nominal_memory']
                records.append(dict(response=r,commit=c))
            allrecords[mode]=records;receipt=dict(mode=mode,passed=True,cached_actor_calls=72,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'])
        finally:receipt['reaping']=w.close()
        save(D/'cache'/(mode+'-records-private.json'),records);receipts.append(receipt)
    assert read(D/'cache/OFF-reset-private.json')['state']==read(D/'cache/ON-reset-private.json')['state']
    first=next((i+1 for i,(a,b) in enumerate(zip(allrecords['OFF'],allrecords['ON'])) if a['response']['action']!=b['response']['action']),None)
    save(D/'cache-receipt.json',dict(passed=True,receipts=receipts,cached_actor_calls=144,first_cached_command_difference=first,first_difference_not_forced=True,reset_state_same=True,new_native_actions=0))
    print('335OFF72exactA; ON72exact334; resetstatesidentical; cachedfirstchangeobserved',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','cache']);p.add_argument('--private-root',required=True,type=Path);a=p.parse_args();globals()[a.command](a.private_root)

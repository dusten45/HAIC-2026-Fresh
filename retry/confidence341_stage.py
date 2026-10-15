"""Freeze a saved-TRAIN observational audit, without policy or simulator calls."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage341';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.routing340_stage import verify as previous
    previous(R,True);G=Path(__file__).resolve().parent.parent;D=R/'stage341';assert not D.exists();D.mkdir(mode=0o700)
    assert read(R/'stage340/final-saved-evidence-check.json')['passed'];assert read(R/'stage339/reproduction-receipt.json')['passed']
    cases=[]
    for case in read(R/'stage334/plan.json')['cases']:
        key=case['key'];cases.append(dict(key=key,road=case['road'],group=case['group'],pixels=case['pixels'],records=str(R/f'stage334/{key}/OFF-private.jsonl'),GT=str(R/f'stage334/{key}/GT-private.json'),format='334',fallback=False))
    for stage in [337,340]:cases.append(dict(key=f'N2_{stage}',road='N2',group='N2',pixels=str(R/f'stage{stage}/B/frames-actions-private.npz'),records=str(R/f'stage{stage}/B/trace-private.jsonl'),GT=None,format='actual',fallback=True))
    inputs=[R/'stage334/plan.json',R/'stage334/configs-private.json',R/'stage334/actor-cost.json',R/'stage334/summary-private.json',R/'stage339/reproduction-receipt.json',R/'stage340/plan.json',R/'stage340/final-saved-evidence-check.json',R/'stage340/summary-private.json',R/'project-effective-budget-v352.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'research-deadline-current.json']
    for c in cases:
        inputs += [Path(c['pixels']),Path(c['records'])]
        if c['GT']:inputs.append(Path(c['GT']))
    inputs += [G/'retry'/n for n in ['confidence341_stage.py','confidence341_run.py','fallback334_math.py','lineage339_audit.py']]
    inputs += [G/'core/vendor/car_dynamics.py',G/'core/vendor/car_racing.py',G/'env_wrapper.py']
    p=dict(stage=341,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],cases=cases,
        question='Can the121lineage diagnosis support a general legal-observation confidence treatment? First describe existing TRAIN feature distributions and ambiguity, not fit a rule.',
        chronology='Existing337A vs340B124-140; first route/path-length, target/q, pedals, steering, nominal memory, actual hull endpoint gap and planned path clearance. Intervention127-129 vs own-observation aftermath130+. No independent-variable causal claim after divergence.',
        labels='Diagnostic only: center lies inside exactly one captured obstacle circle at current detection; otherwise unresolved or missingGT, never distance-defined false-positive. Propagate supported birth ID only through retained source lineage; actual visibility/occlusion is unlabelled.',
        features=['component area,width,height,aspect,centroid,gray mean/range','touch observation boundary','raw-road neighbors and7x7support','closed-road connectivity to ego road','source2mredetection link, past consecutive direct run and gap','retained age and disappearance without direct detection'],
        gates='Exact detector direct outputs on every saved frame; source tracker reconstruction and lineage on every record. Immutable inputs/geometry/deadline. No missing interval filled, no RGB/semantic labels invented. Stop dependent claims on mismatch.',
        aggregation='Six original roads separately from knownN2. Appearance dedup by road+frame hash+component index, preferring existingGT then registered case order; context dedup also tracker/affine state. Report duplicates and missingGT; no independent-sample inference or exhaustive TRAIN claim.',
        decision='Only propose one observation rule if evidence supports it with dangerous fixture-supported loss audit. No sweep, fitting or step/coordinate memorization. Otherwise report insufficiency and a bounded useful native0counterfactual alternative.',
        costs=dict(new_native_actions=0,new_environment_resets=0,new_actor_calls=0,new_learning_fits=0,parameter_sweeps=0,new_source_physics_ticks=0,research_remaining=1436,final_reserved_actions=84000),
        methodology='Parent attests both full originals reread immediately before request. Problem representation/state estimation/P3/P8/cause isolation applied; official completion objective separate from observational surrogates. Originals not copied.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);print('341registered11existingtrajectories; actor/native/reset/fit/sweep0',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)

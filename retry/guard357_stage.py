"""Freeze one age0 routing guard, common passive observer and bounded cache set."""
import datetime
import hashlib
from pathlib import Path
import sys
import time
import zipfile
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage357';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage357';assert not D.exists();D.mkdir(mode=0o700);old=read(R/'stage349/plan.json');base=old['configs']['candidate'];assert sha(base['archive_path'])==base['archive_sha256']=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208';assert sha(base['worker_path'])==base['worker_sha256']
    with zipfile.ZipFile(base['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
    assert {n:hashlib.sha256(b).hexdigest() for n,b in members.items()}==base['members_sha256'];variant=dict(members)
    before="routing349 = [p for p,e in zip(obstacles,self.support349_state) if not e['low']]"
    after="routing349 = [p for p,h,e in zip(obstacles,self.hazards,self.support349_state) if h[3] == 0 or not e['low']]"
    source=variant['retry/nominal238_base.py'].decode();assert source.count(before)==1;variant['retry/nominal238_base.py']=source.replace(before,after).encode();assert {n for n in members if members[n]!=variant[n]}=={'retry/nominal238_base.py'}
    compile(variant['retry/nominal238_base.py'],'nominal238_base.py','exec')
    F=D/'artifacts';F.mkdir(mode=0o700);archive=F/'retained357.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(variant.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,15,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100444<<16;z.writestr(item,data)
    archive.chmod(0o600)
    # Both arms use exactly this passive observer; selection stays in the ZIP.
    source=Path(base['worker_path']).read_text();before="    removed=[] if support is None else [i for i,e in enumerate(support) if e['low']]\n    selected=[p[:3] for i,p in enumerate(full) if i not in removed]\n    assert [list(p) for p in obstacles_override]==[list(p) for p in selected]"
    after="""    selected=[list(p) for p in obstacles_override]
    kept=[];cursor=0
    for i,hazard in enumerate(full):
        if cursor<len(selected) and list(hazard[:3])==selected[cursor]:
            kept.append(i);cursor+=1
    assert cursor==len(selected),'routing arguments must be ordered full-hazard subset'
    removed=[i for i in range(len(full)) if i not in kept]"""
    assert source.count(before)==1;source=source.replace(before,after);worker=D/'passive-worker-private.py';worker.write_text(source);worker.chmod(0o600);compile(source,str(worker),'exec')
    configs=dict(baseline=dict(base,worker_path=str(worker),worker_sha256=sha(worker)),variant=dict(base,archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in variant.items()},worker_path=str(worker),worker_sha256=sha(worker)))
    p342=read(R/'stage342/plan.json');affected=[dict(c) for c in p342['cases']];untouched=[dict(c,expected_tracker=str(R/f"stage334/{c['key']}/ON-private.jsonl")) for c in p342['untouched_cases']]
    for c in affected:c['reference']=str(R/f"stage342/{c['key']}/candidate/records-private.jsonl");c['reference_format']='342'
    fresh=dict(key='T2954_355',road='T2954',group='new355',pixels=str(R/'stage355/B/frames-actions-private.npz'),records=str(R/'stage355/B/trace-private.jsonl'),expected_tracker=str(R/'stage355/B/trace-private.jsonl'),GT=None,format='actual',reference=str(R/'stage355/B/trace-private.jsonl'),reference_format='355')
    cases=[fresh]+affected
    for c in cases+untouched:c['count']=len(Path(c['records']).read_text().splitlines())
    assert sum(c['count'] for c in cases)==1671 and sum(c['count'] for c in untouched)==1121
    v=read(R/'project-effective-budget-v370.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1644,84000,0)
    files=[G/'retry/guard357_stage.py',G/'retry/guard357_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/support342_logic.py',G/'retry/confidence341_run.py',G/'retry/package349_run.py',G/'retry/probe338_stage.py',R/'stage349/plan.json',R/'stage349/candidate/reset-private.json',R/'stage342/plan.json',R/'stage342/summary-private.json',R/'stage356/summary-private.json',R/'stage355/summary-private.json',R/'stage355/B/reset-policy-private.json',R/'project-effective-budget-v370.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',Path(base['archive_path']),archive,Path(base['worker_path']),worker,Path(old['sandbox_path'])]
    for c in cases+untouched:
        files += [Path(c[k]) for k in ['pixels','records','expected_tracker']]
        if c.get('GT'):files.append(Path(c['GT']))
        if c.get('reference'):files.append(Path(c['reference']))
        if c['key'].startswith('N2_') and c['key'] in ['N2_337','N2_340']:files.append(R/f"stage342/{c['key']}/baseline/records-private.jsonl")
    plan=dict(stage=357,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],configs=configs,sandbox_path=old['sandbox_path'],cases=cases,untouched_cases=untouched,order=['baseline','variant'],
        policy_change='Exactly one nominal routing comprehension adds currentage0protection. Allothermembers including342birthflag/tracker/dedup/expiry/fullhazardfeatures/H1/controller/fallback identical.349and296unchanged; separateprivatevariant.',
        instrumentation='Samepassiveworkerforbotharms records the actual ordered routing subset. It doesnotchoose orfilter. Old349observer assumedlow==excluded; replacedonlythatmeasurementassumption to let runner verify actualmembership forbothpolicies.',
        budget=dict(actor_act_calls=3342,actor_resets=12,replayed_inputs_per_arm=1671,algebra_only_inputs=1121,total_covered_saved_inputs=2792,new_native_actions=0,new_environment_resets=0,new_learning_fits=0,research_remaining=1644,final_reserve=84000),
        gates='All12trajectories included inpoint-leveldirect/birth-supportedretained audit; knownmissingGT remainsunknown. Six no-lowbirthcases provenidentical by source/flaginduction, notnewactorreplay. Baseline fresh replay must reproduce original342generic/355actions/features/path/audit/tracker/support/nominalmemory/originalstateprojection before itsvariant.',
        preserved_requirement='No fixture-supported direct or birth-supportedretained UID actuallywithheld byvariant. Auditactualroutingmembership, notlowflagalone. A supportedloss fails andstop; baseline355known92loss iscontrol evidence, notcandidatepass.',
        N2_gate='BothN2_337andN2_340variant must preserve entireoriginal349route/target/float32control/nominalmemorysequences ontheir233inputs.121:0retainedpointmuststillbeexcluded127-129. Comparetonofilter342baseline for required127route/pedaland128steeringeffect; notjustsourcededuction.',
        stop='Source/reset/input/interface/tracker/baselinereproduction mismatch, variant supportedexclusion orN2effectloss stops immediately. Chargecallsbeforerequests, preservefailedjournal. No retry/newthreshold/expandedarm/fit/native/split/promotion. No actualcompletion/generalization claim fromfixedpixels.',source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_act_calls=0,actor_resets=0,cap=3342,reset_cap=12));save(D/'artifacts-private.json',configs)
    print('357 registered: oneprivateage0guard; sixpairedreplays3342acts/12resets; sixalgebraonly1121inputs; native0.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())

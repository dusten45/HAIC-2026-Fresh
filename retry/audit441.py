"""Read saved440 JSON and source hashes only; never imports a simulator.

Usage: python -m retry.audit441 PRIVATE_ROOT
Writes a new private stage441 audit, preserving all stage440 evidence.
"""
import ast
import datetime
import hashlib
import json
import sys
import time
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root):
    cpu, wall = time.process_time(), time.perf_counter()
    source = Path(__file__).resolve().parents[1]
    d, out = root / 'stage440', root / 'stage441'
    out.mkdir(mode=0o700, exist_ok=True)
    target = out / 'audit-private.json'
    assert not target.exists(), 'Audit output must be new'
    plan, budget = read(d / 'plan.json'), read(d / 'budget.json')
    static = read(d / 'static-result.json')
    assert static['passed'] and static['tests'] == 179
    assert static['plan_sha256'] == sha(d / 'plan.json')
    hashes = {str(p.relative_to(source)): sha(p)
              for p in sorted((source / 'retry').glob('*440.py'))}
    for name, digest in hashes.items():
        path = source / name
        assert plan['sources'][str(path)] == digest
        ast.parse(path.read_text(), filename=name)
    for name, digest in plan['protected'].items():
        assert sha(Path(name)) == digest
    arms = {}
    for name in ['C0', 'P']:
        folder = d / ('actual_' + name)
        rows = [json.loads(line) for line in
                (folder / 'trace-private.jsonl').read_text().splitlines()]
        prefix = suffix = raw = 0
        widths, differences = [], []
        assert len(rows) == budget['actual']['arm_actions'][name]
        for i, row in enumerate(rows, 1):
            label = name + '_step' + str(i)
            before_path = folder / (label + '-before-native-private.json')
            after_path = folder / (label + '-after-native-private.json')
            before, after = read(before_path), read(after_path)
            fact = read(folder / (label + '-actual-fact-private.json'))
            assert row['step'] == i and row == fact['row']
            assert sha(before_path) == after['pre_proof_sha256']
            assert sha(after_path) == fact['full_native_post_sha256']
            assert after['ticket_success'] and after['native_full_clock_verified']
            assert after['native_sequence'] == i
            assert before['actual_calls_in_this_env_before'] == i - 1
            assert fact['forecast_not_read'] and fact['fact']['native_fact_committed']
            assert not fact['fact']['overall_verification_success']
            assert row['raw_ticks'] == len(after['posts'])
            assert (after['full_post']['wrapper']['elapsed_raw_steps'] -
                    after['full_pre']['wrapper']['elapsed_raw_steps']) == row['raw_ticks']
            if i > 1:
                assert rows[i - 2]['post'] == row['pre']
            if i <= 118:
                assert read(folder / (label + '-prefix-verification-private.json'))['passed']
                prefix += 1
            else:
                verification = read(folder / (label + '-verification-private.json'))
                packet = read(d / (name + '_decision' + str(i - 118) +
                                   '-before-actual-dispatch-private.json'))
                record = packet['record']
                assert verification['passed'] and record['parent_memory_RNG_ledger_unchanged']
                assert record['canonical_adapter']['equal']
                assert not record['actual_done_before_step']
                assert not record['model_authorizes_actual_DONE']
                report = verification['report']
                assert report['actual_ledger'] == fact['fact']['actual_ledger']
                assert report['actual_committed_from_native_only']
                assert not report['model_values_committed']
                c = report['comparison']
                widths.append(c['progress_interval'][1] - c['progress_interval'][0])
                differences.append(abs(c['progress_difference_m']))
                suffix += 1
            assert not row['safety'] and row['damage'] == 0
            raw += row['raw_ticks']
        assert len(list(folder.glob('*-after-native-private.json'))) == len(rows)
        assert len(list(folder.glob('*-before-native-private.json'))) == len(rows)
        fork = read(folder / 'fork-private.json')
        assert fork == read(root / 'stage423/actual_C0/fork-private.json')
        last = rows[-1]
        arms[name] = dict(actions=len(rows), prefix_verified=prefix,
                          suffix_verified=suffix, raw_action_ticks=raw,
                          reset_ticks=51, damage=0,
                          official_finish=last['completed'],
                          max_progress_interval_width_m=max(widths),
                          max_abs_progress_difference_m=max(differences),
                          last_fact_sha256=sha(folder / (name + '_step' + str(len(rows)) +
                                                       '-actual-fact-private.json')))
    assert sum(x['actions'] for x in arms.values()) == budget['actual']['actions'] == 329
    finals = {}
    for path in d.glob('*-observer-final-private.json'):
        x = read(path)
        finals[x['link']['world_number']] = path
    post_count = action_count = final_posts = 0
    unfinished = []
    for path in d.glob('*-observer-private.json'):
        x = read(path)
        n = x['link']['world_number']
        assert x['link']['plan_sha256'] == static['plan_sha256']
        assert x['link']['source_manifest'] == plan['semantic_sources']
        assert x['failure'] is None
        post_count += len(x['posts'])
        action_count += len(x['actions'])
        if n in finals:
            f = read(finals[n])
            assert x['posts'] == f['posts'] and x['actions'] == f['actions']
            assert f['failure'] is None
            final_posts += len(f['posts'])
        else:
            unfinished.append(dict(world=n, label=x['link']['label'],
                                   durable_posts=len(x['posts']),
                                   durable_actions=len(x['actions']),
                                   final_receipt_present=False))
    m = budget['model']
    worlds = len(list(d.glob('world*-before-constructor-private.json')))
    first_steps = len(list(d.glob('world*-before-first-step-private.json')))
    assert worlds == m['worlds'] == m['confirmed_worlds'] == 295
    assert first_steps == 294  # one held pending parent was never integrated
    assert len(list(d.glob('*-observer-private.json'))) == worlds
    assert m['reserved_ticks'] == m['ticks'] == 30806
    assert post_count == 30762 and m['ticks'] - post_count == 44
    assert len(finals) == 292 and sorted(x['world'] for x in unfinished) == [293, 294, 295]
    assert not (d / 'P_decision23-before-actual-dispatch-private.json').exists()
    assert not (d / 'P_decision23-evidence-private.json').exists()
    assert not (d / 'result.json').exists() and not (d / 'stop-private.json').exists()
    v460 = read(root / 'project-effective-budget-v460.json')
    assert v460['research_remaining'] == 27878
    assert v460['actual_cumulative_wrapper_actions'] == 1320186
    assert v460['final_reserved_actions'] == 84000 and v460['final_reserve_used'] == 0
    a = budget['actual']
    c0 = read(d / 'actual_C0/result.json')
    tag_cpu, tag_wall = sum(m['CPU_by_tag'].values()), sum(m['wall_by_tag'].values())
    payload = dict(stage=441, mode='SAVED_ONLY_NO_SIMULATOR_IMPORT',
                   at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   authorization_end_utc='2026-10-20T10:01:55Z',
                   new_actual_actions=0, new_model_ticks=0, new_worlds=0,
                   static440=static, source_hashes=hashes, arms=arms,
                   pair_gain_s=None, promotion=False,
                   stop_class='EXTERNAL_SIGTERM_AFTER_ASSISTANT_DEADLINE_ERROR',
                   model=dict(meter_ticks=m['ticks'], reserved_ticks=m['reserved_ticks'],
                              raw_observer_posts=post_count, raw_observer_actions=action_count,
                              final_observer_posts=final_posts, worlds=worlds,
                              first_step_proofs=first_steps, final_receipts=len(finals),
                              unfinished=sorted(unfinished, key=lambda x:x['world']),
                              meter_ticks_without_raw_post_receipt=m['ticks']-post_count),
                   timing=dict(durable_only=True, final_process_CPU_unknown=True,
                               actual_CPU_s=a['CPU_s'], actual_wall_s=a['wall_s'],
                               model_CPU_s=m['CPU_s'], model_wall_s=m['execution_wall_s'],
                               wholeworker_CPU_s=budget['wholeworker_CPU_s'],
                               wholeworker_wall_s=budget['whole_execution_wall_s'],
                               narrow_model_tags_CPU_s=tag_cpu, narrow_model_tags_wall_s=tag_wall,
                               model_outside_narrow_tags_CPU_s=m['CPU_s']-tag_cpu,
                               C0_arm_actual_CPU_s=c0['exclusive_actual_CPU_s'],
                               actual_minus_C0_arm_CPU_s=a['CPU_s']-c0['exclusive_actual_CPU_s'],
                               outside_exclusive_CPU_s=budget['wholeworker_CPU_s']-m['CPU_s']-a['CPU_s'],
                               outside_exclusive_wall_s=budget['whole_execution_wall_s']-m['execution_wall_s']-a['wall_s']),
                   budget460_sha256=sha(root / 'project-effective-budget-v460.json'),
                   stage440_budget_sha256=sha(d / 'budget.json'),
                   stage440_plan_sha256=sha(d / 'plan.json'),
                   audit_CPU_s=time.process_time()-cpu, audit_wall_s=time.perf_counter()-wall)
    with target.open('x') as file:
        json.dump(payload, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write('\n')
    print(json.dumps({k:payload[k] for k in ['stage', 'mode', 'arms', 'model', 'timing',
                                            'audit_CPU_s', 'audit_wall_s']}))


if __name__ == '__main__':
    run(Path(sys.argv[1]))

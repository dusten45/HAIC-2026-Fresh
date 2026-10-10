"""Fixed saved-only connector gate: legal decision values and action opportunities.

No participant, simulator, training or replay imports. Raw contact is an outcome
label; it cannot supply a pre-action feature or an intermediate policy decision.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connector_signal(telemetry):
    """Only the route and the obstacle inputs actually consumed by that route."""
    path = telemetry['selected_path']; hazards = telemetry['route_obstacle_inputs']
    memory = telemetry['memory_hazards_after_tracker']
    assert hazards == [item[:3] for item in memory]
    if len(path) < 2 or not hazards:
        return {'evaluable':False, 'margin_m':None, 'signal':False}
    a, b = path[:2]; dx, dy = b[0]-a[0], b[1]-a[1]; square = dx*dx+dy*dy
    assert math.hypot(*a) < 1e-9 and square > 0
    margins = []
    for x, y, radius in hazards:
        u = max(0., min(1., ((x-a[0])*dx+(y-a[1])*dy)/square))
        margins.append(math.hypot(x-a[0]-u*dx, y-a[1]-u*dy)-radius-2.6)
    margin = min(margins)
    return {'evaluable':True, 'margin_m':margin, 'signal':margin < -1e-9}


def inspect_case(case):
    indexed = {}; windows = []
    for name in case['event_windows']:
        saved = json.loads(Path(name).read_text())
        windows.append({'kind':saved['kind'], 'onset_step':saved['onset_step'],
                        'trigger_step':saved['trigger_step'],
                        'first_saved_step':saved['rows'][0]['step'], 'last_saved_step':saved['rows'][-1]['step']})
        for row in saved['rows']:
            if row['step'] in indexed: assert indexed[row['step']] == row
            indexed[row['step']] = row
    ordered = [indexed[k] for k in sorted(indexed)]
    assert ordered
    decisions = []; contact = None
    for row in ordered:
        tick = row['raw_intervals']; assert tick and row['before_time'] == tick[0]['before_time']
        assert row['after_time'] == tick[-1]['after_time']
        assert row['truth_before']['time'] == row['before_time']
        for left, right in zip(tick, tick[1:]): assert left['after_time'] == right['before_time']
        prior = indexed.get(row['step']-1)
        if prior:
            assert prior['after_time'] == row['before_time']
            assert prior['observation_sha256_after'] == row['observation_sha256_before']
        measured = connector_signal(row['route_telemetry'])
        decision = {'step':row['step'], 'latest_pixel_acquisition_sim_time':row['before_time'],
                    'decision_sim_time':row['before_time'], 'first_action_application_sim_time':tick[0]['before_time'],
                    'decision_wall_including_IPC_ms':row['act_including_IPC_ms'],
                    'observation_sha256_before':row['observation_sha256_before'],
                    'acquisition_hash_link_to_prior_saved_row':prior is not None,
                    'raw_ticks_in_action':len(tick), **measured}
        decisions.append(decision)
        for index, raw in enumerate(tick):
            if raw['collision'] and contact is None:
                contact = {'step':row['step'], 'raw_tick_within_action':index+1,
                           'before_time':raw['before_time'], 'after_time':raw['after_time'],
                           'source':'privileged original raw collision label only'}
    if case['role'] == 'contact':
        assert contact is not None and contact['step'] == case['first_contact_step']
        prefix = [d for d in decisions if d['step'] <= contact['step']]
    else:
        assert contact is None and case['official_collision_steps'] == 0
        prefix = decisions
    positives = [d for d in prefix if d['signal']]
    first = positives[0] if positives else None
    slots = [d for d in prefix if first and first['step'] <= d['step']]
    contiguous = bool(slots) and [d['step'] for d in slots] == list(range(slots[0]['step'], slots[-1]['step']+1))
    return {'id':case['id'], 'role':case['role'], 'windows':windows,
            'retained_decision_count':len(decisions), 'evaluated_prefix_decision_count':len(prefix),
            'evaluable_prefix_decisions':sum(d['evaluable'] for d in prefix),
            'positive_prefix_decisions':len(positives), 'first_saved_signal':first,
            'raw_contact':contact, 'precontact_action_opportunities':len(slots) if contact and contiguous else None,
            'additional_decision_opportunities_after_first_signal':max(0,len(slots)-1) if contact and contiguous else None,
            'precontact_signal_positive_action_slots':[d['step'] for d in positives] if contact else None,
            'opportunity_steps':[d['step'] for d in slots] if contact else None,
            'opportunity_span_contiguous':contiguous if contact else None,
            'lead_to_raw_contact_interval_s':([contact['before_time']-first['decision_sim_time'],
                                              contact['after_time']-first['decision_sim_time']] if contact and first else None),
            'intermediate_raw_ticks_counted_as_new_decisions':0,
            'decision_records':decisions}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args(); path = args.plan.resolve(); directory = path.parent
    plan = json.loads(path.read_text()); wall = time.perf_counter(); cpu = time.process_time()
    assert sha(path) == (directory/'plan.sha256').read_text().split()[0]
    assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(plan['deadline_utc'])
    for name, wanted in plan['source_sha256'].items(): assert sha(Path(name)) == wanted, name
    cases = [inspect_case(c) for c in plan['cases']]
    contacts = [c for c in cases if c['role'] == 'contact']; controls = [c for c in cases if c['role'] == 'control']
    assert len(contacts) == 2 and len(controls) == 3
    legal_preaction = all(c['first_saved_signal'] and c['opportunity_span_contiguous'] for c in contacts)
    controls_evaluable = all(c['evaluable_prefix_decisions'] > 0 for c in controls)
    distinguishable = controls_evaluable and legal_preaction and not any(c['first_saved_signal'] for c in controls)
    report = {'verdict':'NO_REOPEN_CURRENT_SIGNAL_NOT_DISCRIMINATIVE_OR_ACTIONABILITY_UNESTABLISHED',
              'fixed_legal_preaction_signal_present_in_contacts':legal_preaction,
              'controls_evaluable':controls_evaluable, 'fixed_signal_distinguishes_controls':distinguishable,
              'contacts_with_signal':sum(bool(c['first_saved_signal']) for c in contacts),
              'no_contact_controls_with_signal':sum(bool(c['first_saved_signal']) for c in controls),
              'sufficient_braking_or_avoidance_time':'NOT_ESTABLISHED',
              'derived_margin_was_existing_policy_flag':False, 'cases':cases,
              'time_semantics':'Latest supplied image is prior wrapper final post-world render. Route and hazards are produced in act before action return; simulation time stays fixed during CPU/IPC. Same-row final action is applied before its first raw world step. No pixel stack or new decision is supplied between its raw ticks.',
              'legal_feature_inputs':['stored selected_path', 'stored route_obstacle_inputs'],
              'outcome_or_clock_labels_only':['raw collision interval', 'before/after simulation time', 'completed no-contact case label'],
              'limits':['First signal means first in retained prefix; gaps and episode-wide earlier signals are not reconstructed.',
                        'Contact/control windows have different event anchors and coverage; this selected-case gate is not a population accuracy estimate.',
                        'Raw contact onset is bounded to one raw interval, not a measured instant.',
                        'Existing legal intermediate values support potential same-decision computation; the frozen policy did not implement this signal or intervention.',
                        'A pre-action slot proves availability, not sufficient response time, achievable braking or prevention.',
                        'No saved pixels are regenerated and no new feature, threshold, model or counterfactual action is evaluated.'],
              'CPU_s':time.process_time()-cpu, 'metric_wall_s':time.perf_counter()-wall,
              'new_environment_actions':0, 'policy_or_model_calls':0, 'policy_changes':0,
              'replays_or_threshold_sweeps':0, 'closed_old_case_reopened':False,
              'followup_contrast_experiment_authorized_by_this_gate':False,
              'plan_sha256':sha(path), 'source_sha256':plan['source_sha256']}
    assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(plan['deadline_utc'])
    target = directory/'gate-report.json'; target.write_text(json.dumps(report, indent=2)+'\n'); target.chmod(0o600)
    print(json.dumps({k:v for k,v in report.items() if k in ('verdict','contacts_with_signal','no_contact_controls_with_signal','fixed_signal_distinguishes_controls','CPU_s','metric_wall_s')}))


if __name__ == '__main__': main()

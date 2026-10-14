"""Read saved pre-contact road support and target availability; no policy calls."""
import argparse
import json
from pathlib import Path
import time


def read_rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def review(traces, collections):
    started=time.perf_counter()
    evidence=[]
    for path in traces:
        rows=read_rows(path)
        first=next((r['step'] for r in rows if r['collision']),None)
        window=[r for r in rows if first is None or r['step']<=first]
        nonempty=[r for r in window if r['pixel_path']]
        unsupported=[r for r in nonempty if not all(r['path_road_supported'])]
        evidence.append(dict(trace_role=path.parent.name,actions=len(rows),
            first_collision_action=first,pre_contact_including_first_action=len(window),
            nonempty_paths=len(nonempty),paths_with_unsupported_points=len(unsupported),
            first_unsupported_path_action=unsupported[0]['step'] if unsupported else None,
            unsupported_targets=sum(r['target_road_supported'] is False for r in nonempty),
            target_missing_inputs=sum(bool(r['features'][0]) for r in window),
            sample_support_is_not_swept_body_feasibility=True))
    availability=[]
    for path in collections:
        rows=read_rows(path)
        availability.append(dict(road=path.parent.name,actions=len(rows),
            target_missing_inputs=sum(bool(r['features'][0]) for r in rows)))
    return dict(stage=314,review_only=True,policy_created=False,
        experiment_preregistered=False,native_evaluation_started=False,
        selected_structural_change=None,
        decision='No justified untested structural intervention selected; preserve296 and all prior failures.',
        candidate_family_review=[
            dict(axis='Temporal road perception fusion',prior=[253],
                reason='Already tested with actual mask/action changes and slower paired laps; no new direct mechanism evidence.'),
            dict(axis='Tracker transport/origin/fallback',prior=[130,131,132,184],
                reason='Existing origin, speed, metric-motion and privileged-motion studies; residual error alone does not justify repackaging.'),
            dict(axis='Direction or local route memory',prior=[208,209,261,305],
                reason='Direction and reference recovery already tested; new reliable legal signal and distinct pre-failure effect not established.'),
            dict(axis='Road closing creates unsupported connections',prior=[178,186,253],
                reason='Current failed296 pre-contact path samples and targets remain road-supported; a specific false bridge and its causal effect have not been observed.'),
            dict(axis='Pedal mode/teacher or head representation',prior=[236,248,251,276,290,306,307],
                reason='Mode exclusion, added state, matched-steering imitation and categorical joint control have already been tested; no new label objective is justified within this small screen.'),
            dict(axis='Missing-target correction',prior=[301,303,305],
                reason='Already directly tested on current296; do not reintroduce the same guard or reference recovery.')],
        current_saved_support=evidence,current_saved_target_availability=availability,
        limitations=['No statement that all perception, planning, or learning methods are impossible.',
            'Existing sampled road support does not prove continuous hull feasibility or eliminate all perception errors.',
            'This review is not a performance experiment or a new original-document mapping.'],
        next_evidence_needed='Identify a distinct pre-failure information/representation error and show an existing-input, legal intervention changes it before spending native. No automatic new collection, fit, source search or intervention.',
        cost=dict(new_native=0,new_source_physics_ticks=0,new_fits=0,new_policy_calls=0,
            new_paid_resources=0,aggregate_wall_s=time.perf_counter()-started),
        champion296_maintained=True,research_remaining=3880,final_reserved_actions=84000,
        reserve_used=0,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,
        automatic_extension=False,promotion=False)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--trace',type=Path,action='append',required=True)
    p.add_argument('--collection',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(review(a.trace,a.collection),ensure_ascii=False,indent=2)+'\n')

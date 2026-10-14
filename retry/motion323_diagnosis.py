"""Cached causal interval displacement diagnosis; never connect to an actor."""
import argparse
import collections
import datetime
import gzip
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from retry import background_motion as bm
from retry.hud248_features import decode
from retry.path271_run import read, save, sha


def rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])


def capture_registration(previous, current):
    """Observe the unmodified register return's accepted inliers, not refit them."""
    assert sys.getprofile() is None
    captured = {}

    def profile(frame, event, arg):
        if event == 'return' and frame.f_code is bm.register.__code__:
            if arg['status'] == 'registered':
                captured.update(p=frame.f_locals['p'].copy(), q=frame.f_locals['q'].copy())

    sys.setprofile(profile)
    try:
        record = bm.register(previous, current)
    finally:
        sys.setprofile(None)
    return record, captured


def origin_displacement(R, t, anchor):
    pixel = (R-np.eye(2))@anchor+t
    return np.array([-pixel[0], pixel[1]])/bm.PIXELS_PER_UNIT


def weighted_metrics(truth, prediction, roads, mask):
    roads = np.asarray(roads); rr = roads[mask]
    if not len(rr):
        return dict(rows=0, roads=0)
    e = prediction[mask]-truth[mask]
    w = np.array([1/(len(set(rr))*sum(rr == r)) for r in rr])
    result = dict(rows=len(rr), roads=len(set(rr)), channels=['right_m', 'forward_m'],
                  MAE=(w@abs(e)).tolist(), RMSE=np.sqrt(w@(e*e)).tolist(),
                  bias=(w@e).tolist(), max_abs=abs(e).max(0).tolist())
    for name, quantile in [('p95_abs', .95), ('p99_abs', .99)]:
        result[name] = []
        for k in range(2):
            order = np.argsort(abs(e[:, k]), kind='stable')
            index = min(np.searchsorted(np.cumsum(w[order]), quantile), len(order)-1)
            result[name].append(float(abs(e[order[index], k])))
    return result


def run(R):
    G = Path(__file__).resolve().parent.parent; D = R/'stage323'; p = read(D/'plan.json')
    assert sha(D/'plan.json') == (D/'plan.sha256').read_text().strip()
    for q, h in p['input_hashes'].items():
        assert sha(q) == h, q
    assert not (D/'opening.json').exists()
    assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z', '+00:00'))
    save(D/'code-receipt.json', dict(script_sha256=sha(Path(__file__))))
    save(D/'opening.json', dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start, cpu = time.perf_counter(), time.process_time(); cv2.setNumThreads(1)
    anchor = np.asarray(p['anchor']); truth = []; free = []; fixed = []; fallback = []
    roads = []; accepted = []; post = []; records = []; provenance = []; yaw_errors = []
    # Algebraic sign/units check before reading label outcomes; no rendered simulation.
    synthetic_max = 0.
    for delta in [-.12, 0., .12]:
        rot = rotation(delta); displacement = np.array([.23, 1.7])
        pix = bm.PIXELS_PER_UNIT*np.array([-displacement[0], displacement[1]])
        t = pix-(rot-np.eye(2))@anchor
        points = np.array([[10., 10.], [30., 12.], [21., 39.], [66., 29.]])
        q = points@rot.T+t
        estimated_t = q.mean(0)-rot@points.mean(0)
        synthetic_max = max(synthetic_max, float(abs(origin_displacement(rot, estimated_t, anchor)-displacement).max()))
    assert synthetic_max < 1e-12
    for road in p['roads']:
        F = R/'stage306/collection'/road
        trace = [json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        cache = np.load(F/'observations-actions-private.npz'); obs = cache['observations']
        assert len(obs) == len(trace) and np.array_equal(obs[1:, :3], obs[:-1, 1:])
        with gzip.open(F/'full-source-captures-private.jsonl.gz', 'rt') as f:
            snapshots = {r['step']: r for r in map(json.loads, f)}
        assert len(snapshots) == len(trace)
        first = next((r['step'] for r in trace if r['collision']), None)
        counts = collections.Counter(); maximum_time_error = 0.
        for i in range(1, len(trace)):
            before = snapshots[i]; now = snapshots[i+1]
            assert trace[i]['step'] == i+1 and trace[i-1]['step'] == i
            assert now['features'] == trace[i]['features'] and before['features'] == trace[i-1]['features']
            assert now['final296'] == trace[i]['action'] and now['previous_action'] == cache['actions'][i-1].tolist()
            interval = now['snapshot']['actual_time']-before['snapshot']['actual_time']
            maximum_time_error = max(maximum_time_error, abs(interval-.08)); assert abs(interval-.08) < 1e-9
            previous, current = obs[i-1, -1], obs[i, -1]
            # Both endpoint HUD readings already exist at policy row i+1.
            delta = .5*(decode(previous)[5]+decode(current)[5])*.08
            rec, support = capture_registration(np.rint(previous*255).astype(np.uint8), np.rint(current*255).astype(np.uint8))
            fb = np.array([0., trace[i]['features'][4]*.08])
            good = rec['status'] == 'registered'; a = fb.copy(); b = fb.copy()
            if good:
                points, following = support['p'], support['q']
                assert len(points) == rec['inliers']
                a = origin_displacement(np.array(rec['rotation']), np.array(rec['translation']), anchor)
                rot = rotation(delta); t = following.mean(0)-rot@points.mean(0)
                b = origin_displacement(rot, t, anchor)
                rec['HUD_fixed_RMS_px'] = float(np.sqrt(np.mean(np.sum((points@rot.T+t-following)**2, axis=1))))
                rec['HUD_fixed_translation'] = t.tolist()
            h0, h1 = before['snapshot']['hull'], now['snapshot']['hull']
            target = rotation(-h1['angle'])@(np.array(h1['position'])-h0['position'])
            actual_delta = np.arctan2(np.sin(h1['angle']-h0['angle']), np.cos(h1['angle']-h0['angle']))
            yaw_errors.append(delta-actual_delta)
            truth.append(target); free.append(a); fixed.append(b); fallback.append(fb)
            roads.append(road); accepted.append(good); post.append(first is not None and i >= first)
            rec.update(road=road, current_step=i+1, latest_input_step=i+1, interval_s=interval, HUD_integrated_delta=delta)
            records.append(rec); counts[rec['reason']] += 1
        provenance.append(dict(road=road,raw_preaction_rows=len(trace),eligible_intervals=len(trace)-1,
                               reset_unavailable_rows=1,first_collision_post_action=first,
                               accepted=counts['accepted'],reasons=dict(counts),maximum_interval_error_s=maximum_time_error,
                               stack_shift_exact=True,terminal_after_frame_used=False))
        print(json.dumps(provenance[-1]), flush=True)
    truth = np.asarray(truth); accepted = np.asarray(accepted); post = np.asarray(post)
    predictions = dict(free_rotation_with_fallback=np.asarray(free),HUD_fixed_rotation_with_fallback=np.asarray(fixed),same_fallback_only=np.asarray(fallback))
    masks = dict(whole=np.ones(len(truth), bool),registered=accepted,abstained=~accepted,
                 before_first_collision_or_no_collision=~post,after_first_collision=post,
                 registered_before=accepted&~post,registered_after=accepted&post,
                 abstained_before=~accepted&~post,abstained_after=~accepted&post)
    metrics = {label: {arm: weighted_metrics(truth, pred, roads, mask) for arm, pred in predictions.items()} for label, mask in masks.items()}
    byroad = {road: {label: {arm: weighted_metrics(truth,pred,roads,mask&(np.asarray(roads)==road)) for arm,pred in predictions.items()} for label,mask in masks.items()} for road in p['roads']}
    same = np.array_equal(predictions['free_rotation_with_fallback'][~accepted], predictions['HUD_fixed_rotation_with_fallback'][~accepted]); assert same
    np.savez_compressed(D/'predictions-private.npz',GT=truth,**predictions,accepted=accepted,post_collision=post,roads=np.asarray(roads));(D/'predictions-private.npz').chmod(0o600)
    q=D/'registrations-private.jsonl';q.write_text(''.join(json.dumps(r)+'\n' for r in records));q.chmod(0o600)
    assert not any(n.startswith(('core','env_wrapper','Box2D')) for n in sys.modules)
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    v=read(R/'project-effective-budget-v331.json'); assert v['research_remaining']==395
    pub=dict(stage=323,duplicate_found=False,prior_review=dict(ego_observer='50/54/55 flow-feature regressions, not HUD constrained registration',background_motion='56 free SVD rotation; no HUD fixed translation tested in reviewed records',reviewed_stages=[50,54,55,56]),
             target=p['target'],recipe=p['recipe'],fallback=p['fallback'],anchor_source='Unchanged56 TRAIN-only fixed calibration; no refit',
             total_intervals=len(truth),accepted=int(accepted.sum()),abstained=int((~accepted).sum()),coverage=float(accepted.mean()),
             reset_unavailable_rows=6,provenance=provenance,road_balanced_metrics=metrics,per_road=byroad,
             validation=dict(synthetic_sign_scale_max_abs_error_m=synthetic_max,shared_support_and_abstention=True,
                             fallback_exact_on_abstentions=same,source_hashes_unchanged=True,causal_endpoints_verified=True,
                             HUD_integrated_yaw_MAE_rad=float(np.mean(abs(np.asarray(yaw_errors)))),
                             HUD_integrated_yaw_p95_abs_rad=float(np.quantile(abs(np.asarray(yaw_errors)),.95))),
             quantile_recipe='Inverse weighted empirical CDF, equal mass per road within each stratum; not interpolation or pooled length weighting.',
             cost=dict(new_native=0,new_source_physics_ticks=0,new_actor_calls=0,new_fits=0,new_PPO=0,new_paid_resources=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu),
             research_remaining=395,final_reserved_actions=84000,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
             limitations=['Known six TRAIN trajectories, correlated intervals, not control benefit or new generalization validation.',
                          'Shared original free-fit acceptance freezes support; this does not evaluate a newly designed constrained-fit acceptance rule.',
                          'HUD trapezoidal endpoint integration is approximate, not true interval yaw; fallback norm speed assumes no lateral motion.',
                          'Hull-origin finite displacement differs from COM displacement and instantaneous velocity; no instant-state engineering claim.'])
    save(G/'retry/motion323_result.json',pub);save(D/'analysis-receipt.json',pub['cost'])
    print(json.dumps(dict(rows=len(truth),coverage=pub['coverage'],whole=metrics['whole'],registered=metrics['registered'],cost=pub['cost'])),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    run(parser.parse_args().private_root.resolve())

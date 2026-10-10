"""Compare a student's action with a teacher label at the same saved observation."""
import numpy as np

MODES = ('coast', 'gas_only', 'brake_only', 'both')


def action_events(student, teacher, *, steer_deadband=.05, steer_error=.10,
                  active_threshold=.10, pedal_error=.10):
    student, teacher = np.asarray(student, dtype=np.float64), np.asarray(teacher, dtype=np.float64)
    if student.ndim != 2 or student.shape[1] != 3 or teacher.shape != student.shape:
        raise ValueError('Aligned action and current-state label arrays of shape (N, 3) required')
    if not np.isfinite(student).all() or not np.isfinite(teacher).all():
        raise ValueError('Finite actions and labels required')
    if min(steer_deadband, steer_error, active_threshold, pedal_error) <= 0:
        raise ValueError('Positive thresholds required')
    error = np.abs(student - teacher)
    opposite = student[:, 0] * teacher[:, 0] < 0
    outside_deadband = np.minimum(np.abs(student[:, 0]), np.abs(teacher[:, 0])) >= steer_deadband
    student_mode = (student[:, 1] >= active_threshold).astype(int) + 2 * (student[:, 2] >= active_threshold)
    teacher_mode = (teacher[:, 1] >= active_threshold).astype(int) + 2 * (teacher[:, 2] >= active_threshold)
    major_pedal = np.maximum(error[:, 1], error[:, 2]) >= pedal_error
    masks = {
        'robust_opposed_steer': opposite & outside_deadband & (error[:, 0] >= steer_error),
        'near_zero_opposed_steer': opposite & ~outside_deadband,
        'substantial_steer_error': error[:, 0] >= steer_error,
        'substantial_gas_error': error[:, 1] >= pedal_error,
        'substantial_brake_error': error[:, 2] >= pedal_error,
        'mode_mismatch': teacher_mode != student_mode,
        'major_mode_mismatch': (teacher_mode != student_mode) & major_pedal,
    }
    for t, name_t in enumerate(MODES):
        for s, name_s in enumerate(MODES):
            if t != s:
                masks[f'modepair:teacher_{name_t}:student_{name_s}'] = (
                    (teacher_mode == t) & (student_mode == s) & major_pedal)
    return masks, student_mode, teacher_mode


def contiguous_runs(mask, steps, before_times, after_times):
    mask = np.asarray(mask, dtype=bool)
    steps = np.asarray(steps, dtype=int)
    before_times, after_times = np.asarray(before_times, float), np.asarray(after_times, float)
    if any(a.shape != mask.shape for a in [steps, before_times, after_times]):
        raise ValueError('Aligned event mask, action numbers and own-trace timestamps required')
    if np.any(np.diff(steps) <= 0) or np.any(after_times < before_times):
        raise ValueError('Ordered unique actions and valid intervals required')
    runs, start = [], None
    for i in range(len(mask) + 1):
        continues = i < len(mask) and mask[i] and (start is None or steps[i] == steps[i - 1] + 1)
        if start is not None and not continues:
            end = i - 1
            runs.append(dict(start_action=int(steps[start]), end_action=int(steps[end]),
                actions=end - start + 1, duration_s=float(after_times[end] - before_times[start])))
            start = None
        if i < len(mask) and mask[i] and start is None:
            start = i
    return runs


def summarize_actions(student, teacher, steps, before_times, after_times, *,
                      sustained_min_actions=5, **thresholds):
    masks, student_mode, teacher_mode = action_events(student, teacher, **thresholds)
    student, teacher = np.asarray(student, float), np.asarray(teacher, float)
    if not len(student):
        raise ValueError('At least one aligned action is required')
    error = student - teacher
    events = {}
    for name, mask in masks.items():
        runs = contiguous_runs(mask, steps, before_times, after_times)
        events[name] = dict(actions=int(mask.sum()), rate=float(mask.mean()),
            max_run_actions=max((r['actions'] for r in runs), default=0),
            max_run_duration_s=max((r['duration_s'] for r in runs), default=0.),
            sustained_runs=[r for r in runs if r['actions'] >= sustained_min_actions])
    return dict(rows=len(student), first_action=int(steps[0]), last_action=int(steps[-1]),
        channel_MAE=np.abs(error).mean(0).tolist(), channel_p95_abs=np.percentile(np.abs(error), 95, axis=0).tolist(),
        channel_max_abs=np.abs(error).max(0).tolist(), channel_signed_mean=error.mean(0).tolist(),
        student_mode_counts={name: int((student_mode == i).sum()) for i, name in enumerate(MODES)},
        teacher_mode_counts={name: int((teacher_mode == i).sum()) for i, name in enumerate(MODES)}, events=events)

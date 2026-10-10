"""Causal background registration under the official fixed camera geometry.

The camera follows the hull origin and rotates with hull angle. Original screen
1000x800 becomes grayscale84x84; resize width to105 to restore isotropic units.
No HUD, sprite, state, action, future frame or per-scene geometry enters inference.
One optional TRAIN-only calibration adjusts the two pixel-anchor coordinates.
"""
import cv2
import numpy as np

PIXELS_PER_UNIT = 1.701  # .105 * SCALE6 * ZOOM2.7, after horizontal rectification.
NOMINAL_ANCHOR = np.array([52.5, 63.0])
LOCAL_COM = np.array([0.0, -0.08253068932955615])  # Source hull-fixture centroid.
SETTINGS = {'rectified_size': [105, 84], 'corners_max': 100, 'corner_quality': .01,
            'corner_min_distance': 3, 'corner_block': 3, 'LK_window': 15,
            'LK_levels': 0, 'forward_backward_max_px': .5,
            'ransac_max_px': .7, 'ransac_max_iterations': 1000,
            'ransac_confidence': .99, 'minimum_inliers': 6,
            'minimum_inlier_fraction': .6, 'scale_range': [.98, 1.02],
            'maximum_rigid_RMS_px': .5, 'maximum_rotation_rad': .2,
            'anchor_calibration_bound_px': 1.0}


def background_mask():
    # Margin includes the LK half-window. Bottom HUD and centered car excluded.
    mask = np.zeros((84, 105), np.uint8)
    # A single-resolution LK avoids coarse pyramids mixing excluded HUD/sprite.
    mask[8:64, 8:96] = 255
    mask[47:64, 37:70] = 0
    return mask


def _image(frame):
    frame = np.asarray(frame)
    if frame.shape != (84, 84) or frame.dtype != np.uint8:
        raise ValueError('uint8 grayscale84 frame required')
    return cv2.resize(frame, (105, 84), interpolation=cv2.INTER_LINEAR)


def _inside(points, mask):
    rounded = np.rint(points).astype(int)
    valid = ((rounded[:, 0] >= 0) & (rounded[:, 0] < 105) &
             (rounded[:, 1] >= 0) & (rounded[:, 1] < 84))
    result = np.zeros(len(points), bool)
    result[valid] = mask[rounded[valid, 1], rounded[valid, 0]] > 0
    return result


def register(previous, current):
    """Estimate a previous→current pixel rigid map from these two frames only."""
    first, second = _image(previous), _image(current)
    mask = background_mask()
    texture = float(first[mask > 0].std())
    points = cv2.goodFeaturesToTrack(first, 100, .01, 3, mask=mask, blockSize=3)
    receipt = {'status': 'abstain', 'background_std': texture, 'corners': 0,
               'tracked': 0, 'inliers': 0}
    if points is None or len(points) < 6:
        return dict(receipt, reason='insufficient_background_corners')
    receipt['corners'] = len(points)
    options = dict(winSize=(15, 15), maxLevel=0,
                   criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
    after, ok1, _ = cv2.calcOpticalFlowPyrLK(first, second, points, None, **options)
    if after is None:
        return dict(receipt, reason='forward_LK_failed')
    back, ok2, _ = cv2.calcOpticalFlowPyrLK(second, first, after, None, **options)
    if back is None:
        return dict(receipt, reason='backward_LK_failed')
    p, q, returned = points[:, 0], after[:, 0], back[:, 0]
    good = ((ok1[:, 0] > 0) & (ok2[:, 0] > 0) & np.isfinite(q).all(1) &
            np.isfinite(returned).all(1) & (np.linalg.norm(returned-p, axis=1) <= .5))
    good &= _inside(np.nan_to_num(q, nan=-100, posinf=-100, neginf=-100), mask)
    p, q = p[good], q[good];receipt['tracked'] = len(p)
    if len(p) < 6:
        return dict(receipt, reason='insufficient_bidirectional_tracks')
    cv2.setRNGSeed(0)
    affine, inlier_mask = cv2.estimateAffinePartial2D(
        p, q, method=cv2.RANSAC, ransacReprojThreshold=.7,
        maxIters=1000, confidence=.99, refineIters=0)
    if affine is None or not np.isfinite(affine).all():
        return dict(receipt, reason='similarity_RANSAC_failed')
    kept = inlier_mask[:, 0] > 0;receipt['inliers'] = int(kept.sum())
    fraction = float(kept.mean());scale = float(np.hypot(affine[0, 0], affine[1, 0]))
    receipt.update(inlier_fraction=fraction, similarity_scale=scale)
    if kept.sum() < 6 or fraction < .6:
        return dict(receipt, reason='insufficient_RANSAC_support')
    if not .98 <= scale <= 1.02:
        return dict(receipt, reason='fixed_zoom_scale_mismatch')
    p, q = p[kept].astype(float), q[kept].astype(float)
    pc, qc = p.mean(0), q.mean(0)
    u, _, vt = np.linalg.svd((p-pc).T@(q-qc))
    rotation = vt.T@u.T
    if np.linalg.det(rotation) < 0:
        vt[-1] *= -1;rotation = vt.T@u.T
    translation = qc-rotation@pc
    rms = float(np.sqrt(np.mean(np.sum((p@rotation.T+translation-q)**2, axis=1))))
    delta = float(np.arctan2(rotation[1, 0], rotation[0, 0]))
    receipt.update(rigid_RMS_px=rms, delta_yaw_rad=delta,
                   rotation=rotation.tolist(), translation=translation.tolist())
    if rms > .5 or abs(delta) > .2:
        return dict(receipt, reason='rigid_residual_or_rotation_limit')
    return dict(receipt, status='registered', reason='accepted')


def motion_from_registration(record, *, anchor, interval_s):
    """Current-body COM displacement/yaw and interval means; no instant claim."""
    if record['status'] != 'registered' or interval_s <= 0:
        raise ValueError('registered pair and positive actual interval required')
    rotation = np.asarray(record['rotation']);translation = np.asarray(record['translation'])
    pixel_shift = (rotation-np.eye(2))@np.asarray(anchor)+translation
    origin = np.array([-pixel_shift[0], pixel_shift[1]])/PIXELS_PER_UNIT
    reflect = np.diag([1., -1.])
    # R(-delta_yaw) in body coordinates = F * pixel_rotation * F.
    com = origin + LOCAL_COM-reflect@rotation@reflect@LOCAL_COM
    displacement = np.r_[com, record['delta_yaw_rad']]
    return displacement, displacement/interval_s


def calibrate_anchor(records, origin_current_body_displacement, weights):
    """One bounded two-parameter TRAIN-only fit; never calibrate inference rows.

    Pose labels are allowed here solely to locate the fixed camera pixel anchor.
    World scale, yaw sign/gain and COM geometry remain source-defined constants.
    """
    blocks, targets, row_weights = [], [], []
    for rec, truth, weight in zip(records, origin_current_body_displacement, weights):
        if rec['status'] != 'registered':
            continue
        rotation = np.asarray(rec['rotation']);translation = np.asarray(rec['translation'])
        blocks.append(np.eye(2)-rotation)
        targets.append(translation+PIXELS_PER_UNIT*np.array([truth[0], -truth[1]]))
        row_weights.extend([weight, weight])
    if not blocks:
        raise ValueError('no registered TRAIN pairs for anchor calibration')
    matrix = np.concatenate(blocks);target = np.concatenate(targets)
    root = np.sqrt(row_weights)
    estimate, _, rank, singular = np.linalg.lstsq(matrix*root[:, None], target*root, rcond=None)
    if rank != 2 or not np.isfinite(estimate).all() or singular[-1] < 1e-6:
        raise ValueError('TRAIN anchor unidentifiable from observed rotation support')
    anchor = np.clip(estimate, NOMINAL_ANCHOR-1, NOMINAL_ANCHOR+1)
    return anchor, {'unconstrained_anchor': estimate.tolist(), 'constrained_anchor': anchor.tolist(),
                    'bound_hit': bool(np.any(anchor != estimate)), 'rank': int(rank),
                    'singular_values': singular.tolist(), 'accepted_TRAIN_pairs': len(blocks),
                    'world_scale_yaw_gain_fit': False}

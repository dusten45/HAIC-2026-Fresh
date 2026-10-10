"""Matched extra updates from a frozen action checkpoint and fixed normalization."""
import hashlib

import numpy as np


def parameter_digest(model):
    h = hashlib.sha256()
    for name in ['mean', 'scale', 'label_mean', 'label_scale']:
        a = np.asarray(getattr(model, name))
        h.update(name.encode()); h.update(str(a.shape).encode()); h.update(a.tobytes())
    for w, b in model.arrays:
        h.update(w.tobytes()); h.update(b.tobytes())
    return h.hexdigest()


def batch_indices(old_count, correction_count, *, seed, updates, batch_size, mixed):
    """Both arms share old draws; mixed batches have exactly half of each source."""
    if old_count < 1 or updates < 1 or batch_size < 2 or batch_size % 2:
        raise ValueError('Positive counts and an even batch size are required')
    if mixed and correction_count < 1:
        raise ValueError('Mixed updates need correction rows')
    old_rng = np.random.default_rng(seed + 1)
    correction_rng = np.random.default_rng(seed + 2)
    for _ in range(updates):
        old = old_rng.integers(old_count, size=batch_size)
        if mixed:
            yield old[:batch_size // 2], correction_rng.integers(correction_count, size=batch_size // 2)
        else:
            yield old, np.empty(0, dtype=np.int64)


def continue_model(model, old_inputs, old_labels, *, old_weights, seed, updates,
                   learning_rate, batch_size, correction_inputs=None,
                   correction_labels=None, check=None):
    """Start fresh Adam at existing weights; never refit any normalizer."""
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    mixed = correction_inputs is not None
    x, y = np.asarray(old_inputs, np.float32), np.asarray(old_labels, np.float32)
    w = np.asarray(old_weights, np.float32)
    if x.ndim != 2 or y.shape != (len(x), 3) or w.shape != (len(x),):
        raise ValueError('Aligned original features, labels and weights required')
    if not all(np.isfinite(a).all() for a in [x, y, w]) or np.any(w <= 0):
        raise ValueError('Finite data and positive weights required')
    if mixed:
        cx, cy = np.asarray(correction_inputs, np.float32), np.asarray(correction_labels, np.float32)
        if cx.ndim != 2 or cx.shape[1] != x.shape[1] or cy.shape != (len(cx), 3):
            raise ValueError('Aligned correction features and labels required')
        if not np.isfinite(cx).all() or not np.isfinite(cy).all():
            raise ValueError('Finite correction data required')
    normalizers = {n: getattr(model, n).copy() for n in ['mean', 'scale', 'label_mean', 'label_scale']}
    initial_digest = parameter_digest(model)
    layers = []
    for i, (weight, bias) in enumerate(model.arrays):
        layer = torch.nn.Linear(weight.shape[1], weight.shape[0])
        with torch.no_grad():
            layer.weight.copy_(torch.from_numpy(weight))
            layer.bias.copy_(torch.from_numpy(bias))
        layers.append(layer)
        if i < len(model.arrays) - 1:
            layers.append(torch.nn.Tanh())
    network = torch.nn.Sequential(*layers)
    tx = torch.from_numpy((x - model.mean) / model.scale)
    ty = torch.from_numpy((y - model.label_mean) / model.label_scale)
    tw = torch.from_numpy(w / w.mean())
    if mixed:
        tcx = torch.from_numpy((cx - model.mean) / model.scale)
        tcy = torch.from_numpy((cy - model.label_mean) / model.label_scale)
    optimizer = torch.optim.Adam(network.parameters(), lr=learning_rate)
    history = []
    old_draws = correction_draws = 0
    for step, (old_ids, correction_ids) in enumerate(batch_indices(len(x), len(cx) if mixed else 0,
            seed=seed, updates=updates, batch_size=batch_size, mixed=mixed), 1):
        if check is not None and (step == 1 or step % 100 == 0):
            check()
        ids = torch.from_numpy(old_ids)
        old_loss = (((network(tx[ids]) - ty[ids]) ** 2).mean(1) * tw[ids]).mean()
        loss = old_loss
        if mixed:
            correction_ids = torch.from_numpy(correction_ids)
            correction_loss = ((network(tcx[correction_ids]) - tcy[correction_ids]) ** 2).mean()
            loss = .5 * old_loss + .5 * correction_loss
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        old_draws += len(old_ids); correction_draws += len(correction_ids)
        if step == 1 or step == updates or step % 1050 == 0:
            history.append({'update': step, 'standardized_loss': float(loss.detach())})
    model.arrays = [(layer.weight.detach().numpy().copy(), layer.bias.detach().numpy().copy())
                    for layer in network if isinstance(layer, torch.nn.Linear)]
    assert all(np.array_equal(getattr(model, n), v) for n, v in normalizers.items())
    model.history = history
    return {'initial_parameter_digest': initial_digest, 'final_parameter_digest': parameter_digest(model),
            'updates': updates, 'old_draws': old_draws, 'correction_draws': correction_draws,
            'mixed': mixed, 'fresh_Adam': True, 'normalizers_unchanged': True, 'history': history}


def action_errors(model, inputs, labels):
    x = (np.asarray(inputs, np.float32) - model.mean) / model.scale
    for i, (w, b) in enumerate(model.arrays):
        x = x @ w.T + b
        if i < len(model.arrays) - 1:
            x = np.tanh(x)
    raw = x * model.label_scale + model.label_mean
    y = np.asarray(labels, np.float32)
    e = model.predict(inputs) - y
    return {'rows': len(y), 'MAE': abs(e).mean(0).tolist(), 'p95_abs': np.percentile(abs(e), 95, axis=0).tolist(),
            'RMSE': np.sqrt((e * e).mean(0)).tolist(),
            'normalized_MSE_clipped': float(((e / [.4, .5, .5]) ** 2).mean()),
            'standardized_MSE_raw': float((((raw - y) / model.label_scale) ** 2).mean())}

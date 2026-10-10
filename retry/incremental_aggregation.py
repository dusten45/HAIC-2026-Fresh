"""Match original/correction updates while adding one equally weighted new source."""
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


def batch_indices(old_count, phase1_count, phase2_count, *, seed, updates, batch_size, aggregate):
    """Share original draws and half of phase-one draws across matched arms."""
    if min(old_count, phase1_count, updates) < 1 or batch_size < 4 or batch_size % 4:
        raise ValueError('Positive counts and a batch size divisible by four required')
    if aggregate and phase2_count < 1:
        raise ValueError('Aggregation requires the new correction source')
    original_rng = np.random.default_rng(seed + 1)
    first_rng = np.random.default_rng(seed + 2)
    second_rng = np.random.default_rng(seed + 3)
    for _ in range(updates):
        original = original_rng.integers(old_count, size=batch_size // 2)
        first = first_rng.integers(phase1_count, size=batch_size // 2)
        if aggregate:
            yield original, first[:batch_size // 4], second_rng.integers(phase2_count, size=batch_size // 4)
        else:
            yield original, first, np.empty(0, dtype=np.int64)


def continue_aggregated_model(model, old_inputs, old_labels, *, old_weights, seed, updates,
                   learning_rate, batch_size, correction_inputs=None,
                   correction_labels=None, phase2_inputs=None, phase2_labels=None, check=None):
    """Start fresh Adam at existing weights; never refit any normalizer."""
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    mixed = correction_inputs is not None
    if not mixed: raise ValueError("The phase-one correction source is required")
    aggregate = phase2_inputs is not None
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
    if aggregate:
        nx, ny = np.asarray(phase2_inputs, np.float32), np.asarray(phase2_labels, np.float32)
        if nx.ndim != 2 or nx.shape[1] != x.shape[1] or ny.shape != (len(nx), 3):
            raise ValueError('Aligned new correction features and labels required')
        if not np.isfinite(nx).all() or not np.isfinite(ny).all():
            raise ValueError('Finite new correction data required')
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
    if aggregate:
        tnx = torch.from_numpy((nx - model.mean) / model.scale)
        tny = torch.from_numpy((ny - model.label_mean) / model.label_scale)
    optimizer = torch.optim.Adam(network.parameters(), lr=learning_rate)
    history = []
    old_draws = correction_draws = phase2_draws = 0
    for step, (old_ids, correction_ids, new_ids) in enumerate(batch_indices(len(x), len(cx), len(nx) if aggregate else 0,
            seed=seed, updates=updates, batch_size=batch_size, aggregate=aggregate), 1):
        if check is not None and (step == 1 or step % 100 == 0):
            check()
        ids = torch.from_numpy(old_ids)
        old_loss = (((network(tx[ids]) - ty[ids]) ** 2).mean(1) * tw[ids]).mean()
        loss = old_loss
        if mixed:
            correction_ids = torch.from_numpy(correction_ids)
            correction_loss = ((network(tcx[correction_ids]) - tcy[correction_ids]) ** 2).mean()
            loss = .5 * old_loss + .5 * correction_loss
            if aggregate:
                new_ids_tensor = torch.from_numpy(new_ids)
                new_loss = ((network(tnx[new_ids_tensor]) - tny[new_ids_tensor]) ** 2).mean()
                loss = .5 * old_loss + .25 * correction_loss + .25 * new_loss
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        old_draws += len(old_ids); correction_draws += len(correction_ids); phase2_draws += len(new_ids)
        if step == 1 or step == updates or step % 1050 == 0:
            history.append({'update': step, 'standardized_loss': float(loss.detach())})
    model.arrays = [(layer.weight.detach().numpy().copy(), layer.bias.detach().numpy().copy())
                    for layer in network if isinstance(layer, torch.nn.Linear)]
    assert all(np.array_equal(getattr(model, n), v) for n, v in normalizers.items())
    model.history = history
    return {'initial_parameter_digest': initial_digest, 'final_parameter_digest': parameter_digest(model),
            'updates': updates, 'old_draws': old_draws, 'correction_draws': correction_draws,
            'aggregate': aggregate, 'phase2_draws': phase2_draws, 'fresh_Adam': True, 'normalizers_unchanged': True, 'history': history}


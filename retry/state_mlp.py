"""Small CPU regressor for three state quantities in their physical units.

Input extraction and data partitions belong to the caller. Normalization uses
training rows only or an explicitly supplied frozen training normalizer.
This module imports neither simulator nor policy and does not clip actions.
"""
import numpy as np


class SmallStateMLP:
    def __init__(self, hidden=64):
        if not isinstance(hidden, int) or isinstance(hidden, bool) or hidden < 1:
            raise ValueError('positive integer hidden width required')
        self.hidden = hidden

    def fit(self, inputs, labels, sample_weight, *, seed, shuffle_seed, epochs,
            learning_rate, batch_size, normalization=None, deadline_epoch=None):
        import time
        import torch
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        x, y, w = [np.asarray(a, dtype=np.float64) for a in (inputs, labels, sample_weight)]
        if x.ndim != 2 or not len(x) or y.shape != (len(x), 3) or w.shape != (len(x),):
            raise ValueError('nonempty aligned features, three targets and row weights required')
        if not all(np.isfinite(a).all() for a in (x, y, w)) or np.any(w <= 0) or not np.isclose(w.sum(), len(x)):
            raise ValueError('finite data and positive mean-one weights required')
        if normalization is None:
            self.mean = np.average(x, axis=0, weights=w)
            self.scale = np.maximum(np.sqrt(np.average((x-self.mean)**2, axis=0, weights=w)), 1e-6)
            self.target_mean = np.average(y, axis=0, weights=w)
        else:
            self.mean, self.scale, self.target_mean = [np.asarray(a, dtype=np.float64).copy() for a in normalization]
        if self.mean.shape != (x.shape[1],) or self.scale.shape != self.mean.shape or self.target_mean.shape != (3,) or np.any(self.scale <= 0) or not all(np.isfinite(a).all() for a in (self.mean, self.scale, self.target_mean)):
            raise ValueError('finite, aligned training normalization with positive scales required')
        if epochs < 1 or batch_size < 1 or learning_rate <= 0:
            raise ValueError('positive fixed training settings required')
        tx = torch.from_numpy(((x-self.mean)/self.scale).astype(np.float32))
        ty = torch.from_numpy((y-self.target_mean).astype(np.float32))
        tw = torch.from_numpy(w.astype(np.float32))
        model = torch.nn.Sequential(torch.nn.Linear(x.shape[1], self.hidden), torch.nn.Tanh(),
                                    torch.nn.Linear(self.hidden, self.hidden), torch.nn.Tanh(),
                                    torch.nn.Linear(self.hidden, 3))
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        generator = torch.Generator().manual_seed(shuffle_seed)
        def full_loss():
            with torch.no_grad():
                return float((((model(tx)-ty)**2).mean(1)*tw).mean())
        initial_loss = full_loss()
        self.history = [{'epoch': 0, 'weighted_physical_MSE': initial_loss}]
        self.first_update_max_parameter_delta = None
        for epoch in range(epochs):
            if deadline_epoch is not None and time.time() >= deadline_epoch:
                raise TimeoutError('fixed training deadline expired')
            order = torch.randperm(len(x), generator=generator)
            for ids in order.split(batch_size):
                before = [p.detach().clone() for p in model.parameters()] if self.first_update_max_parameter_delta is None else None
                loss = (((model(tx[ids])-ty[ids])**2).mean(1)*tw[ids]).mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite training loss')
                optimizer.zero_grad()
                loss.backward()
                if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()):
                    raise FloatingPointError('nonfinite training gradient')
                optimizer.step()
                if before is not None:
                    self.first_update_max_parameter_delta = max(float((p.detach()-b).abs().max()) for p, b in zip(model.parameters(), before))
            if epoch == 0 or (epoch+1) % 100 == 0 or epoch == epochs-1:
                value = full_loss()
                if not np.isfinite(value):
                    raise FloatingPointError('nonfinite whole training loss')
                self.history.append({'epoch': epoch+1, 'weighted_physical_MSE': value})
        if not all(torch.isfinite(p).all() for p in model.parameters()):
            raise FloatingPointError('nonfinite final parameters')
        layers = [p for p in model if isinstance(p, torch.nn.Linear)]
        self.arrays = [(p.weight.detach().numpy().copy(), p.bias.detach().numpy().copy()) for p in layers]
        self.sanity = {'initial_TRAIN_weighted_physical_MSE': initial_loss,
                       'final_TRAIN_weighted_physical_MSE': self.history[-1]['weighted_physical_MSE'],
                       'first_update_changed_parameters': self.first_update_max_parameter_delta > 0,
                       'final_loss_below_initial': self.history[-1]['weighted_physical_MSE'] < initial_loss,
                       'all_losses_gradients_parameters_finite': True, 'epochs_completed': epochs}
        return self

    def predict(self, inputs):
        x = np.asarray(inputs, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != len(self.mean) or not np.isfinite(x).all():
            raise ValueError('finite input matrix matching fitted dimensions required')
        z = ((x-self.mean)/self.scale).astype(np.float32)
        for i, (w, b) in enumerate(self.arrays):
            z = z @ w.T + b
            if i < len(self.arrays)-1:
                z = np.tanh(z)
        return z.astype(np.float64) + self.target_mean

    def save(self, path):
        values = {'hidden': np.array(self.hidden), 'mean': self.mean,
                  'scale': self.scale, 'target_mean': self.target_mean}
        for i, (w, b) in enumerate(self.arrays):
            values[f'w{i}'], values[f'b{i}'] = w, b
        np.savez_compressed(path, **values)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as saved:
            model = cls(hidden=int(saved['hidden']))
            for name in ['mean', 'scale', 'target_mean']:
                setattr(model, name, saved[name].copy())
            model.arrays = [(saved[f'w{i}'].copy(), saved[f'b{i}'].copy()) for i in range(3)]
        return model

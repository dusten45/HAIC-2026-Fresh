"""Small CPU action imitator; private fitted arrays are loaded separately.

Training settings are supplied once by the experiment contract.  Observation
and memory processing belongs to the feature adapter, not the teacher policy.
"""
import numpy as np


LOW = np.array([-.4, 0., 0.], dtype=np.float32)
HIGH = np.array([.4, .5, .5], dtype=np.float32)


def clip_actions(values):
    return np.clip(values, LOW, HIGH).astype(np.float32)


class SmallActionMLP:
    def __init__(self, hidden=64):
        self.hidden = hidden

    def fit(self, inputs, labels, *, seed, epochs, learning_rate, batch_size,
            weights=None):
        import torch
        torch.set_num_threads(1)
        torch.manual_seed(seed)
        x, y = np.asarray(inputs, np.float32), np.asarray(labels, np.float32)
        if x.ndim != 2 or y.shape != (len(x), 3) or not len(x):
            raise ValueError('aligned nonempty features and action labels required')
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('finite data required')
        self.mean, self.scale = x.mean(0), np.maximum(x.std(0), .05)
        self.label_mean, self.label_scale = y.mean(0), np.maximum(y.std(0), .05)
        tx = torch.from_numpy((x - self.mean) / self.scale)
        ty = torch.from_numpy((y - self.label_mean) / self.label_scale)
        w = np.ones(len(x), np.float32) if weights is None else np.asarray(weights, np.float32)
        if w.shape != (len(x),) or np.any(w <= 0) or not np.isfinite(w).all():
            raise ValueError('positive finite weights required')
        tw = torch.from_numpy(w / w.mean())
        model = torch.nn.Sequential(torch.nn.Linear(x.shape[1], self.hidden),
            torch.nn.Tanh(), torch.nn.Linear(self.hidden, self.hidden),
            torch.nn.Tanh(), torch.nn.Linear(self.hidden, 3))
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        generator = torch.Generator().manual_seed(seed + 1)
        history = []
        for epoch in range(epochs):
            order = torch.randperm(len(x), generator=generator)
            total = 0.
            for ids in order.split(batch_size):
                error = ((model(tx[ids]) - ty[ids]) ** 2).mean(1)
                loss = (error * tw[ids]).mean()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total += float(loss.detach()) * len(ids)
            if epoch == 0 or epoch == epochs - 1 or (epoch + 1) % 50 == 0:
                history.append({'epoch': epoch + 1, 'weighted_standardized_MSE': total / len(x)})
        layers = [layer for layer in model if isinstance(layer, torch.nn.Linear)]
        self.arrays = [(layer.weight.detach().numpy().copy(), layer.bias.detach().numpy().copy())
                       for layer in layers]
        self.history = history
        return self

    def predict(self, inputs):
        x = (np.asarray(inputs, np.float32) - self.mean) / self.scale
        for i, (w, b) in enumerate(self.arrays):
            x = x @ w.T + b
            if i < len(self.arrays) - 1:
                x = np.tanh(x)
        return clip_actions(x * self.label_scale + self.label_mean)

    def save(self, path):
        values = {name: getattr(self, name) for name in ['mean', 'scale', 'label_mean', 'label_scale']}
        for i, (w, b) in enumerate(self.arrays):
            values[f'w{i}'], values[f'b{i}'] = w, b
        np.savez(path, **values)

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path, allow_pickle=False) as saved:
            for name in ['mean', 'scale', 'label_mean', 'label_scale']:
                setattr(model, name, saved[name].copy())
            model.arrays = [(saved[f'w{i}'].copy(), saved[f'b{i}'].copy()) for i in range(3)]
        return model


class LinearActionControl:
    def fit(self, inputs, labels, *, ridge, weights):
        x = np.asarray(inputs, np.float64)
        self.mean, self.scale = x.mean(0), np.maximum(x.std(0), .05)
        x = np.c_[np.ones(len(x)), (x - self.mean) / self.scale]
        w = np.asarray(weights)
        penalty = np.eye(x.shape[1]) * ridge * w.sum()
        penalty[0, 0] = 0
        self.coefficients = np.linalg.solve(x.T @ (x * w[:, None]) + penalty,
                                            x.T @ (labels * w[:, None]))
        return self

    def predict(self, inputs):
        x = np.asarray(inputs, np.float64)
        return clip_actions(np.c_[np.ones(len(x)), (x - self.mean) / self.scale] @ self.coefficients)


class ImitationAgent:
    """Hybrid: frozen legal perception/memory followed by learned action only."""
    def __init__(self, features, model):
        self.features, self.model = features, model

    def reset(self, observation):
        self.features.reset(observation)

    def act(self, observation):
        current = self.features.observe(observation)
        action = self.model.predict(current[None])[0]
        self.features.record_action(action)
        return action

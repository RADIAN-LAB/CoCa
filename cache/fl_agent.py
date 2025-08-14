"""Federated Learning–based cache advisor (stub).

This module defines a skeleton for a federated-learning cache-admission agent.
The goal is to decide which task results should be stored/replicated in
vehicular caches before the scheduler runs.

Initial version keeps the interface minimal so other components can integrate
without breaking while the learning logic is developed later.
"""
from __future__ import annotations

"""Federated-learning cache adviser with a tiny MLP (PyTorch).

Features per key (simple for now):
 0. Normalised request frequency (0-1)

Label: 1 if key produced cache hit, 0 otherwise.

Training loop (simulated FedAvg):
 • Each node would do one local SGD step; here we have a single global node so
   we imitate multiple local batches.
 • Every `round_freq` timesteps we average parameters (trivial in this single
   node case).
"""
from typing import Dict, List, Any
from collections import defaultdict
import logging
import math

import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)

torch.manual_seed(0)

class _MLP(nn.Module):
    def __init__(self, in_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pylint: disable=arguments-renamed
        return self.net(x)


class FLAdvisor:
    """Federated-learning adviser (single-process simulation).

    Feature vector per key:
        [norm_freq, norm_priority, norm_size_kb, one_hot(task_type 4)]  => 7 dims
    """

    _TYPE_COUNT = 4
    _FEAT_DIM = 12  # + speed, rsu_load, pop_decay

    def __init__(self, max_pool_size: int = 500, lr: float = 0.01, round_freq: int = 20):
        self.max_pool_size = max_pool_size
        self.round_freq = round_freq

        self.model = _MLP(self._FEAT_DIM)
        self.last_loss: float | None = None
        self._optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self._loss_fn = nn.BCELoss()

        # Runtime tables
        self._freq: Dict[str, int] = defaultdict(int)  # request counts
        self._labels: Dict[str, int] = defaultdict(int)  # 1 if hit else 0 (latest)
        self._timestep = 0

    # ------------------------------------------------------------------
    # Public API expected by experiment loop
    # ------------------------------------------------------------------

    def observe_tasks(self, items: List[tuple[str, dict]]):
        """Observe tasks.

        items: list of (key, row_dict)
        """
        import math
        for k, row in items:
            self._freq[k] += 1
            # store attributes for feature building later
            if "_attrs" not in self.__dict__:
                self._attrs: Dict[str, dict] = {}
            if k not in self._attrs:
                self._attrs[k] = row
        self._timestep += 1

    def observe_cache_result(self, key: str, hit: bool):
        """Record hit/miss outcome for supervised signal."""
        self._labels[key] = 1 if hit else 0

    def _local_update(self):
        if not self._labels:
            return
        # Build mini-batch tensors
        keys, ys = zip(*self._labels.items())
        max_freq = max(self._freq.values()) + 1e-9
        feat_batch = []
        for k in keys:
            row = self._attrs.get(k, {})
            freq = self._freq[k] / max_freq
            priority = int(row.get("priority", 0)) / 3.0
            size = int(row.get("data_size_kB", 100)) / 1000.0
            ttype = int(row.get("task_type", 0))
            locality = 1.0 if row.get("origin_rsu") == row.get("destination_rsu") else 0.0
            log_freq = math.log10(1 + self._freq[k]) / math.log10(1 + max_freq)
            speed = float(row.get("veh_speed_kmh", 0.0)) / 120.0
            rsu_load = float(row.get("rsu_load", 0.0))
            decay = float(row.get("pop_decay", 0.0))
            onehot = [1.0 if ttype == i else 0.0 for i in range(self._TYPE_COUNT)]
            feat_batch.append([freq, log_freq, priority, size, locality, speed, rsu_load, decay] + onehot)
        xs = torch.tensor(feat_batch, dtype=torch.float32)
        ys_t = torch.tensor(ys, dtype=torch.float32).unsqueeze(1)

        # One SGD step
        self._optimizer.zero_grad()
        preds = self.model(xs)
        loss = self._loss_fn(preds, ys_t)
        loss.backward()
        self.last_loss = loss.item()
        self._optimizer.step()
        logger.debug("FLAdvisor local SGD loss %.4f on %d samples", loss.item(), len(keys))
        # reset labels after update
        self._labels.clear()

    def select_pool(self) -> List[str]:
        """Return list of keys to keep (top-K by model score)."""
        if not self._freq:
            return []
        # Prepare feature tensor
        keys = list(self._freq.keys())
        max_freq = max(self._freq.values()) + 1e-9
        feat_list = []
        for k in keys:
            row = self._attrs.get(k, {})
            freq = self._freq[k] / max_freq
            priority = int(row.get("priority", 0)) / 3.0
            size = int(row.get("data_size_kB", 100)) / 1000.0  # normalise 0-1
            ttype = int(row.get("task_type", 0))
            locality = 1.0 if row.get("origin_rsu") == row.get("destination_rsu") else 0.0
            log_freq = math.log10(1 + self._freq[k]) / math.log10(1 + max_freq)
            speed = float(row.get("veh_speed_kmh", 0.0)) / 120.0
            rsu_load = float(row.get("rsu_load", 0.0))
            decay = float(row.get("pop_decay", 0.0))
            onehot = [1.0 if ttype == i else 0.0 for i in range(self._TYPE_COUNT)]
            feat_list.append([freq, log_freq, priority, size, locality, speed, rsu_load, decay] + onehot)
        xs = torch.tensor(feat_list, dtype=torch.float32)
        with torch.no_grad():
            scores = self.model(xs).squeeze(1).tolist()
        scored = sorted(zip(keys, scores), key=lambda kv: -kv[1])
        selected = [k for k, _ in scored[: self.max_pool_size]]
        return selected

    # ------------------------------------------------------------------
    # Federated-learning simulation helpers
    # ------------------------------------------------------------------

    def maybe_fedavg_round(self):
        """Simulate FedAvg every `round_freq` timesteps (trivial in single node)."""
        if self._timestep % self.round_freq == 0:
            # In multi-node scenario we would average weights here.
            # With one node no action is needed.
            pass
        # Run local update at every timestep for simplicity
        self._local_update()

    def save_state(self) -> Dict[str, Any]:
        return {
            "state_dict": self.model.state_dict(),
            "freq": dict(self._freq),
        }

    def load_state(self, state: Dict[str, Any]):
        if "state_dict" in state:
            self.model.load_state_dict(state["state_dict"])
        self._freq.update(state.get("freq", {}))

__all__ = ["FLAdvisor"]

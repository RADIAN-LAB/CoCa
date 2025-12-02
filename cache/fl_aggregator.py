"""Central aggregator for federated learning of cache popularity models.

Each RSU owns a local ``FLAdvisor`` instance (client).  Every ``round_freq``
 timesteps the SDN controller calls ``aggregate()`` to perform FedAvg on the
 model parameters and broadcast the updated global weights back to the
 clients.

This module intentionally stays framework-agnostic: it just manipulates the
PyTorch *state_dict*s that come from the advisors.  Networking / RPC is out of
scope for the simulator, so everything happens in-process.
"""
from __future__ import annotations

from typing import Dict, Iterable

import torch

from .fl_agent import FLAdvisor  # local import, avoids circular issues


class FLAggregator:
    """Implements simple FedAvg across multiple *in-process* FLAdvisor clients."""

    def __init__(self, clients: Dict[int, FLAdvisor]):
        self.clients = clients  # rsu_id -> advisor

    # ---------------------------------------------------------------------
    # FedAvg algorithm
    # ---------------------------------------------------------------------
    @staticmethod
    def _average_state_dicts(state_dicts: Iterable[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """Return element-wise average of a collection of PyTorch state_dicts."""
        avg_state: Dict[str, torch.Tensor] = {}
        count = 0
        for sd in state_dicts:
            count += 1
            for k, v in sd.items():
                if k not in avg_state:
                    avg_state[k] = v.clone().detach()
                else:
                    avg_state[k] += v
        # divide by number of models
        for k in avg_state:
            avg_state[k] /= count
        return avg_state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def aggregate(self) -> None:
        """Perform one FedAvg round and broadcast the new weights."""
        if not self.clients:
            return
        # collect local weights
        state_dicts = [adv.model.state_dict() for adv in self.clients.values()]
        global_state = self._average_state_dicts(state_dicts)
        # broadcast back
        for adv in self.clients.values():
            adv.model.load_state_dict(global_state)

    # convenient helper for experiment scripts
    def maybe_aggregate(self, timestep: int, round_freq: int) -> None:
        """Call aggregate() every *round_freq* timesteps."""
        if timestep % round_freq == 0:
            self.aggregate()


__all__ = ["FLAggregator"]

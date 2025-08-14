"""Reinforcement-Learning agent stub for cache admission/eviction.

For now this is a placeholder that only logs interactions, so the rest of the
system can integrate without requiring a full RL implementation. Later you can
swap in a real DQN/Actor-Critic.
"""
from __future__ import annotations

"""Simple DQN agent for cache admission/eviction decisions."""
from collections import deque
from typing import Any, Dict, Tuple
import random
import logging

import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)

_ACTIONS = ["noop", "evict_lru", "evict_random", "evict_lfu", "shrink_ttl"]

class _QNet(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, len(_ACTIONS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pylint: disable=arguments-renamed
        return self.net(x)

class RLAgent:
    def __init__(self, state_dim: int = 9, gamma: float = 0.95, lr: float = 1e-3, batch_size: int = 32):
        self.state_dim = state_dim
        self.gamma = gamma
        self.batch_size = batch_size
        self.epsilon = 1.0  # exploration
        self.eps_min = 0.05
        self.eps_decay = 0.995

        self.q_net = _QNet(state_dim)
        self.target_net = _QNet(state_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)

        self.replay: deque[Tuple[torch.Tensor, int, float, torch.Tensor]] = deque(maxlen=5000)
        self.step_counter = 0

    # ------------------------------------------------------------------
    def decide(self, state: Dict[str, Any]) -> str:
        state_vec = torch.tensor(self._state_to_vec(state), dtype=torch.float32)
        if random.random() < self.epsilon:
            action_idx = random.randrange(len(_ACTIONS))
        else:
            with torch.no_grad():
                q_vals = self.q_net(state_vec)
                action_idx = int(torch.argmax(q_vals).item())
        return _ACTIONS[action_idx]

    def observe(self, state: Dict[str, Any], action: str, reward: float, next_state: Dict[str, Any], done: bool = False):
        # Store transition
        s = torch.tensor(self._state_to_vec(state), dtype=torch.float32)
        ns = torch.tensor(self._state_to_vec(next_state), dtype=torch.float32)
        self.replay.append((s, _ACTIONS.index(action), reward, ns))
        self._learn()
        if done:
            # update target
            self.target_net.load_state_dict(self.q_net.state_dict())
        # decay epsilon
        self.epsilon = max(self.eps_min, self.epsilon * self.eps_decay)

    # ------------------------------------------------------------------
    def _learn(self):
        if len(self.replay) < self.batch_size:
            return
        batch = random.sample(self.replay, self.batch_size)
        states, actions, rewards, next_states = zip(*batch)
        states_t = torch.stack(list(states))
        next_states_t = torch.stack(list(next_states))
        actions_t = torch.tensor(actions, dtype=torch.int64).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)

        current_q = self.q_net(states_t).gather(1, actions_t)
        with torch.no_grad():
            max_next_q = self.target_net(next_states_t).max(1, keepdim=True).values
            target_q = rewards_t + self.gamma * max_next_q
        loss = nn.functional.mse_loss(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    # ------------------------------------------------------------------
    def _state_to_vec(self, state: Dict[str, Any]):
        return [
            state.get("cache_usage", 0.0),
            state.get("hit_rate", 0.0),
            state.get("avg_completion", 0.0),
            state.get("mean_priority", 0.0),
            state.get("mean_size", 0.0),
            state.get("locality_ratio", 0.0),
            state.get("mean_speed", 0.0),
            state.get("mean_rsu_load", 0.0),
            state.get("mean_pop_decay", 0.0),
        ]

__all__ = ["RLAgent"]

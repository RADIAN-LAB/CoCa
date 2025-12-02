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

# Restrict RL to structured, deterministic eviction strategies.
# Random eviction and TTL shrinking remain available for fixed baselines,
# but RL itself only chooses among noop / LRU / LFU.
_ACTIONS = ["noop", "evict_lru", "evict_lfu"]

class _QNet(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 256):
        super().__init__()
        # Larger, deeper network for better pattern learning
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, len(_ACTIONS)),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pylint: disable=arguments-renamed
        return self.net(x)

class RLAgent:
    def __init__(self, state_dim: int = 11, gamma: float = 0.95, lr: float = 5e-4, batch_size: int = 128):
        self.state_dim = state_dim
        self.gamma = gamma
        self.batch_size = batch_size
        self.epsilon = 0.9  # High initial exploration
        self.eps_min = 0.05  # Keep some exploration
        self.eps_decay = 0.997  # Slow decay for thorough exploration

        self.q_net = _QNet(state_dim, hidden=256)
        self.target_net = _QNet(state_dim, hidden=256)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)

        self.replay: deque[Tuple[torch.Tensor, int, float, torch.Tensor]] = deque(maxlen=50000)
        self.step_counter = 0
        self.target_update_freq = 50  # More stable target updates
        self.last_loss = 0.0
        self.learn_every = 4  # Learn every N steps
        self.num_updates = 2  # Multiple gradient updates per learn step

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
        
        self.step_counter += 1
        
        # Learn every N steps with multiple updates
        if self.step_counter % self.learn_every == 0:
            for _ in range(self.num_updates):
                self._learn()
        
        # Periodic target network update
        if self.step_counter % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        
        # Decay epsilon
        self.epsilon = max(self.eps_min, self.epsilon * self.eps_decay)

    # ------------------------------------------------------------------
    def _learn(self):
        if len(self.replay) < self.batch_size * 2:  # Need more samples before learning
            return
        batch = random.sample(self.replay, self.batch_size)
        states, actions, rewards, next_states = zip(*batch)
        states_t = torch.stack(list(states))
        next_states_t = torch.stack(list(next_states))
        actions_t = torch.tensor(actions, dtype=torch.int64).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1)

        current_q = self.q_net(states_t).gather(1, actions_t)
        
        # Double DQN: use online net to select action, target net to evaluate
        with torch.no_grad():
            next_actions = self.q_net(next_states_t).argmax(1, keepdim=True)
            next_q = self.target_net(next_states_t).gather(1, next_actions)
            target_q = rewards_t + self.gamma * next_q
        
        loss = nn.functional.smooth_l1_loss(current_q, target_q)  # Huber loss for stability
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        self.last_loss = loss.item()

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
            # Phase-aware features to detect pattern changes
            state.get("phase_position", 0.0),  # Position within phase (0-1)
            state.get("hit_rate_delta", 0.0),  # Recent hit rate change
        ]

    # ------------------------------------------------------------------
    # Model persistence
    # ------------------------------------------------------------------
    def save(self, path: str):
        """Save model weights and training state."""
        torch.save({
            'q_net': self.q_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'step_counter': self.step_counter,
        }, path)
        logger.info(f"RL agent saved to {path}")

    def load(self, path: str):
        """Load model weights and training state."""
        checkpoint = torch.load(path)
        self.q_net.load_state_dict(checkpoint['q_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon)
        self.step_counter = checkpoint.get('step_counter', 0)
        logger.info(f"RL agent loaded from {path}, epsilon={self.epsilon:.3f}")

__all__ = ["RLAgent"]

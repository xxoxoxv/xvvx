"""
Experience Replay System - Store and Learn from Past Experiences
"""

import uuid
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class Experience:
    """Single experience record"""
    id: str
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    next_state: Dict[str, Any]
    done: bool
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Experience':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ExperienceReplay:
    """Experience replay buffer with prioritized sampling"""
    
    def __init__(
        self,
        capacity: int = 100000,
        priority_alpha: float = 0.6,
        priority_beta: float = 0.4
    ):
        self.capacity = capacity
        self.priority_alpha = priority_alpha
        self.priority_beta = priority_beta
        self.buffer: List[Experience] = []
        self.priorities: List[float] = []
        self.position = 0
        self.is_full = False
    
    def add(
        self,
        state: Dict,
        action: Dict,
        reward: float,
        next_state: Dict,
        done: bool,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add experience to replay buffer"""
        exp_id = hashlib.sha256(
            f"{datetime.now().isoformat()}_{uuid.uuid4()}".encode()
        ).hexdigest()[:16]
        
        experience = Experience(
            id=exp_id,
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(1.0)  # Max priority
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = 1.0
            self.is_full = True
        
        self.position = (self.position + 1) % self.capacity
        return exp_id
    
    def sample(self, batch_size: int = 32) -> List[Dict]:
        """Sample batch of experiences with prioritized sampling"""
        if not self.buffer:
            return []
        
        import random
        import numpy as np
        
        priorities = np.array(self.priorities) ** self.priority_alpha
        probabilities = priorities / priorities.sum()
        
        indices = np.random.choice(
            len(self.buffer),
            size=min(batch_size, len(self.buffer)),
            replace=False,
            p=probabilities
        )
        
        samples = [self.buffer[i].to_dict() for i in indices]
        
        # Update priorities (importance sampling weights)
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.priority_beta)
        weights /= weights.max()
        
        for i, sample in enumerate(samples):
            sample['weight'] = float(weights[i])
        
        return samples
    
    def update_priorities(self, indices: List[int], new_priorities: List[float]):
        """Update priorities for sampled experiences"""
        for idx, priority in zip(indices, new_priorities):
            if 0 <= idx < len(self.priorities):
                self.priorities[idx] = max(priority, 1e-6)
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get most recent experiences"""
        recent = self.buffer[-count:] if len(self.buffer) >= count else self.buffer
        return [exp.to_dict() for exp in reversed(recent)]
    
    def filter_by_reward(
        self,
        min_reward: Optional[float] = None,
        max_reward: Optional[float] = None
    ) -> List[Dict]:
        """Filter experiences by reward range"""
        filtered = []
        for exp in self.buffer:
            if min_reward is not None and exp.reward < min_reward:
                continue
            if max_reward is not None and exp.reward > max_reward:
                continue
            filtered.append(exp.to_dict())
        return filtered
    
    def filter_by_metadata(self, key: str, value: Any) -> List[Dict]:
        """Filter experiences by metadata"""
        filtered = []
        for exp in self.buffer:
            if exp.metadata.get(key) == value:
                filtered.append(exp.to_dict())
        return filtered
    
    def clear(self):
        """Clear all experiences"""
        self.buffer.clear()
        self.priorities.clear()
        self.position = 0
        self.is_full = False
    
    def stats(self) -> Dict:
        """Get buffer statistics"""
        if not self.buffer:
            return {
                'count': 0,
                'capacity': self.capacity,
                'is_full': False,
                'avg_reward': 0,
                'min_reward': 0,
                'max_reward': 0
            }
        
        rewards = [exp.reward for exp in self.buffer]
        return {
            'count': len(self.buffer),
            'capacity': self.capacity,
            'is_full': self.is_full,
            'avg_reward': sum(rewards) / len(rewards),
            'min_reward': min(rewards),
            'max_reward': max(rewards),
            'positive_count': sum(1 for r in rewards if r > 0),
            'negative_count': sum(1 for r in rewards if r < 0)
        }
    
    def save_to_redis(self, redis_layer, key: str = 'experience_replay'):
        """Save buffer to Redis"""
        import json
        data = {
            'buffer': [exp.to_dict() for exp in self.buffer],
            'priorities': self.priorities,
            'position': self.position,
            'is_full': self.is_full
        }
        # Note: In production, use Redis streams or lists for large buffers
        print(f"ℹ Experience replay saved (simulation)")
        return True
    
    def load_from_redis(self, redis_layer, key: str = 'experience_replay'):
        """Load buffer from Redis"""
        # Note: Implementation depends on Redis storage strategy
        print(f"ℹ Experience replay loaded (simulation)")
        return True


# Singleton instance
_experience_replay: Optional[ExperienceReplay] = None


def get_experience_replay(capacity: int = 100000) -> ExperienceReplay:
    """Get or create experience replay singleton"""
    global _experience_replay
    if _experience_replay is None:
        _experience_replay = ExperienceReplay(capacity=capacity)
    return _experience_replay

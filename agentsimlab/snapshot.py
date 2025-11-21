"""Snapshot utilities coordinating kernel and agent snapshots."""
import pickle
from typing import Any, Dict, Iterable

class Snapshot:
    def __init__(self, kernel_blob: bytes, agent_states: Dict[str, Dict]):
        self.kernel_blob = kernel_blob
        self.agent_states = agent_states

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({'kernel': self.kernel_blob, 'agents': self.agent_states}, f)

    @staticmethod
    def load(path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return Snapshot(data['kernel'], data['agents'])

"""Lightweight simulation logger."""
import json
from typing import Any, Dict

class SimLogger:
    def __init__(self):
        self._events = []

    def log(self, event_type: str, actor: str, payload: Dict):
        evt = {'type': event_type, 'actor': actor, 'payload': payload}
        self._events.append(evt)

    def export_jsonl(self, path: str):
        with open(path, 'w') as f:
            for e in self._events:
                f.write(json.dumps(e) + "\n")

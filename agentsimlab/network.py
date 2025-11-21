"""Network / communication layer stubs."""
from typing import Dict, Any

class Network:
    def __init__(self, topology=None):
        self.topology = topology or {}
        self.messages = []

    def send(self, src: str, dst: str, payload: Any):
        self.messages.append({'src': src, 'dst': dst, 'payload': payload})

    def drain(self):
        msgs = list(self.messages)
        self.messages.clear()
        return msgs

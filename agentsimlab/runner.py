"""Experiment runner updated to use deterministic kernel registration."""
from .kernel import Kernel
from .snapshot import Snapshot
from typing import Iterable

class Experiment:
    def __init__(self, seed=0, phases=None):
        self.kernel = Kernel(seed=seed, phases=phases)
        self.agents = []
        self.logger = None

    def add_agent(self, agent, phase=None):
        self.agents.append(agent)
        # register with kernel under agent.agent_id
        self.kernel.register(agent.agent_id, agent, phase=phase)

    def run(self, steps=10):
        for a in self.agents:
            a.on_start(self.kernel)
        self.kernel.run(steps)

    def snapshot(self):
        agent_states = {a.agent_id: a.snapshot() for a in self.agents}
        return Snapshot(self.kernel.snapshot(), agent_states)

    def restore(self, snapshot_obj: Snapshot):
        self.kernel.restore(snapshot_obj.kernel_blob)
        for a in self.agents:
            state = snapshot_obj.agent_states.get(a.agent_id, {})
            a.restore(state)

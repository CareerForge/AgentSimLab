"""Agent API stubs that use Kernel-provided RNG streams."""
from typing import Any, Dict

class BaseAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def on_start(self, kernel):
        """Optional lifecycle hook called before simulation starts."""
        pass

    def observe(self, obs):
        """Receive an observation object (framework-specific)."""
        pass

    def act(self, kernel):
        """Return an action or perform effects using the kernel. Must be deterministic if kernel RNG is used."""
        raise NotImplementedError

    def step(self, kernel):
        """Default stepping behaviour: call act()."""
        self.act(kernel)

    def step_phase(self, kernel, phase: str):
        # default to normal step
        self.step(kernel)

    def snapshot(self) -> Dict:
        return {'agent_id': self.agent_id}

    def restore(self, data: Dict):
        self.agent_id = data.get('agent_id', self.agent_id)

class CounterAgent(BaseAgent):
    """A trivial agent used in tests: increments internal counter by kernel-provided RNG each step."""
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.counter = 0.0

    def act(self, kernel):
        rng = kernel.get_rng(self.agent_id)
        self.counter += rng.random()
        return self.counter

    def snapshot(self):
        return {'agent_id': self.agent_id, 'counter': self.counter}

    def restore(self, data):
        super().restore(data)
        self.counter = data.get('counter', 0.0)

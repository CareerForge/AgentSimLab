from agentsimlab.runner import Experiment
from agentsimlab.agent import CounterAgent

def test_experiment_basic():
    exp = Experiment(seed=42)
    a = CounterAgent('bot')
    exp.add_agent(a)
    exp.run(steps=5)
    assert exp.kernel.time == 5
    assert a.counter > 0

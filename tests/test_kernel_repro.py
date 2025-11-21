from agentsimlab.kernel import Kernel
from agentsimlab.agent import CounterAgent
from agentsimlab.snapshot import Snapshot

def run_sequence(seed, steps=5, num_agents=2):
    kernel = Kernel(seed=seed)
    agents = []
    for i in range(num_agents):
        a = CounterAgent(f'a{i}')
        agents.append(a)
        kernel.register(a.agent_id, a)
    # run steps and collect counters
    for _ in range(steps):
        kernel.step()
    return [a.counter for a in agents], kernel.time

def test_reproducible_runs_multi_agent():
    c1, t1 = run_sequence(123, steps=10, num_agents=3)
    c2, t2 = run_sequence(123, steps=10, num_agents=3)
    assert t1 == t2
    for x,y in zip(c1,c2):
        assert abs(x - y) < 1e-12

def test_snapshot_and_restore_multi_agent(tmp_path):
    kernel = Kernel(seed=999)
    agents = []
    for i in range(2):
        a = CounterAgent(f'a{i}')
        agents.append(a)
        kernel.register(a.agent_id, a)
    kernel.run(3)
    snap = Snapshot(kernel.snapshot(), {a.agent_id: a.snapshot() for a in agents})
    # advance more
    kernel.run(2)
    vals_after = [a.counter for a in agents]
    # save and restore
    p = tmp_path / 'agentsim.snap'
    snap.save(str(p))
    loaded = Snapshot.load(str(p))
    kernel.restore(loaded.kernel_blob)
    for a in agents:
        a.restore(loaded.agent_states[a.agent_id])
    # continue and check determinism
    kernel.run(2)
    for a, v in zip(agents, vals_after):
        assert abs(a.counter - v) < 1e-12

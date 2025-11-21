"""Deterministic Kernel with RNG management and deterministic scheduling.

Features:
- Master RNG seed for run-level determinism.
- Per-entity RNG streams derived deterministically from master RNG.
- Deterministic scheduler that runs registered entities in a stable order.
- Snapshot/restore capturing time and RNG states for reproducibility.
- Support for logical "phases" within a tick to allow deterministic ordering
  of perception/action/commit steps.

Notes:
- This implementation uses Python's `random.Random` for portability.
- For higher-performance or cross-language reproducibility, replace RNG
  implementation with a fixed algorithm like PCG64 and serialize state explicitly.
"""
from typing import Any, Dict, List, Optional, Callable, Tuple
import random
import pickle
import hashlib

class RNGStream:
    """A lightweight RNG stream wrapper around random.Random.

    Each stream is seeded from an integer. We keep its internal state via getstate/setstate.
    """
    def __init__(self, seed: int):
        self._seed = int(seed)
        self._rng = random.Random(self._seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def get_state(self) -> Tuple:
        return self._rng.getstate()

    def set_state(self, state: Tuple):
        self._rng.setstate(state)

    def reseed(self, seed: int):
        self._seed = int(seed)
        self._rng = random.Random(self._seed)

class RNGManager:
    """Manages the master RNG and per-entity streams.

    Per-entity seeds are derived deterministically from the master RNG using
    hashed integers so that per-entity streams are reproducible across runs.
    """
    def __init__(self, master_seed: int):
        self.master_seed = int(master_seed)
        self.master = random.Random(self.master_seed)
        self._streams: Dict[str, RNGStream] = {}

    def _derive_seed(self, name: str) -> int:
        # derive a 32-bit-ish integer seed deterministically from master RNG and name
        # We draw from master RNG deterministically and mix with the name hash.
        # Note: calling this will advance the master RNG; the order of derive calls is stable
        # as long as registration order is deterministic.
        drawn = self.master.getrandbits(64)
        h = int(hashlib.sha256(name.encode('utf-8')).hexdigest(), 16) & ((1<<64)-1)
        seed = (drawn ^ h) & ((1<<63)-1)
        return seed

    def get_stream(self, name: str) -> RNGStream:
        if name not in self._streams:
            seed = self._derive_seed(name)
            self._streams[name] = RNGStream(seed)
        return self._streams[name]

    def get_state(self) -> Dict[str, Tuple]:
        state = {'master_state': self.master.getstate(), 'streams': {}}
        for name, s in self._streams.items():
            state['streams'][name] = s.get_state()
        return state

    def set_state(self, state: Dict[str, Tuple]):
        self.master.setstate(state['master_state'])
        for name, st in state.get('streams', {}).items():
            if name in self._streams:
                self._streams[name].set_state(st)
            else:
                # create stream and set its state
                s = RNGStream(0)
                s.set_state(st)
                self._streams[name] = s

class Kernel:
    """Deterministic simulation kernel.

    Entities registered with the kernel must implement a .step(kernel) method.
    They may request an RNG stream by calling kernel.get_rng(name) to obtain a
    per-entity RNGStream instance seeded deterministically.

    The scheduler runs entities in registration order, and supports "phases"
    within a tick to control ordering: e.g., 'perceive', 'act', 'commit'.
    """
    def __init__(self, seed: int = 0, phases: Optional[List[str]] = None):
        self.time = 0
        self._rng_manager = RNGManager(seed)
        self._entities: List[Tuple[str, Any]] = []  # list of (id, entity)
        self._phases = phases or ['perceive', 'act', 'commit']
        # mapping phase -> list of (id, entity)
        self._phase_registrations: Dict[str, List[Tuple[str, Any]]] = {p: [] for p in self._phases}

    def register(self, entity_id: str, entity: Any, phase: Optional[str] = None):
        """Register an entity under a stable id and optional phase.
        Registration order determines execution order for determinism.
        """
        if phase is None:
            phase = self._phases[0]
        if phase not in self._phases:
            raise ValueError(f"Unknown phase: {phase}")
        # avoid duplicate registrations
        if any(entity is e for (_id, e) in self._entities):
            return
        self._entities.append((entity_id, entity))
        self._phase_registrations[phase].append((entity_id, entity))

    def unregister(self, entity: Any):
        self._entities = [(i,e) for (i,e) in self._entities if e is not entity]
        for p in self._phases:
            self._phase_registrations[p] = [(i,e) for (i,e) in self._phase_registrations[p] if e is not entity]

    def get_rng(self, name: str):
        """Return the RNGStream for a given name (usually agent id)."""
        return self._rng_manager.get_stream(name)

    def step(self):
        """Run a single logical tick executing all phases in order."""
        # For reproducibility we iterate phases and within each phase iterate in registration order.
        for phase in self._phases:
            for entity_id, entity in list(self._phase_registrations[phase]):
                # call entity.step_phase if available else .step
                # provide phase to the entity via attribute or method param
                step_fn = getattr(entity, 'step_phase', None)
                if callable(step_fn):
                    step_fn(self, phase)
                else:
                    # default: call .step(kernel)
                    entity.step(self)
        self.time += 1

    def run(self, steps: int):
        for _ in range(steps):
            self.step()

    def snapshot(self) -> bytes:
        """Return a bytes blob encoding kernel time and RNG manager state."""
        state = {
            'time': self.time,
            'rng': self._rng_manager.get_state(),
            'phases': self._phases,
            # we do not serialize entities here; entities are expected to implement their own snapshot APIs
        }
        return pickle.dumps(state)

    def restore(self, blob: bytes):
        state = pickle.loads(blob)
        self.time = state['time']
        self._phases = state.get('phases', self._phases)
        self._rng_manager.set_state(state['rng'])

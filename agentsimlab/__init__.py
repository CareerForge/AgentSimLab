"""AgentSimLab - lightweight reproducible multi-agent simulation stubs.

This package is a starting scaffold for the AgentSimLab project described by the user:
deterministic kernel, snapshotting, agent API, network stubs, logging, and basic tests.
"""

from .kernel import Kernel
from .agent import BaseAgent
from .snapshot import Snapshot
from .network import Network
from .logger import SimLogger
from .version import __version__

__all__ = ["Kernel", "BaseAgent", "Snapshot", "Network", "SimLogger", "__version__"]

"""50_ArcanisSecurity — Capability-based security framework.

Implements fine-grained capability tokens for the Arcanis ecosystem,
replacing the RBAC model in 22_ArcanisSecurity with a capability-based model.
"""

__version__ = "0.1.0"

from arcanis_security.capability import Capability, CapabilityToken, CapabilityScope
from arcanis_security.manager import CapabilityManager

__all__ = ["Capability", "CapabilityToken", "CapabilityScope", "CapabilityManager"]

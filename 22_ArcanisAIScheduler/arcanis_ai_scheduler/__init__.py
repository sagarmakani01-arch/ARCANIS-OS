"""22_ArcanisAIScheduler — AI-augmented process scheduler.

Tracks process behavior patterns, predicts workload types, and provides
scheduling hints (priority boosts, time quantum adjustments) to the kernel.
"""

__version__ = "0.1.0"

from arcanis_ai_scheduler.tracker import ProcessTracker, ProcessBehavior
from arcanis_ai_scheduler.predictor import WorkloadPredictor, WorkloadType
from arcanis_ai_scheduler.scheduler import AIScheduler

__all__ = ["ProcessTracker", "ProcessBehavior", "WorkloadPredictor",
           "WorkloadType", "AIScheduler"]

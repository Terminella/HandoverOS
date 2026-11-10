
"""
HandoverOS Intelligence Engine.

Extracts, verifies and structures project knowledge
for project continuity and handover generation.
"""

from intelligence.pipeline import IntelligencePipeline
from intelligence.schemas import IntelligencePipelineResult

__all__ = [
    "IntelligencePipeline",
    "IntelligencePipelineResult",
]

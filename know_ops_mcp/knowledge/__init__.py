"""Knowledge domain — Pydantic models, registry, and serializer.

Importing this package auto-registers all known Knowledge subclasses.
"""

from know_ops_mcp.knowledge.base import BaseKnowledge, for_type, register
from know_ops_mcp.knowledge.general import GeneralKnowledge

__all__ = ["BaseKnowledge", "GeneralKnowledge", "for_type", "register"]

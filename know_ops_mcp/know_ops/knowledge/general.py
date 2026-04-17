"""GeneralKnowledge — default knowledge type with no extra fields beyond BaseKnowledge."""

from __future__ import annotations

from typing import Literal

from know_ops_mcp.know_ops.knowledge.base import BaseKnowledge, register


@register
class GeneralKnowledge(BaseKnowledge):
    type: Literal["general"] = "general"

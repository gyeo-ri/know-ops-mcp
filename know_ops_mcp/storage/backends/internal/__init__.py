"""Internal storage backends.

No external dependency. Usable for testing, temporary use, or single-device
production.
"""

from __future__ import annotations

from know_ops_mcp.storage.base import BaseStorage


class InternalStorage(BaseStorage):
    pass

"""Internal storage backends.

No external dependency. Usable for testing, temporary use, or single-device
production. Can also be passed as the `cache` argument to ExternalStorage.
"""

from __future__ import annotations

from know_ops_mcp.know_ops.storage.base import BaseStorage


class InternalStorage(BaseStorage):
    pass

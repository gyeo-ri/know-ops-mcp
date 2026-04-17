"""External storage backends.

Talk to a remote source (GitHub, S3, Notion, etc) over the network.
Wrapped by `CachedStorage` for performance.
"""

from __future__ import annotations

from abc import abstractmethod

from know_ops_mcp.storage.base import BaseStorage


class ExternalStorage(BaseStorage):
    @abstractmethod
    def list_versions(self) -> dict[str, str]:
        """Return name -> opaque version string (e.g., GitHub SHA, ETag).

        Used by `CachedStorage` to detect which entries changed without
        downloading their full content.
        """
        ...

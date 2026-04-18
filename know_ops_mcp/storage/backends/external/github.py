"""GitHub repository storage via the REST API.

One `<knowledge_key>.md` file per entry under an optional subdirectory of a
single branch. Network-only; pair with `CachedStorage` to avoid hitting the
API on every read.

Listing uses the Git Trees API (recursive=true) which supports up to ~100k
entries / 7MB tree size in a single call. Larger repos raise a runtime error
(no pagination fallback).

Rate limit handling: on 429 or 403-with-rate-limit-exhausted, wait for
Retry-After / X-RateLimit-Reset and retry once. Further failures raise.
"""

from __future__ import annotations

import base64
import re
import time
from urllib.parse import urlparse

import httpx

from know_ops_mcp.storage.backends.external import ExternalStorage

_API_BASE = "https://api.github.com"
_DEFAULT_TIMEOUT = 10.0
_MAX_RETRY_WAIT = 60.0


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub repo URL.

    Accepts `https://github.com/owner/repo`, with or without `.git` suffix
    or trailing slash. Raises ValueError on malformed input.
    """
    parsed = urlparse(url.strip())
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError(f"Not a github.com URL: {url!r}")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"URL missing owner/repo: {url!r}")
    owner, repo = parts[0], parts[1]
    repo = re.sub(r"\.git$", "", repo)
    return owner, repo


class GitHubStorage(ExternalStorage):
    def __init__(
        self,
        repo_url: str,
        token: str,
        *,
        subdirectory: str = "",
        branch: str = "main",
    ) -> None:
        self._owner, self._repo = parse_repo_url(repo_url)
        self._subdirectory = subdirectory.strip("/")
        self._branch = branch
        self._client = httpx.Client(
            base_url=_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=_DEFAULT_TIMEOUT,
        )

    def _path(self, name: str) -> str:
        if self._subdirectory:
            return f"{self._subdirectory}/{name}.md"
        return f"{name}.md"

    def _contents_url(self, path: str) -> str:
        return f"/repos/{self._owner}/{self._repo}/contents/{path}"

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        for attempt in range(2):
            r = self._client.request(method, url, **kwargs)
            if attempt == 0 and _is_rate_limited(r):
                time.sleep(_compute_wait(r))
                continue
            return r
        return r  # type: ignore[possibly-undefined]

    def _get_metadata(self, path: str) -> dict | None:
        r = self._request("GET", self._contents_url(path), params={"ref": self._branch})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def read(self, name: str) -> str | None:
        meta = self._get_metadata(self._path(name))
        if meta is None:
            return None
        return base64.b64decode(meta["content"]).decode("utf-8")

    def write(self, name: str, content: str) -> None:
        path = self._path(name)
        existing = self._get_metadata(path)
        body: dict = {
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self._branch,
        }
        if existing is not None:
            body["sha"] = existing["sha"]
            body["message"] = f"Update {name}"
        else:
            body["message"] = f"Create {name}"
        r = self._request("PUT", self._contents_url(path), json=body)
        r.raise_for_status()

    def delete(self, name: str) -> bool:
        path = self._path(name)
        existing = self._get_metadata(path)
        if existing is None:
            return False
        r = self._request(
            "DELETE",
            self._contents_url(path),
            json={
                "message": f"Delete {name}",
                "sha": existing["sha"],
                "branch": self._branch,
            },
        )
        r.raise_for_status()
        return True

    def _to_key(self, path: str) -> str:
        rel = path[len(self._subdirectory) + 1:] if self._subdirectory else path
        return rel.removesuffix(".md")

    def list_versions(self) -> dict[str, str]:
        return {self._to_key(e["path"]): e["sha"] for e in self._list_tree()}

    def list_all(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for entry in self._list_tree():
            key = self._to_key(entry["path"])
            content = self.read(key)
            if content is not None:
                result[key] = content
        return result

    def _list_tree(self) -> list[dict]:
        r = self._request(
            "GET",
            f"/repos/{self._owner}/{self._repo}/git/trees/{self._branch}",
            params={"recursive": "true"},
        )
        if r.status_code == 404:
            return []
        r.raise_for_status()
        payload = r.json()
        if payload.get("truncated"):
            raise RuntimeError(
                "Repository tree exceeds GitHub Trees API single-call limit "
                "(~100k entries / 7MB). This backend does not paginate; "
                "split into multiple repos or use a smaller subdirectory."
            )
        prefix = f"{self._subdirectory}/" if self._subdirectory else ""
        entries: list[dict] = []
        for item in payload.get("tree", []):
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if not path.endswith(".md"):
                continue
            basename = path.rsplit("/", 1)[-1]
            if not basename[0:1].islower():
                continue
            if prefix and not path.startswith(prefix):
                continue
            entries.append({"path": path, "sha": item["sha"]})
        return entries

    def close(self) -> None:
        self._client.close()


def _is_rate_limited(r: httpx.Response) -> bool:
    if r.status_code == 429:
        return True
    if r.status_code == 403 and r.headers.get("x-ratelimit-remaining") == "0":
        return True
    return False


def _compute_wait(r: httpx.Response) -> float:
    retry_after = r.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), _MAX_RETRY_WAIT)
        except ValueError:
            pass
    reset = r.headers.get("x-ratelimit-reset")
    if reset:
        try:
            wait = max(float(reset) - time.time(), 0) + 1
            return min(wait, _MAX_RETRY_WAIT)
        except ValueError:
            pass
    return 5.0

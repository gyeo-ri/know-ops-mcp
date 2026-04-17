import base64

import httpx
import pytest
import respx

from know_ops_mcp.storage.backends.external.github import (
    GitHubStorage,
    parse_repo_url,
)

OWNER = "octo"
REPO = "notes"
TOKEN = "test-token"
BRANCH = "main"


@pytest.fixture
def storage():
    return GitHubStorage(
        f"https://github.com/{OWNER}/{REPO}",
        token=TOKEN,
        branch=BRANCH,
    )


@pytest.fixture
def storage_with_subdir():
    return GitHubStorage(
        f"https://github.com/{OWNER}/{REPO}",
        token=TOKEN,
        branch=BRANCH,
        subdirectory="kb",
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Skip the rate-limit retry sleep so tests run fast."""
    monkeypatch.setattr(
        "know_ops_mcp.storage.backends.external.github.time.sleep",
        lambda _seconds: None,
    )


def _contents_url(path: str) -> str:
    return f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"


def _trees_url() -> str:
    return f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{BRANCH}"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _contents_payload(path: str, content: str, sha: str = "deadbeef") -> dict:
    return {"path": path, "sha": sha, "content": _b64(content), "encoding": "base64"}


class TestParseRepoUrl:
    def test_basic(self):
        assert parse_repo_url("https://github.com/owner/repo") == ("owner", "repo")

    def test_with_git_suffix(self):
        assert parse_repo_url("https://github.com/owner/repo.git") == ("owner", "repo")

    def test_with_trailing_slash(self):
        assert parse_repo_url("https://github.com/owner/repo/") == ("owner", "repo")

    def test_with_extra_path_segments_kept(self):
        assert parse_repo_url("https://github.com/owner/repo/tree/main") == (
            "owner",
            "repo",
        )

    def test_www_subdomain_accepted(self):
        assert parse_repo_url("https://www.github.com/owner/repo") == (
            "owner",
            "repo",
        )

    def test_strips_whitespace(self):
        assert parse_repo_url("  https://github.com/owner/repo  ") == (
            "owner",
            "repo",
        )

    def test_rejects_non_github(self):
        with pytest.raises(ValueError, match="Not a github.com URL"):
            parse_repo_url("https://gitlab.com/owner/repo")

    def test_rejects_missing_repo(self):
        with pytest.raises(ValueError, match="missing owner/repo"):
            parse_repo_url("https://github.com/owner")


class TestRead:
    @respx.mock
    def test_returns_decoded_content(self, storage):
        respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("hello.md", "body")
            )
        )
        assert storage.read("hello") == "body"

    @respx.mock
    def test_404_returns_none(self, storage):
        respx.get(_contents_url("ghost.md")).mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        assert storage.read("ghost") is None

    @respx.mock
    def test_5xx_raises(self, storage):
        respx.get(_contents_url("oops.md")).mock(
            return_value=httpx.Response(500, json={"message": "Server Error"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("oops")

    @respx.mock
    def test_subdirectory_prefix_in_path(self, storage_with_subdir):
        respx.get(_contents_url("kb/topic.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("kb/topic.md", "body")
            )
        )
        assert storage_with_subdir.read("topic") == "body"

    @respx.mock
    def test_sends_branch_ref_query(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("hello.md", "body")
            )
        )
        storage.read("hello")
        assert dict(route.calls.last.request.url.params) == {"ref": BRANCH}

    @respx.mock
    def test_sends_authorization_header(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("hello.md", "body")
            )
        )
        storage.read("hello")
        assert route.calls.last.request.headers["authorization"] == f"Bearer {TOKEN}"


class TestWrite:
    @respx.mock
    def test_creates_new_when_absent(self, storage):
        respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        put_route = respx.put(_contents_url("hello.md")).mock(
            return_value=httpx.Response(201, json={})
        )

        storage.write("hello", "body")

        body = put_route.calls.last.request.read()
        import json as _json
        sent = _json.loads(body)
        assert sent["message"].startswith("Create")
        assert sent["branch"] == BRANCH
        assert "sha" not in sent
        assert base64.b64decode(sent["content"]).decode() == "body"

    @respx.mock
    def test_updates_existing_with_sha(self, storage):
        respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("hello.md", "old", sha="abc123")
            )
        )
        put_route = respx.put(_contents_url("hello.md")).mock(
            return_value=httpx.Response(200, json={})
        )

        storage.write("hello", "new")

        import json as _json
        sent = _json.loads(put_route.calls.last.request.read())
        assert sent["message"].startswith("Update")
        assert sent["sha"] == "abc123"
        assert base64.b64decode(sent["content"]).decode() == "new"

    @respx.mock
    def test_unicode_content_round_trips_base64(self, storage):
        respx.get(_contents_url("k.md")).mock(
            return_value=httpx.Response(404, json={})
        )
        put_route = respx.put(_contents_url("k.md")).mock(
            return_value=httpx.Response(201, json={})
        )

        storage.write("k", "한글 🚀")
        import json as _json
        sent = _json.loads(put_route.calls.last.request.read())
        assert base64.b64decode(sent["content"]).decode() == "한글 🚀"


class TestDelete:
    @respx.mock
    def test_deletes_present_returns_true(self, storage):
        respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                200, json=_contents_payload("hello.md", "body", sha="cafe")
            )
        )
        del_route = respx.delete(_contents_url("hello.md")).mock(
            return_value=httpx.Response(200, json={})
        )

        assert storage.delete("hello") is True
        import json as _json
        sent = _json.loads(del_route.calls.last.request.read())
        assert sent["sha"] == "cafe"
        assert sent["message"].startswith("Delete")
        assert sent["branch"] == BRANCH

    @respx.mock
    def test_absent_returns_false_without_delete_call(self, storage):
        respx.get(_contents_url("ghost.md")).mock(
            return_value=httpx.Response(404, json={})
        )
        del_route = respx.delete(_contents_url("ghost.md"))
        assert storage.delete("ghost") is False
        assert del_route.call_count == 0


class TestListVersions:
    def _tree_payload(self, entries: list[dict], truncated: bool = False) -> dict:
        return {"tree": entries, "truncated": truncated}

    @respx.mock
    def test_returns_name_to_sha(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200,
                json=self._tree_payload([
                    {"type": "blob", "path": "a.md", "sha": "sha-a"},
                    {"type": "blob", "path": "b.md", "sha": "sha-b"},
                ]),
            )
        )
        assert storage.list_versions() == {"a": "sha-a", "b": "sha-b"}

    @respx.mock
    def test_filters_non_md(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200,
                json=self._tree_payload([
                    {"type": "blob", "path": "a.md", "sha": "sha-a"},
                    {"type": "blob", "path": "readme.txt", "sha": "ignored"},
                    {"type": "tree", "path": "subdir", "sha": "ignored"},
                ]),
            )
        )
        assert storage.list_versions() == {"a": "sha-a"}

    @respx.mock
    def test_filters_nested_files_at_root(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200,
                json=self._tree_payload([
                    {"type": "blob", "path": "top.md", "sha": "sha-top"},
                    {"type": "blob", "path": "nested/inner.md", "sha": "ignored"},
                ]),
            )
        )
        assert storage.list_versions() == {"top": "sha-top"}

    @respx.mock
    def test_subdirectory_includes_only_direct_children(self, storage_with_subdir):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200,
                json=self._tree_payload([
                    {"type": "blob", "path": "kb/topic.md", "sha": "sha-topic"},
                    {"type": "blob", "path": "kb/sub/deeper.md", "sha": "ignored"},
                    {"type": "blob", "path": "other/x.md", "sha": "ignored"},
                ]),
            )
        )
        assert storage_with_subdir.list_versions() == {"topic": "sha-topic"}

    @respx.mock
    def test_truncated_response_raises(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200, json=self._tree_payload([], truncated=True)
            )
        )
        with pytest.raises(RuntimeError, match="exceeds GitHub Trees API"):
            storage.list_versions()

    @respx.mock
    def test_404_returns_empty_dict(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        assert storage.list_versions() == {}

    @respx.mock
    def test_sends_recursive_query(self, storage):
        route = respx.get(_trees_url()).mock(
            return_value=httpx.Response(200, json=self._tree_payload([]))
        )
        storage.list_versions()
        assert route.calls.last.request.url.params["recursive"] == "true"


class TestListAll:
    @respx.mock
    def test_combines_tree_and_per_entry_reads(self, storage):
        respx.get(_trees_url()).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tree": [
                        {"type": "blob", "path": "a.md", "sha": "sha-a"},
                        {"type": "blob", "path": "b.md", "sha": "sha-b"},
                    ],
                    "truncated": False,
                },
            )
        )
        respx.get(_contents_url("a.md")).mock(
            return_value=httpx.Response(200, json=_contents_payload("a.md", "body-a"))
        )
        respx.get(_contents_url("b.md")).mock(
            return_value=httpx.Response(200, json=_contents_payload("b.md", "body-b"))
        )
        assert storage.list_all() == {"a": "body-a", "b": "body-b"}


class TestRateLimitRetry:
    @respx.mock
    def test_retries_once_on_429(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            side_effect=[
                httpx.Response(429, headers={"retry-after": "0"}, json={}),
                httpx.Response(
                    200, json=_contents_payload("hello.md", "body")
                ),
            ]
        )
        assert storage.read("hello") == "body"
        assert route.call_count == 2

    @respx.mock
    def test_retries_once_on_403_with_remaining_zero(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            side_effect=[
                httpx.Response(
                    403,
                    headers={"x-ratelimit-remaining": "0", "retry-after": "0"},
                    json={"message": "rate limited"},
                ),
                httpx.Response(
                    200, json=_contents_payload("hello.md", "body")
                ),
            ]
        )
        assert storage.read("hello") == "body"
        assert route.call_count == 2

    @respx.mock
    def test_does_not_retry_403_with_remaining_nonzero(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(
                403,
                headers={"x-ratelimit-remaining": "5"},
                json={"message": "forbidden"},
            )
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("hello")
        assert route.call_count == 1

    @respx.mock
    def test_gives_up_after_single_retry(self, storage):
        route = respx.get(_contents_url("hello.md")).mock(
            return_value=httpx.Response(429, headers={"retry-after": "0"}, json={})
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("hello")
        assert route.call_count == 2

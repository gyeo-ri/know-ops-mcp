import base64
import json

import httpx
import pytest

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
    monkeypatch.setattr(
        "know_ops_mcp.storage.backends.external.github.time.sleep",
        lambda _seconds: None,
    )


def _contents_url(path: str, *, with_ref: bool = True) -> str:
    base = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    return f"{base}?ref={BRANCH}" if with_ref else base


def _trees_url() -> str:
    return (
        f"https://api.github.com/repos/{OWNER}/{REPO}"
        f"/git/trees/{BRANCH}?recursive=true"
    )


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
    def test_returns_decoded_content(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body"),
        )
        assert storage.read("hello") == "body"

    def test_404_returns_none(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("ghost.md"),
            status_code=404,
            json={"message": "Not Found"},
        )
        assert storage.read("ghost") is None

    def test_5xx_raises(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("oops.md"),
            status_code=500,
            json={"message": "Server Error"},
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("oops")

    def test_subdirectory_prefix_in_path(self, httpx_mock, storage_with_subdir):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("kb/topic.md"),
            json=_contents_payload("kb/topic.md", "body"),
        )
        assert storage_with_subdir.read("topic") == "body"

    def test_sends_branch_ref_query(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body"),
        )
        storage.read("hello")
        request = httpx_mock.get_request(method="GET")
        assert dict(request.url.params) == {"ref": BRANCH}

    def test_sends_authorization_header(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body"),
        )
        storage.read("hello")
        request = httpx_mock.get_request(method="GET")
        assert request.headers["authorization"] == f"Bearer {TOKEN}"


class TestWrite:
    def test_creates_new_when_absent(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=404,
            json={"message": "Not Found"},
        )
        httpx_mock.add_response(
            method="PUT",
            url=_contents_url("hello.md", with_ref=False),
            status_code=201,
            json={},
        )

        storage.write("hello", "body")

        put_request = httpx_mock.get_request(method="PUT")
        sent = json.loads(put_request.read())
        assert sent["message"].startswith("Create")
        assert sent["branch"] == BRANCH
        assert "sha" not in sent
        assert base64.b64decode(sent["content"]).decode() == "body"

    def test_updates_existing_with_sha(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "old", sha="abc123"),
        )
        httpx_mock.add_response(
            method="PUT",
            url=_contents_url("hello.md", with_ref=False),
            status_code=200,
            json={},
        )

        storage.write("hello", "new")

        put_request = httpx_mock.get_request(method="PUT")
        sent = json.loads(put_request.read())
        assert sent["message"].startswith("Update")
        assert sent["sha"] == "abc123"
        assert base64.b64decode(sent["content"]).decode() == "new"

    def test_unicode_content_round_trips_base64(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("k.md"),
            status_code=404,
            json={},
        )
        httpx_mock.add_response(
            method="PUT",
            url=_contents_url("k.md", with_ref=False),
            status_code=201,
            json={},
        )

        storage.write("k", "한글 🚀")
        put_request = httpx_mock.get_request(method="PUT")
        sent = json.loads(put_request.read())
        assert base64.b64decode(sent["content"]).decode() == "한글 🚀"


class TestDelete:
    def test_deletes_present_returns_true(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body", sha="cafe"),
        )
        httpx_mock.add_response(
            method="DELETE",
            url=_contents_url("hello.md", with_ref=False),
            status_code=200,
            json={},
        )

        assert storage.delete("hello") is True
        del_request = httpx_mock.get_request(method="DELETE")
        sent = json.loads(del_request.read())
        assert sent["sha"] == "cafe"
        assert sent["message"].startswith("Delete")
        assert sent["branch"] == BRANCH

    def test_absent_returns_false_without_delete_call(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("ghost.md"),
            status_code=404,
            json={},
        )
        assert storage.delete("ghost") is False
        assert httpx_mock.get_requests(method="DELETE") == []


class TestListVersions:
    def _tree_payload(self, entries: list[dict], truncated: bool = False) -> dict:
        return {"tree": entries, "truncated": truncated}

    def test_returns_name_to_sha(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([
                {"type": "blob", "path": "a.md", "sha": "sha-a"},
                {"type": "blob", "path": "b.md", "sha": "sha-b"},
            ]),
        )
        assert storage.list_versions() == {"a": "sha-a", "b": "sha-b"}

    def test_filters_non_md(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([
                {"type": "blob", "path": "a.md", "sha": "sha-a"},
                {"type": "blob", "path": "readme.txt", "sha": "ignored"},
                {"type": "tree", "path": "subdir", "sha": "ignored"},
            ]),
        )
        assert storage.list_versions() == {"a": "sha-a"}

    def test_filters_uppercase_md(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([
                {"type": "blob", "path": "entry.md", "sha": "sha-e"},
                {"type": "blob", "path": "README.md", "sha": "ignored"},
                {"type": "blob", "path": "sub/CONTRIBUTING.md", "sha": "ignored"},
            ]),
        )
        assert storage.list_versions() == {"entry": "sha-e"}

    def test_includes_nested_files_as_slash_keys(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([
                {"type": "blob", "path": "top.md", "sha": "sha-top"},
                {"type": "blob", "path": "nested/inner.md", "sha": "sha-inner"},
            ]),
        )
        assert storage.list_versions() == {
            "top": "sha-top",
            "nested/inner": "sha-inner",
        }

    def test_subdirectory_includes_nested_children(
        self, httpx_mock, storage_with_subdir
    ):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([
                {"type": "blob", "path": "kb/topic.md", "sha": "sha-topic"},
                {"type": "blob", "path": "kb/sub/deeper.md", "sha": "sha-deeper"},
                {"type": "blob", "path": "other/x.md", "sha": "ignored"},
            ]),
        )
        assert storage_with_subdir.list_versions() == {
            "topic": "sha-topic",
            "sub/deeper": "sha-deeper",
        }

    def test_truncated_response_raises(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([], truncated=True),
        )
        with pytest.raises(RuntimeError, match="exceeds GitHub Trees API"):
            storage.list_versions()

    def test_404_returns_empty_dict(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            status_code=404,
            json={"message": "Not Found"},
        )
        assert storage.list_versions() == {}

    def test_sends_recursive_query(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json=self._tree_payload([]),
        )
        storage.list_versions()
        request = httpx_mock.get_request(method="GET")
        assert request.url.params["recursive"] == "true"


class TestListAll:
    def test_combines_tree_and_per_entry_reads(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_trees_url(),
            json={
                "tree": [
                    {"type": "blob", "path": "a.md", "sha": "sha-a"},
                    {"type": "blob", "path": "b.md", "sha": "sha-b"},
                ],
                "truncated": False,
            },
        )
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("a.md"),
            json=_contents_payload("a.md", "body-a"),
        )
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("b.md"),
            json=_contents_payload("b.md", "body-b"),
        )
        assert storage.list_all() == {"a": "body-a", "b": "body-b"}


class TestRateLimitRetry:
    def test_retries_once_on_429(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=429,
            headers={"retry-after": "0"},
            json={},
        )
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body"),
        )
        assert storage.read("hello") == "body"
        assert len(httpx_mock.get_requests(method="GET")) == 2

    def test_retries_once_on_403_with_remaining_zero(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=403,
            headers={"x-ratelimit-remaining": "0", "retry-after": "0"},
            json={"message": "rate limited"},
        )
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            json=_contents_payload("hello.md", "body"),
        )
        assert storage.read("hello") == "body"
        assert len(httpx_mock.get_requests(method="GET")) == 2

    def test_does_not_retry_403_with_remaining_nonzero(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=403,
            headers={"x-ratelimit-remaining": "5"},
            json={"message": "forbidden"},
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("hello")
        assert len(httpx_mock.get_requests(method="GET")) == 1

    def test_gives_up_after_single_retry(self, httpx_mock, storage):
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=429,
            headers={"retry-after": "0"},
            json={},
        )
        httpx_mock.add_response(
            method="GET",
            url=_contents_url("hello.md"),
            status_code=429,
            headers={"retry-after": "0"},
            json={},
        )
        with pytest.raises(httpx.HTTPStatusError):
            storage.read("hello")
        assert len(httpx_mock.get_requests(method="GET")) == 2

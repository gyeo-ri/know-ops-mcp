from know_ops_mcp.storage import StorageService
from know_ops_mcp.storage.backends.internal.memory import MemoryStorage


class _Recorder(MemoryStorage):
    def __init__(self):
        super().__init__()
        self.refresh_calls: list[str | None] = []

    def refresh(self, name=None):
        self.refresh_calls.append(name)


class _NoRefresh(MemoryStorage):
    pass


class TestPassthrough:
    def test_read_write_delete_list_delegate(self):
        backend = MemoryStorage()
        svc = StorageService(backend)
        svc.write("a", "body-a")
        svc.write("b", "body-b")
        assert svc.read("a") == "body-a"
        assert svc.list_all() == {"a": "body-a", "b": "body-b"}
        assert svc.delete("a") is True
        assert svc.delete("a") is False
        assert svc.read("a") is None


class TestRefresh:
    def test_calls_backend_refresh_when_present(self):
        backend = _Recorder()
        svc = StorageService(backend)
        svc.refresh()
        svc.refresh("alpha")
        assert backend.refresh_calls == [None, "alpha"]

    def test_no_op_when_backend_lacks_refresh(self):
        svc = StorageService(_NoRefresh())
        svc.refresh()
        svc.refresh("alpha")


class TestConfigure:
    def test_swaps_backend(self):
        first = MemoryStorage()
        second = MemoryStorage()
        svc = StorageService(first)
        svc.write("a", "in-first")
        svc.configure(second)
        assert svc.read("a") is None
        svc.write("a", "in-second")
        assert second.read("a") == "in-second"
        assert first.read("a") == "in-first"

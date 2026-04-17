"""Storage backend abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    def read(self, name: str) -> str | None:
        ...

    @abstractmethod
    def write(self, name: str, content: str) -> None:
        ...

    @abstractmethod
    def delete(self, name: str) -> bool:
        ...

    @abstractmethod
    def list_all(self) -> dict[str, str]:
        ...

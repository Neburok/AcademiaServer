from abc import ABC, abstractmethod


class SearchEngine(ABC):
    @abstractmethod
    def search(self, notes: list[dict], query: str) -> list[dict]:
        raise NotImplementedError

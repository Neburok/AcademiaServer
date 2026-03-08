from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def analyze_message(self, text: str, context: list[str] = [], memory: list[dict] = []) -> dict:
        raise NotImplementedError

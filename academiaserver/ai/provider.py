from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def analyze_message(self, text: str) -> dict:
        raise NotImplementedError

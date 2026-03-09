from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def analyze_message(
        self,
        text: str,
        context: list[str] = [],
        memory: list[dict] = [],
        system_prompt_override: str | None = None,
    ) -> dict:
        raise NotImplementedError

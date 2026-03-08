from app.config.settings import settings


class LLMClient:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key

    def ready(self) -> bool:
        return bool(self.api_key)

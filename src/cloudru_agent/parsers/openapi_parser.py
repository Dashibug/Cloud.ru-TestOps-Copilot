from pathlib import Path
from cloudru_agent.models.requirements import ApiRequirementsDocument


class OpenApiParser:
    """
    Заглушка парсера OpenAPI.
    На MVP для UI генерации он не используется, но нужен, чтобы модуль корректно импортировался.
    """

    def to_requirements(self, path: Path) -> ApiRequirementsDocument:
        # TODO: позже здесь будет реальный парсинг OpenAPI 3.0
        return ApiRequirementsDocument(service="Evolution Compute API v3", operations=[])

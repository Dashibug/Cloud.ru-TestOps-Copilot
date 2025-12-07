from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from cloudru_agent.models.requirements import UiRequirementsDocument, UiRequirement
from cloudru_agent.llm.evolution_client import EvolutionClient

class UiRequirementsParser:
    """
   - parse(path): читает YAML с уже структурированными требованиями.
    Ожидает структуру:
    feature: "..."
    requirements:
      - id: "REQ_..."
        block: "BLOCK_..."
        title: "..."
        description: "..."
        priority: "CRITICAL" | "NORMAL" | "LOW"

    - parse_text_with_llm(text): просит Evolution FM распарсить сырой текст
    """

    def parse(self, path: Path) -> UiRequirementsDocument:
        raw: Dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))

        feature = raw.get("feature", "Cloud.ru Price Calculator")
        req_items = raw.get("requirements", [])

        requirements = [UiRequirement(**item) for item in req_items]
        return UiRequirementsDocument(feature=feature, requirements=requirements)

    def parse_text_with_llm(
            self,
            text: str,
            llm: Optional[EvolutionClient] = None,
    ) -> UiRequirementsDocument:
        """
        Использует Evolution FM для преобразования текста в UiRequirementsDocument.
        """
        client = llm or EvolutionClient()
        return client.ui_requirements_from_text(text)

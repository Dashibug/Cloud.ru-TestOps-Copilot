from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from cloudru_agent.models.requirements import ApiRequirement, ApiRequirementsDocument


class OpenApiParser:
    """
    Парсер OpenAPI 3.0 -> ApiRequirementsDocument.

    Берём из спеки только то, что нужно для генерации тестов:
    метод, путь, summary, теги и коды ответов.
    """

    def parse_file(self, path: str | Path) -> ApiRequirementsDocument:
        text = Path(path).read_text(encoding="utf-8")
        return self.parse_text(text)

    def parse_text(self, text: str) -> ApiRequirementsDocument:
        """
        Универсальный вход: сюда можно передать содержимое yaml/json
        (то, что прилетело из файла в Streamlit).
        """
        try:
            data = yaml.safe_load(text)
        except Exception:
            data = json.loads(text)
        return self._parse_dict(data)

    # --- внутренности ---

    def _parse_dict(self, data: Dict[str, Any]) -> ApiRequirementsDocument:
        feature = data.get("info", {}).get("title", "Evolution Compute API v3")
        servers = data.get("servers") or []
        if servers and isinstance(servers, list):
            base_url = servers[0].get("url", "https://compute.api.cloud.ru")
        else:
            base_url = "https://compute.api.cloud.ru"

        requirements: List[ApiRequirement] = []

        paths = data.get("paths") or {}
        for path, path_item in paths.items():
            for method in ("get", "post", "put", "patch", "delete"):
                op = path_item.get(method)
                if not op:
                    continue

                section = self._infer_section(op.get("tags") or [], path)
                # по условиям кейса 2 нас интересуют только VMs / Disks / Flavors
                if section not in ("VMs", "Disks", "Flavors"):
                    continue

                summary = (
                    op.get("summary")
                    or op.get("description")
                    or f"{method.upper()} {path}"
                )
                operation_id = op.get("operationId")

                responses = op.get("responses") or {}
                success_code = self._pick_success_code(responses)
                error_codes = [
                    int(code)
                    for code in responses.keys()
                    if str(code).startswith(("4", "5"))
                ]

                req_id = self._make_requirement_id(section, method, path, operation_id)
                priority = (
                    "CRITICAL"
                    if method in ("post", "delete", "put", "patch")
                    else "NORMAL"
                )

                requirements.append(
                    ApiRequirement(
                        id=req_id,
                        section=section,
                        method=method.upper(),
                        path=path,
                        summary=summary,
                        priority=priority,
                        tag=(op.get("tags") or [None])[0],
                        operation_id=operation_id,
                        success_code=success_code,
                        error_codes=error_codes,
                    )
                )

        return ApiRequirementsDocument(
            feature=feature,
            base_url=base_url,
            requirements=requirements,
        )

    @staticmethod
    def _infer_section(tags: List[str], path: str) -> str:
        """
        Определяем блок тестирования из тегов/пути:
        - VMs   — операции с виртуальными машинами
        - Disks — операции с дисками
        - Flavors — конфигурации инстансов
        """
        joined_tags = " ".join(tags).lower()
        path_lower = path.lower()

        if "vm" in joined_tags or "/vms" in path_lower:
            return "VMs"
        if "disk" in joined_tags or "/disks" in path_lower:
            return "Disks"
        if "flavor" in joined_tags or "/flavors" in path_lower:
            return "Flavors"
        return "Other"

    @staticmethod
    def _pick_success_code(responses: Dict[str, Any]) -> int:
        # сначала пытаемся взять один из "классических" кодов успеха
        for candidate in ("200", "201", "202", "204"):
            if candidate in responses:
                return int(candidate)
        # потом — первый неошибочный код
        for code in responses.keys():
            try:
                code_int = int(code)
            except (TypeError, ValueError):
                continue
            if code_int < 400:
                return code_int
        # запасной вариант
        return 200

    @staticmethod
    def _make_requirement_id(
        section: str, method: str, path: str, operation_id: str | None
    ) -> str:
        if operation_id:
            base = operation_id
        else:
            base = f"{section}_{method}_{path}"
        base = base.upper()
        base = re.sub(r"[^A-Z0-9]+", "_", base)
        return f"API_{base}".strip("_")

from typing import List, Optional
from pydantic import BaseModel


class UiRequirement(BaseModel):
    id: str
    block: str
    title: str
    description: Optional[str] = None
    priority: str = "NORMAL"  # CRITICAL / NORMAL / LOW


class UiRequirementsDocument(BaseModel):
    feature: str = "Cloud.ru Price Calculator"
    requirements: List[UiRequirement]


class ApiRequirement(BaseModel):
    """
    Описание одного API-требования (эндпоинта).
    """
    id: str                     # уникальный ID кейса, например API_VMS_GET_LIST
    section: str                # 'VMs', 'Disks', 'Flavors'
    method: str                 # GET / POST / PUT / DELETE ...
    path: str                   # /v3/vms, /v3/disks/{id}, ...
    summary: str                # человекочитаемое название операции
    priority: str = "NORMAL"    # CRITICAL / NORMAL / LOW
    tag: Optional[str] = None   # первый tag из OpenAPI, если есть
    operation_id: Optional[str] = None
    success_code: int = 200     # ожидаемый успешный статус
    error_codes: List[int] = [] # список 4xx/5xx, если есть в спецификации


class ApiRequirementsDocument(BaseModel):
    """
    Набор требований по API (из OpenAPI-спеки).
    """
    feature: str                # например "Evolution Compute API v3"
    base_url: str               # https://compute.api.cloud.ru
    requirements: List[ApiRequirement]


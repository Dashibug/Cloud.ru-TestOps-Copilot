from typing import List, Optional
from pydantic import BaseModel


class UiRequirement(BaseModel):
    id: str
    block: str          # например "BLOCK_1_START_PAGE"
    title: str          # текст требования
    description: Optional[str] = None
    priority: str = "NORMAL"  # CRITICAL / NORMAL / LOW


class UiRequirementsDocument(BaseModel):
    feature: str = "Cloud.ru Price Calculator"
    requirements: List[UiRequirement]


class ApiOperationRequirement(BaseModel):
    id: str             # например "VM_CREATE_SUCCESS"
    resource: str       # VMs / Disks / Flavors
    method: str
    path: str
    scenario: str       # "успешное создание VM"
    priority: str = "NORMAL"


class ApiRequirementsDocument(BaseModel):
    service: str = "Evolution Compute API v3"
    operations: List[ApiOperationRequirement]

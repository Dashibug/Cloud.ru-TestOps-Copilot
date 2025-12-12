from typing import List
from pydantic import BaseModel


class CoverageEntry(BaseModel):
    scope: str          # например UI или API
    total_tests: int
    files: List[str]


class CoverageReport(BaseModel):
    root_dir: str
    entries: List[CoverageEntry]

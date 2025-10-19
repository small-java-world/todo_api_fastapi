from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ArtifactCreate(BaseModel):
    content: str  # Base64エンコードされたコンテンツ
    media_type: str
    source_task_hid: Optional[str] = None
    purpose: Optional[str] = None


class ArtifactInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sha256: str
    media_type: str
    bytes_size: int
    created_at: datetime
    source_task_hid: Optional[str] = None
    purpose: Optional[str] = None
    cas_uri: str
    cas_path: str


class TaskArtifactLinkCreate(BaseModel):
    sha256_hash: str
    role: str  # spec, prompt, test, build, log, patch, artifact


class TaskArtifactLink(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_hid: str
    role: str
    created_at: datetime
    artifact: ArtifactInfo


class ArtifactRetrieve(BaseModel):
    sha256_hash: str


class TaskSummaryCreate(BaseModel):
    task_hid: str
    summary_140: str
    acceptance_json: Optional[Dict[str, Any]] = None


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_hid: str
    summary_140: str
    acceptance_json: Optional[Dict[str, Any]] = None
    updated_at: datetime


class OutlineCard(BaseModel):
    hierarchical_id: str
    title: str
    summary: str
    acceptance: List[str]
    depends_on: List[str]
    uris: Dict[str, str]  # spec, tests_dir, context_pack等のURI

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LeaseQAResponse(_Base):
    answer: str

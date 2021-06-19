from pydantic import BaseModel
from typing import Optional


class Policy(BaseModel):
    source: str
    name: Optional[str]
    target: int
    query: Optional[str]
    config: Optional[dict]

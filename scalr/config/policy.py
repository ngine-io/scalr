from pydantic import BaseModel
from typing import Optional


class PolicyConfig(BaseModel):
    name: str
    target: int
    query: Optional[str]
    config: Optional[dict]

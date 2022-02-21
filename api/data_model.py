"""Model containing pydandic models, used as data schemas for the REST api (see main.py)"""
from pydantic import BaseModel

class InData(BaseModel):
    duration: int
    a: float
    b: float
    wait: int | None = None

class OutResponse(BaseModel):
    status: str | None = None
    result: str | None = None
    task_id: str | None = None
    full_traceback: str | None = None
    url: str | None = None
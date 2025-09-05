from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TelemetryIn(BaseModel):
    x: float; y: float; z: float
    slope: Optional[float] = None
    tag: Optional[str] = None

class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; x: float; y: float; z: float
    slope: Optional[float] = None
    tag: Optional[str] = None
    ts: datetime

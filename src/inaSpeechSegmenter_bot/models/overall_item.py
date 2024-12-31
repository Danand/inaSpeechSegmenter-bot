from pydantic import BaseModel

class OverallItem(BaseModel):
    label: str
    ratio: float

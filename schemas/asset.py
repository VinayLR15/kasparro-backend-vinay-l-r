from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RawAssetSchema(BaseModel):
    source: str
    record_id: str
    payload: Dict[str, Any]

class AssetSchema(BaseModel):
    external_id: str = Field(...)
    symbol: Optional[str]
    name: Optional[str]
    source: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

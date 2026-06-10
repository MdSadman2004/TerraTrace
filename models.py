from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DeedEntity(BaseModel):
    grantor: str = Field(..., description="Seller/Transferor of the property")
    grantee: str = Field(..., description="Buyer/Transferee of the property")
    price: float = Field(default=0.0, description="Purchase transaction amount")
    year: int = Field(..., description="Year the transaction occurred")

class CovenantRestriction(BaseModel):
    restriction_type: str = Field(..., description="Type of covenant or restriction (e.g. Utility, Height)")
    description: str = Field(..., description="Detail description of restriction")
    year: int = Field(..., description="Year restriction was registered")

class TitleVerification(BaseModel):
    is_complete: bool = Field(..., description="True if no gaps exist in chain of title")
    ownership_flow: List[str] = Field(default=[], description="Chronological owner transfers")
    discrepancies: List[str] = Field(default=[], description="Description of any ownership gaps")

class ZoningAssessment(BaseModel):
    height_limit: Optional[float] = Field(default=None, description="Max building height in feet")
    commercial_allowed: bool = Field(default=True, description="False if zoning prohibits business operations")
    easements: List[str] = Field(default=[], description="List of easements on land")

class TitleReport(BaseModel):
    metadata: Dict[str, Any] = Field(default={}, description="General indexing metadata")
    history: List[DeedEntity] = Field(..., description="Chronological transaction record list")
    restrictions: List[CovenantRestriction] = Field(default=[], description="Aggregated restrictions list")
    verification: TitleVerification = Field(..., description="Title succession results")
    zoning: ZoningAssessment = Field(..., description="Zoning compliance results")

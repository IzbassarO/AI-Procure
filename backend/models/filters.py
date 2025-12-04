from pydantic import BaseModel
from typing import Optional, Literal, List

class DateRange(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None

class TenderFilters(BaseModel):
    category: Optional[List[str]] = None
    method: Optional[List[str]] = None
    purchaseType: Optional[List[str]] = None
    status: Optional[List[str]] = None
    features: Optional[List[str]] = None
    dateRange: Optional[DateRange] = None

    amountSort: Optional[Literal["asc", "desc"]] = None

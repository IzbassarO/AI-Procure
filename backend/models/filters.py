# backend/models/filters.py
from pydantic import BaseModel
from typing import Optional, Literal, List

class DateRange(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None

class TenderFilters(BaseModel):
    # теперь это СПИСКИ (мульти-фильтры)
    category: Optional[List[str]] = None          # Общие_Вид предмета закупок
    method: Optional[List[str]] = None            # Общие_Способ проведения закупки
    purchaseType: Optional[List[str]] = None      # Общие_Тип закупки
    status: Optional[List[str]] = None            # Детали_Статус объявления
    features: Optional[List[str]] = None          # Общие_Признаки
    dateRange: Optional[DateRange] = None

    amountSort: Optional[Literal["asc", "desc"]] = None

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TradingDate(BaseModel):
    trading_date: datetime

    class Config:
        from_attributes = True

class TradingResult(BaseModel):
    id: int
    trading_date: datetime
    oil_id: int
    delivery_type_id: int
    delivery_basis_id: int
    volume: float
    price: float
    total_value: float

    class Config:
        from_attributes = True

class TradingDynamics(TradingResult):
    pass 

class LastTradingDatesResponse(BaseModel):
    dates: List[datetime]
    total: int

class TradingDynamicsResponse(BaseModel):
    result: List[TradingDynamics]
    total: int
    start_date: datetime
    end_date: datetime

class TradingResultsResponse(BaseModel):
    result: List[TradingResult]
    total: int
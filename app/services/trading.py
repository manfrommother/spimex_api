from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import SpimexTradingResult


class TradingService:
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_last_trading_dates(self, limit:int=10) -> List[datetime]:
        '''
        Получаем список последних торговых дат

        Args:
            limit: Кол-во последних дат для получения

        Returns:
            List[datetime]: Список дат в порядке убывания
        '''
        query = (
            select(SpimexTradingResult.trading_date)
            .distinct()
            .order_by(desc(SpimexTradingResult.trading_date))
            .limit(limit)
        )

        result = await self.session.execute(query)
        dates = result.scalars().all()
        return dates
    
    async def get_dynamics(
            self,
            start_date: datetime,
            end_date:datetime,
            oil_id: Optional[int]=None,
            delivery_type_id: Optional[int]=None,
            delivery_basis_id: Optional[int]=None
    ) -> List[SpimexTradingResult]:
        '''Получает данные о торгах за указанный период с фильтрацией.
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            oil_id: ID типа нефтепродукта (опционально)
            delivery_type_id: ID типа поставки (опционально)
            delivery_basis_id: ID базиса поставки (опционально)
            
        Returns:
            List[SpimexTradingResults]: Список результатов торгов
        '''
        query = (
            select(SpimexTradingResult)
            .where(SpimexTradingResult.trading_date.between(start_date, end_date))
            .order_by(desc(SpimexTradingResult.trading_date))
        )

        if oil_id is not None:
            query = query.where(SpimexTradingResult.oil_id == oil_id)
        if delivery_type_id is not None:
            query = query.where(SpimexTradingResult.delivery_type_id == delivery_type_id)
        if delivery_basis_id is not None:
            query = query.where(SpimexTradingResult.delivery_basis_id == delivery_basis_id)

        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_trading_result(
            self,
            oil_id:Optional[int]=None,
            delivery_type_id:Optional[int]=None,
            delivery_basis_id:Optional[int]=None,
            limit:int=100
    ) -> List[SpimexTradingResult]:
        '''
        Получает последние результаты торгов с фильтрацией.
        
        Args:
            oil_id: ID типа нефтепродукта (опционально)
            delivery_type_id: ID типа поставки (опционально)
            delivery_basis_id: ID базиса поставки (опционально)
            limit: Ограничение количества записей
            
        Returns:
            List[SpimexTradingResults]: Список последних результатов торгов
        '''
        query = (
            select(SpimexTradingResult)
            .order_by(desc(SpimexTradingResult.trading_date))
            .limit(limit)
        )

        if oil_id is not None:
            query = query.where(SpimexTradingResult.oil_id == oil_id)
        if delivery_type_id is not None:
            query = query.where(SpimexTradingResult.delivery_type_id == delivery_type_id)
        if delivery_basis_id is not None:
            query = query.where(SpimexTradingResult.delivery_basis_id == delivery_basis_id)

        result = await self.session.execute(query)
        return result.scalars().all()
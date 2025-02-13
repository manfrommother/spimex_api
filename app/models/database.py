from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SpimexTradingResult(Base):
    __tablename__ = 'spimex_tradinf_result'

    id = Column(Integer, primary_key=True, index=True)
    trading_date = Column(DateTime, nullable=False, index=True)
    oil_id = Column(Integer, nullable=False, index=True)
    delivery_type_id = Column(Integer, nullable=False, index=True)
    delivery_basis_id = Column(Integer, nullable=False, index=True)
    volume = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
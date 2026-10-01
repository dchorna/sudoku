# model/record.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from model.database import Base


class Record(Base):
    """Кожна зарахована перемога: хто, в якому режимі/рівні і за скільки секунд."""
    __tablename__ = 'game_records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    mode = Column(String(20), nullable=False, index=True)   
    level = Column(String(10), nullable=False)              
    seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
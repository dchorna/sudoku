from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from model.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    
    classic_easy_wins = Column(Integer, default=0, nullable=False)
    classic_medium_wins = Column(Integer, default=0, nullable=False)
    classic_hard_wins = Column(Integer, default=0, nullable=False)
    
    consecutive_easy_wins = Column(Integer, default=0, nullable=False)
    consecutive_medium_wins = Column(Integer, default=0, nullable=False)
    consecutive_hard_wins = Column(Integer, default=0, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
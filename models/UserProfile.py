from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    broker = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    exchanges = Column(ARRAY(String), nullable=True)        # Example: ['NSE', 'BSE']
    is_active = Column(Boolean, default=True)
    order_types = Column(ARRAY(String), nullable=True)      # Example: ['MARKET', 'LIMIT']
    poa = Column(Boolean, default=False)                    # Power of Attorney (True/False)
    products = Column(ARRAY(String), nullable=True)         # Example: ['CNC', 'MIS']
    user_id = Column(String(100), nullable=False)
    user_name = Column(String(150), nullable=False)
    user_type = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<UserProfile(id={self.id}, broker='{self.broker}', email='{self.email}')>"

    def to_dict(self):
        return {
            "id" : self.id,
            "broker" : self.broker,
            "email" : self.email,
            "exchanges" : self.exchanges,
            "is_active" : self.is_active,
            "order_types" : self.order_types,
            "poa" : self.poa,
            "products" : self.products,
            "user_id" : self.user_id,
            "user_name" : self.user_name,
            "user_type" : self.user_type,
            "created_on" : self.created_on
        }
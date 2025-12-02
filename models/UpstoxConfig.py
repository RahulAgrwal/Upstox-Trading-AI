from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,Float
from sqlalchemy.dialects.postgresql import ARRAY

class UpstoxConfig(Base):
    __tablename__ = "upstox_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())

    api_key = Column(String, nullable=False)
    api_secret = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)  # BUY / SELL
    access_token = Column(String, nullable=False)         # MARKET / LIMIT
    updated_on = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UpstoxConfig(api_key='{self.api_key}', api_secret='{self.api_secret}', redirect_uri='{self.redirect_uri}')>"

    def to_dict(self):
        """Return model instance as dictionary"""
        return {
            "id": self.id,
            "created_on": self.id,
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "redirect_uri": self.redirect_uri,
            "access_token": self.access_token,
            "updated_on": self.updated_on
        }
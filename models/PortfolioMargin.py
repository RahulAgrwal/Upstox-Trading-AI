
from database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, func

class PortfolioMargin(Base):
    __tablename__ = "portfolio_margin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(100))
    user_name = Column(String(150))
    available_margin = Column(Float, default=0.0)
    adhoc_margin = Column(Float, default=0.0)
    exposure_margin = Column(Float, default=0.0)
    notional_cash = Column(Float, default=0.0)
    payin_amount = Column(Float, default=0.0)
    span_margin = Column(Float, default=0.0)
    used_margin = Column(Float, default=0.0)

    def __repr__(self):
        return f"<PortfolioMargin(id={self.id}, available_margin='{self.available_margin}', created_on='{self.created_on}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "adhoc_margin": self.adhoc_margin,
            "available_margin": self.available_margin,
            "exposure_margin": self.exposure_margin,
            "notional_cash": self.notional_cash,
            "payin_amount": self.payin_amount,
            "span_margin": self.span_margin,
            "used_margin": self.used_margin,
            "created_on": self.created_on
        }
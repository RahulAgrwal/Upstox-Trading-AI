from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func,Float
from sqlalchemy.dialects.postgresql import ARRAY

class BrokerageCharges(Base):
    __tablename__ = "brokerage_charges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())

    order_id = Column(String, nullable=False)
    instrument_key = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)  # BUY / SELL
    order_type = Column(String, nullable=False)         # MARKET / LIMIT
    price = Column(Float, nullable=False)
    product = Column(String, nullable=False)            # e.g., 'I' (Intraday)
    validity = Column(String, default="DAY")            # Order validity (e.g., DAY, IOC)


    # Charges Breakdown
    total_charges = Column(Float, default=0.0)
    brokerage_charges = Column(Float, default=0.0)

    # Taxes
    gst = Column(Float, default=0.0)
    stt = Column(Float, default=0.0)
    stamp_duty = Column(Float, default=0.0)
    # Trancation
    transaction = Column(Float, default=0.0)
    clearing = Column(Float, default=0.0)
    sebi_turnover = Column(Float, default=0.0)

    
    # DP Plan Information
    dp_plan_name = Column(String, nullable=True)
    dp_plan_min_expense = Column(Float, default=0.0)

    def __repr__(self):
        return f"<BrokerageCharges(order_id='{self.order_id}', instrument_key='{self.instrument_key}', transaction_type='{self.transaction_type}', total_charges={self.total_charges})>"

    def to_dict(self):
        """Return model instance as dictionary"""
        return {
            "order_id": self.order_id,
            "instrument_key": self.instrument_key,
            "quantity": self.quantity,
            "transaction_type": self.transaction_type,
            "order_type": self.order_type,
            "price": self.price,
            "product": self.product,
            "validity": self.validity,
            "total_charges": self.total_charges,
            "brokerage_charges": self.brokerage_charges,
            "gst": self.gst,
            "stt": self.stt,
            "stamp_duty": self.stamp_duty,
            "transaction": self.transaction,
            "clearing": self.clearing,
            "sebi_turnover": self.sebi_turnover,
            "dp_plan_name": self.dp_plan_name,
            "dp_plan_min_expense": self.dp_plan_min_expense,
        }
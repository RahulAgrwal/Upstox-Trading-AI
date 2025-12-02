from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, func
from database import Base

class OrderDetails(Base):
    __tablename__ = "order_details"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String, nullable=True)
    update_type = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    instrument_token = Column(String, nullable=True)
    instrument_key = Column(String, nullable=True)
    trading_symbol = Column(String, nullable=True)
    product = Column(String, nullable=True)
    order_type = Column(String, nullable=True)
    average_price = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    trigger_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    disclosed_quantity = Column(Integer, nullable=True)
    pending_quantity = Column(Integer, nullable=True)
    transaction_type = Column(String, nullable=True)
    order_ref_id = Column(String, nullable=True)
    exchange_order_id = Column(String, nullable=True)
    parent_order_id = Column(String, nullable=True)
    validity = Column(String, nullable=True)
    status = Column(String, nullable=True)
    is_amo = Column(Boolean, nullable=True)
    variety = Column(String, nullable=True)
    tag = Column(String, nullable=True)
    exchange_timestamp = Column(String, nullable=True)
    status_message = Column(Text, nullable=True)
    order_request_id = Column(String, nullable=True)
    order_timestamp = Column(String, nullable=True)
    filled_quantity = Column(Integer, nullable=True)
    guid = Column(String, nullable=True)
    placed_by = Column(String, nullable=True)
    status_message_raw = Column(Text, nullable=True)
    total_charges = Column(Float, nullable=True)
    brokerage_charges = Column(Float, nullable=True)
    gst = Column(Float, nullable=True)
    stt = Column(Float, nullable=True)
    stamp_duty = Column(Float, nullable=True)
    transaction = Column(Float, nullable=True)
    clearing = Column(Float, nullable=True)
    sebi_turnover = Column(Float, nullable=True)
    dp_plan_name = Column(String, nullable=True)
    dp_plan_min_expense = Column(Float, nullable=True)

    def to_dict(self):
        """Return model instance as dictionary"""
        return {
            "id" :  self.id,
            "order_id": self.order_id,
            "update_type": self.update_type,
            "user_id": self.user_id,
            "exchange": self.exchange,
            "instrument_token": self.instrument_token,
            "instrument_key": self.instrument_key,
            "trading_symbol": self.trading_symbol,
            "product": self.product,
            "order_type": self.order_type,
            "average_price": self.average_price,
            "price": self.price,
            "trigger_price": self.trigger_price,
            "quantity": self.quantity,
            "disclosed_quantity": self.disclosed_quantity,
            "pending_quantity": self.pending_quantity,
            "transaction_type": self.transaction_type,
            "order_ref_id": self.order_ref_id,
            "exchange_order_id": self.exchange_order_id,
            "parent_order_id": self.parent_order_id,
            "validity": self.validity,
            "status": self.status,
            "is_amo": self.is_amo,
            "variety": self.variety,
            "tag": self.tag,
            "exchange_timestamp": self.exchange_timestamp,
            "status_message": self.status_message,
            "order_request_id": self.order_request_id,
            "order_timestamp": self.order_timestamp,
            "filled_quantity": self.filled_quantity,
            "guid": self.guid,
            "placed_by": self.placed_by,
            "status_message_raw": self.status_message_raw,
            "created_on": self.created_on,
            "total_charges": self.total_charges,
            "brokerage_charges": self.brokerage_charges,
            "gst": self.gst,
            "stt": self.stt,
            "stamp_duty": self.stamp_duty,
            "transaction": self.transaction,
            "clearing": self.clearing,
            "sebi_turnover": self.sebi_turnover,
            "dp_plan_name": self.dp_plan_name,
            "dp_plan_min_expense": self.dp_plan_min_expense
        }

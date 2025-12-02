from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel
from typing import Optional

from database import Base


class LLMDecision(Base):
    """
    ORM Model to store LLM trading decisions.
    """
    __tablename__ = "llm_decision"

    id = Column(Integer, primary_key=True, index=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    request = Column(JSONB, nullable=True)
    thought = Column(String, nullable=True)
    action = Column(String(10), nullable=True)  # BUY / SELL / HOLD
    instrument_key = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    cost_info_model = Column(String, nullable=True)
    cost_info_prompt_tokens = Column(Integer, nullable=True)
    cost_info_cached_tokens = Column(Integer, nullable=True)
    cost_info_completion_tokens = Column(Integer, nullable=True)
    cost_info_billable_prompt = Column(Float, nullable=True)
    cost_info_billable_completion = Column(Float, nullable=True)    
    cost_info_cost_usd = Column(Float, nullable=True)
    cost_info_cost_inr = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "request": self.request,
            "thought": self.thought,
            "action": self.action,
            "instrument_key": self.instrument_key,
            "confidence_score": self.confidence_score,
            "current_price": self.current_price,
            "cost_info_model": self.cost_info_model,
            "cost_info_prompt_tokens": self.cost_info_prompt_tokens,
            "cost_info_cached_tokens": self.cost_info_cached_tokens,
            "cost_info_completion_tokens": self.cost_info_completion_tokens,
            "cost_info_billable_prompt": self.cost_info_billable_prompt,
            "cost_info_billable_completion": self.cost_info_billable_completion,
            "cost_info_cost_usd": self.cost_info_cost_usd,
            "cost_info_cost_inr": self.cost_info_cost_inr,
            "created_on": self.created_on.isoformat() if self.created_on else None
        }


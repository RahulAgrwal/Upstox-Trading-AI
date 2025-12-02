from datetime import date, datetime
from config import AGENT_CONFIG
from models.BorkerageCharges import BrokerageCharges
from models.LLMDecision import LLMDecision
from models.OrderDetails import OrderDetails
from models.PortfolioMargin import PortfolioMargin
from models.UserProfile import UserProfile
from logger_config import get_logger
from database import Base, engine, SessionLocal
logger = get_logger(__name__)

class PostgresDatabase:
    """
    A helper class to manage PostgreSQL database operations.
    """

    def __init__(self):
        # Create tables for all models
        Base.metadata.create_all(engine)
        logger.info("✅ Database connection established and tables created (if not exist).")
        self.SessionLocal = SessionLocal
    # -------- CRUD Function --------
    def save_portfolio_margin(self, portfolio_margin: dict):
        db = self.SessionLocal()
        try:
            new_portfolio = PortfolioMargin(
                adhoc_margin=portfolio_margin.get('adhoc_margin', 0.0),
                available_margin=portfolio_margin.get('available_margin', 0.0),
                exposure_margin=portfolio_margin.get('exposure_margin', 0.0),
                notional_cash=portfolio_margin.get('notional_cash', 0.0),
                payin_amount=portfolio_margin.get('payin_amount', 0.0),
                span_margin=portfolio_margin.get('span_margin', 0.0),
                used_margin=portfolio_margin.get('used_margin', 0.0),
                user_id=portfolio_margin.get('user_id', ''),
                user_name=portfolio_margin.get('user_name', ''),
            )
            db.add(new_portfolio)
            db.commit()
            db.refresh(new_portfolio)
            logger.info(f"✅ Portfolio margin saving successfully (id={new_portfolio.id})")
            return new_portfolio
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving portfolio margin: {e}")
        finally:
            db.close()

    def save_user_details(self, user_details: dict):
        db = self.SessionLocal()
        try:
            obj = UserProfile(
                broker=user_details.get('broker'),
                email=user_details.get('email'),
                exchanges=user_details.get('exchanges'),
                is_active=user_details.get('is_active', True),
                order_types=user_details.get('order_types'),
                poa=user_details.get('poa', False),
                products=user_details.get('products'),
                user_id=user_details.get('user_id'),
                user_name=user_details.get('user_name'),
                user_type=user_details.get('user_type'),
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            logger.info(f"✅ User details added successfully (user_name={obj.user_name})")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving user details: {e}")
        finally:
            db.close()

    def save_brokerage_charges(self, brokerage_details: dict):
        db = self.SessionLocal()
        try:
            obj = BrokerageCharges(
                order_id=brokerage_details.get('order_id'),
                instrument_key=brokerage_details.get('instrument_key'),
                quantity=brokerage_details.get('quantity'),
                transaction_type=brokerage_details.get('transaction_type'),
                order_type=brokerage_details.get('order_type'),
                price=brokerage_details.get('price'),
                product=brokerage_details.get('product'),
                validity=brokerage_details.get('validity'),
                total_charges=brokerage_details.get('total_charges'),
                brokerage_charges=brokerage_details.get('brokerage_charges'),
                gst=brokerage_details.get('gst'),
                stt=brokerage_details.get('stt'),
                stamp_duty=brokerage_details.get('stamp_duty'),
                transaction=brokerage_details.get('transaction'),
                clearing=brokerage_details.get('clearing'),
                sebi_turnover=brokerage_details.get('sebi_turnover'),
                dp_plan_name=brokerage_details.get('dp_plan_name'),
                dp_plan_min_expense=brokerage_details.get('dp_plan_min_expense'),
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            logger.info(f"✅ Brokerage details saved successfully (order_id={obj.order_id})")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving brokerage details: {e}")
        finally:
            db.close()

    def save_order_details(self, order_details: dict):
        """
        Save order details to PostgreSQL database.
        """
        db = self.SessionLocal()
        try:
            obj = OrderDetails(
                order_id=order_details.get("order_id"),
                update_type=order_details.get("update_type"),
                user_id=order_details.get("user_id"),
                exchange=order_details.get("exchange"),
                instrument_token=order_details.get("instrument_token"),
                instrument_key=order_details.get("instrument_key"),
                trading_symbol=order_details.get("trading_symbol"),
                product=order_details.get("product"),
                order_type=order_details.get("order_type"),
                average_price=order_details.get("average_price"),
                price=order_details.get("price"),
                trigger_price=order_details.get("trigger_price"),
                quantity=order_details.get("quantity"),
                disclosed_quantity=order_details.get("disclosed_quantity"),
                pending_quantity=order_details.get("pending_quantity"),
                transaction_type=order_details.get("transaction_type"),
                order_ref_id=order_details.get("order_ref_id"),
                exchange_order_id=order_details.get("exchange_order_id"),
                parent_order_id=order_details.get("parent_order_id"),
                validity=order_details.get("validity"),
                status=order_details.get("status"),
                is_amo=order_details.get("is_amo"),
                variety=order_details.get("variety"),
                tag=order_details.get("tag"),
                exchange_timestamp=order_details.get("exchange_timestamp"),
                status_message=order_details.get("status_message"),
                order_request_id=order_details.get("order_request_id"),
                order_timestamp=order_details.get("order_timestamp"),
                filled_quantity=order_details.get("filled_quantity"),
                guid=order_details.get("guid"),
                placed_by=order_details.get("placed_by"),
                status_message_raw=order_details.get("status_message_raw"),
                total_charges=order_details.get("total_charges"),
                brokerage_charges=order_details.get("brokerage_charges"),
                gst=order_details.get("gst"),
                stt=order_details.get("stt"),
                stamp_duty=order_details.get("stamp_duty"),
                transaction=order_details.get("transaction"),
                clearing=order_details.get("clearing"),
                sebi_turnover=order_details.get("sebi_turnover"),
                dp_plan_name=order_details.get("dp_plan_name"),
                dp_plan_min_expense=order_details.get("dp_plan_min_expense")
)

            db.add(obj)
            db.commit()
            db.refresh(obj)
            logger.info(f"✅ Order details saved successfully (order_id={obj.order_id})")
            return obj.to_dict()

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error saving order details: {e}")

        finally:
            db.close()
    def save_llm_decision(self, decision: dict):
        db = self.SessionLocal()
        try:
            response = decision.get("response", {})
            cost_info = response.get("cost_info", {})  # corrected key name

            obj = LLMDecision(
                request=decision.get("request"),
                thought=response.get("thought"),
                action=response.get("action"),
                instrument_key=response.get("instrument_key"),
                confidence_score=response.get("confidence_score"),
                current_price=response.get("current_price"),
                stop_loss=response.get("stop_loss"),
                take_profit=response.get("take_profit"),
                cost_info_model=cost_info.get("model"),
                cost_info_prompt_tokens=cost_info.get("prompt_tokens"),
                cost_info_cached_tokens=cost_info.get("cached_tokens"),
                cost_info_completion_tokens=cost_info.get("completion_tokens"),
                cost_info_billable_prompt=cost_info.get("billable_prompt"),
                cost_info_billable_completion=cost_info.get("billable_completion"),
                cost_info_cost_usd=cost_info.get("cost_usd"),
                cost_info_cost_inr=cost_info.get("cost_inr"),
            )

            db.add(obj)
            db.commit()
            db.refresh(obj)

            logger.info(f"✅ LLM decision saved successfully (id={obj.id})")
            return obj.to_dict()

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error saving LLM decision: {e}")
        finally:
            db.close()
    
    def get_today_decisions_for_instrument(self, instrument_key: str):
        db = self.SessionLocal()
        try:
            today = date.today()

            results = (
                db.query(
                    LLMDecision.created_on,
                    LLMDecision.thought,
                    LLMDecision.action,
                    LLMDecision.current_price,
                    LLMDecision.stop_loss,
                    LLMDecision.take_profit,
                )
                .filter(
                    LLMDecision.instrument_key == instrument_key,
                    LLMDecision.created_on >= datetime.combine(today, datetime.min.time()),
                    LLMDecision.created_on <= datetime.combine(today, datetime.max.time())
                )
                .order_by(LLMDecision.id.desc())
                .limit(AGENT_CONFIG["PREVIOUS_DECISIONS_TO_CONSIDER"])
                .all()
            )

            # convert results into a list of dicts
            return [
                {
                    "decision_on": r.created_on.strftime("%Y-%m-%d %H:%M:%S"),
                    "thought": r.thought,
                    "action": r.action,
                    "stock_price": r.current_price,
                    "stop_loss": r.stop_loss,
                    "take_profit": r.take_profit
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"❌ Error fetching today's decisions: {e}")
            return []
        finally:
            db.close()

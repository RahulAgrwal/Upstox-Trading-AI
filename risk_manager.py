from logger_config import get_logger


logger = get_logger(__name__)

class RiskManager:
    """
    Handles real-time risk management for an intraday trading agent.

    This class is responsible for:
    1.  Validating trade decisions against pre-defined intraday risk rules.
    2.  Calculating appropriate position sizes based on risk capital.
    3.  Tracking daily performance metrics like P&L and total trades.
    4.  Acting as a circuit breaker by halting trading if daily loss limits are breached.
    """

    def __init__(self, config, agent_config):
        """
        Initializes the RiskManager with intraday-specific configuration.

        Args:
            config (dict): A dictionary containing risk management parameters.
        """
        # --- Core Risk Parameters ---
        self.max_position_size = config.get('MAX_POSITION_SIZE', 15000)
        self.stop_loss_pct = config.get('STOP_LOSS_PCT', 0.005)
        self.take_profit_pct = config.get('TAKE_PROFIT_PCT', 0.01)
        self.min_confidence_threshold = config.get('MIN_CONFIDENCE_THRESHOLD', 0.75)
        
        # --- Daily Circuit Breakers ---
        self.max_trades_per_day = config.get('MAX_TRADES_PER_DAY', 20)
        self.max_daily_loss_pct = config.get('MAX_DAILY_LOSS_PCT', 0.02) # 2% of starting capital
        self.leverage_on_intraday = agent_config['LEVERAGE_ON_INTRADAY']
        # --- State Tracking ---
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.is_trading_halted = False
        
        logger.info("Intraday Risk Manager initialized with settings: %s", config)

    def validate_decision(self, llm_decision: dict, portfolio: dict, current_price: float) -> bool:
        """
        Assesses a trade decision from the LLM against all intraday risk rules.

        Args:
            llm_decision (dict): The decision object from the LLM.
            portfolio (dict): The current state of the portfolio.

        Returns:
            bool: True if the trade is approved, False otherwise.
        """
        action = llm_decision.get('action')
        confidence = llm_decision.get('confidence_score', 0)
        quantity = llm_decision.get('quantity', 0)
        available_margin = portfolio.get('available_margin', 0)

        # Rule 0: On 'HOLD'
        if action == 'HOLD':
            logger.warning("Trade rejected: HOLD action.")
            return False


        # --- Pre-Trade Checks for BUY orders ---

        # Rule 1: Check if trading is halted due to daily loss limit
        if self.is_trading_halted:
            logger.warning("Trade rejected: Trading is halted for the day due to max loss limit breach.")
            return False
            
        # Rule 2: Check if max trades for the day have been reached
        if self.trades_today >= self.max_trades_per_day:
            logger.warning(f"Trade rejected: Max trades limit of {self.max_trades_per_day} reached for the day.")
            return False

        # Rule 3: Check LLM confidence score
        if confidence < self.min_confidence_threshold:
            logger.warning(f"Trade rejected: Confidence {confidence:.2f} is below threshold of {self.min_confidence_threshold:.2f}.")
            return False
        
        # 'SELL' (to close positions)
        if action == 'SELL':
            logger.info("SELL action approved to close existing position.")
            return True
        # If all checks pass for a BUY order
        logger.info("BUY decision has been validated by the Risk Manager.")
        self.trades_today += 1 # Increment trade count only for approved BUYs
        return True

    def calculate_quantity(self, price: float) -> int:
        """
        Calculates the number of shares to buy based on max position size.
        
        Args:
            price (float): The current market price of the instrument.
        
        Returns:
            int: The whole number of shares to purchase.
        """
        if price <= 0:
            return 0
        quantity = int(self.max_position_size // price)
        logger.info(f"Calculated quantity: {quantity} shares based on max position size of {self.max_position_size} at price {price}.")
        return quantity

    def update_pnl(self, pnl: float, starting_capital: float):
        """
        Updates the daily Profit and Loss and checks the daily loss limit.
        
        Args:
            pnl (float): The profit or loss from the most recently closed trade.
            starting_capital (float): The portfolio's starting cash for the day.
        """
        self.daily_pnl += pnl
        logger.info(f"Trade closed. P&L: {pnl:.2f}. Total Daily P&L: {self.daily_pnl:.2f}")

        # Check for max daily loss breach
        max_loss_amount = starting_capital * self.max_daily_loss_pct
        if self.daily_pnl < -max_loss_amount:
            self.is_trading_halted = True
            logger.critical(
                f"MAX DAILY LOSS LIMIT BREACHED! P&L {-self.daily_pnl:.2f} exceeds limit of {max_loss_amount:.2f}."
                " Halting all new BUY orders for the day."
            )


import os
import sys
import time
import threading

from flask_api import FlaskAPI
from logger_config import get_logger
from trading_agent import TradingAgent
from config import UPSTOX_CONFIG, LLM_CONFIG, RISK_CONFIG, AGENT_CONFIG, NSE_STOCKS, INTRADAY_TECHNICAL_ANALYZER_CONFIG, NEWSAPI_CONFIG
logger = get_logger(__name__)
def main(agent):
    """
    Main function to initialize and run the trading agent.
    This is the primary entry point of the application.

    Args:
        agent (TradingAgent): An already-instantiated TradingAgent to start.
    """
    # --- IMPORTANT SAFETY CHECK ---
    # Before starting, verify that the user has replaced the placeholder API keys
    # in the configuration file. This prevents runtime errors.
    if "YOUR_OPENAI_API_KEY" in LLM_CONFIG.values():
        logger.error("CRITICAL: API keys are not set in config.py. Please update them before running.")
        return

    logger.info("Initializing Trading Agent...")

    try:
        # Start the agent. This will trigger the authentication and websocket connection processes.
        agent.start()

        # Keep the main thread alive indefinitely. The agent's operations run in background threads.
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # This block catches the user pressing Ctrl+C.
        logger.info("Manual interruption detected. Stopping agent...")
        agent.stop()  # This calls the agent's graceful shutdown method.

    except Exception as e:
        # This is a catch-all for any other critical error that might occur.
        logger.critical(f"A critical error occurred: {e}", exc_info=True)
        agent.stop()  # Attempt to shut down gracefully even after an error.

    finally:
        # This code will run whether the agent is stopped by Ctrl+C or an error.
        logger.info("Agent has been shut down.")
        # Use sys.exit for a graceful shutdown (allows cleanup handlers to run)
        sys.exit(0)

# This standard Python construct ensures that the main() function is called
# only when the script is executed directly (e.g., `python main.py`).
if __name__ == "__main__":
    # Create the TradingAgent first, then attach it to the Flask API so the
    # API routes can call into the agent (for example, to get instruments).
    agent = TradingAgent(
        llm_config=LLM_CONFIG,
        risk_config=RISK_CONFIG,
        agent_config=AGENT_CONFIG,
        intraday_technical_config=INTRADAY_TECHNICAL_ANALYZER_CONFIG,
        news_api_config=NEWSAPI_CONFIG,
    )

    # Create Flask API with the agent attached and start it in a background
    # daemon thread. Disable reloader to avoid double-spawning.
    app = FlaskAPI(agent=agent)
    flask_thread = threading.Thread(target=app.run, daemon=True)
    flask_thread.start()

    # Now run the main logic which will initialize and start the agent.
    main(agent)


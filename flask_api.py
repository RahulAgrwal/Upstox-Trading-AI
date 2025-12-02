from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
import json

from logger_config import get_logger
logger = get_logger(__name__)


class FlaskAPI:
    """Basic Flask API class with common functionality

    Can optionally be instantiated with a `TradingAgent` instance so routes
    can access agent methods like `get_instruments_to_trade`.
    """

    def __init__(self, name=__name__, agent=None):
        self.app = Flask(name)
        self.api = Api(self.app)
        self.agent = agent
        self.setup_routes()

    def setup_routes(self):
        """Setup basic routes"""

        @self.app.route('/')
        def home():
            return jsonify({"message": "Welcome to Flask API", "status": "success"})

        @self.app.route('/get-stocks-to-trade', methods=['POST'])
        def stock_to_trade():
            logger.info("/get-stocks-to-trade called")

            # If an agent is attached, call its get_instruments_to_trade method.
            if self.agent:
                try:
                    # The agent expects a portfolio_margin dict. If the agent has
                    # Upstox clients attached we can attempt to get the current
                    # margin from the first client, otherwise pass a safe default.
                    data = request.get_json()
                    portfolio_margin = {"available_margin": data.get("available_margin", None)}
                    if not portfolio_margin["available_margin"]:
                        try:
                            if getattr(self.agent, 'upstox_clients', None):
                                client = self.agent.upstox_clients[0]
                                portfolio_margin = client.get_user_fund_margin() or {}
                        except Exception:
                            portfolio_margin = {}

                    instruments = self.agent.get_instruments_to_trade(portfolio_margin)
                    return jsonify({"status": "success", "instruments": instruments})
                except Exception as e:
                    logger.error(f"Error getting instruments from agent: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 500

            # Fallback response when no agent is attached
            logger.info("No TradingAgent attached to FlaskAPI. Returning health status.")
            return jsonify({"status": "healthy", "service": "Flask API", "agent_attached": False})

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application"""
        self.app.run(host=host, port=port, debug=debug)


# Example usage
if __name__ == '__main__':
    api = FlaskAPI()
    api.run()
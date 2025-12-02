import upstox_client
import json
from datetime import datetime
import pandas as pd
import requests
import gzip

from logger_config import get_logger
logger = get_logger(__name__)
class UpstoxClient:
    """
    Upstox Client wrapper for trading operations with SDK v2.

    Handles authentication, market data subscription, and order placement.
    """

    def __init__(self, api_key: str, access_token: str = None,api_secret:str=None,redirect_uri : str = None):
        """
        Initialize the Upstox client.

        Args:
            api_key (str): Upstox API key
            access_token (str, optional): Access token. If not provided, user must authenticate.
        """
        self.api_key = api_key
        self.access_token = access_token
        self.client = None
        self.market_data_streamer = None
        self.portfolio_data_streamer = None
        self.subscribed_instruments = set()
        self.nse_instruments = self.fetch_all_nse_instruments()
        self._initialize_client()
        self.user_profile = None
        self.user_funds = None

    def _initialize_client(self):
        """Initializes the Upstox SDK client."""
        if not self.access_token:
            logger.warning("No access token provided. Please authenticate first.")
            return

        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        self.client = upstox_client.ApiClient(configuration)
        logger.info("Upstox client initialized successfully.")

    def authenticate(self):
        """
        Prompts user for manual OAuth2 authentication to generate access token.
        """
        if self.access_token:
            logger.info("Already authenticated with access token.")
            return

        logger.info("Please generate access token using Upstox developer portal or OAuth2 flow. Get token from https://account.upstox.com/developer/apps")
        self.access_token = input("Enter access token: ")
        self._initialize_client()
        logger.info("Access token set successfully.")

    def connect_market_data_streamer(self, on_market_data, on_market_intraday_data):
        """
        Connects to live market data market_data_streamer via Upstox SDK.

        Args:
            instruments (list[str]): List of instrument keys to subscribe to.
            on_tick_callback (function): Callback to receive live tick data.
        """
        if not self.client:
            raise ConnectionError("Upstox client not initialized or authenticated.")

        try:
            self.market_data_streamer = upstox_client.MarketDataStreamerV3(self.client)
            self.market_data_streamer.on("open", self.on_open)
            self.market_data_streamer.on("message", lambda msg: self.on_message(msg, on_market_data, on_market_intraday_data))

            logger.info("Connecting to market_data_streamer...")
            self.market_data_streamer.connect()
            
        except Exception as e:
            logger.error(f"Error setting up market_data_streamer: {e}")
            raise

    def on_open(self):
        logger.info("market_data_streamer connection opened.")
        if self.subscribed_instruments:
            self.subscribe(list(self.subscribed_instruments))
    # Handle incoming market data messages\
    def on_message(self,message, on_market_data, on_market_intraday_data):
        # Update internal market data state
        # logger.info(f"Received message: {message}")
        if 'feeds' in message:
            for instrument_key, feed_data in message['feeds'].items():
                on_market_data(message['feeds'])
                on_market_intraday_data({instrument_key:self.get_intra_day_candle_data(instrument_key)})


    def subscribe(self, instrument_keys, data_type="full"):
        """
        Subscribes to market data for given instruments.

        Args:
            instrument_keys (list[str]): A list of instrument keys to subscribe to.
            data_type (str): The type of data feed ('full' or 'ltpc').
        """
        if self.market_data_streamer:
            logger.info(f"Subscribing to: {str(instrument_keys)}")
            self.market_data_streamer.subscribe(instrument_keys, data_type)
            self.subscribed_instruments.update(instrument_keys)
        else:
            logger.error("market_data_streamer is not connected. Cannot subscribe.")
            
    def unsubscribe(self, instrument_keys):
        """Unsubscribes from market data for given instruments."""
        if self.market_data_streamer:
            logger.info(f"Unsubscribing from: {str(instrument_keys)}")
            self.market_data_streamer.unsubscribe(instrument_keys)
            self.subscribed_instruments.difference_update(instrument_keys)
        else:
            logger.error("Websocket is not connected. Cannot unsubscribe.")


    def place_order(self, instrument_key: str, quantity: int, transaction_type: str,
                    order_type: str = "MARKET", price: float = 0.0, 
                    product: str = "D", validity: str = "DAY", stop_loss: float = 0.0, take_profit: float = 0.0):
        """
        Places an order using Upstox SDK.

        Args:
            instrument_key (str): Instrument token or symbol
            quantity (int): Number of shares
            transaction_type (str): 'BUY' or 'SELL'
            order_type (str): 'MARKET', 'LIMIT', 'SL', 'SL-M'
            price (float): Price for LIMIT orders
            product (str): 'D' for Delivery, 'I' for Intraday
            validity (str): 'DAY' or 'IOC'

        Returns:
            dict: Order response
        """
        if not self.client:
            raise ConnectionError("Upstox client not initialized or authenticated.")

        try:
            # Create order request with string values
            order_req = upstox_client.PlaceOrderV3Request(
                quantity=quantity,
                product=product,  # "D" for Delivery, "I" for Intraday
                validity=validity,  # "DAY" or "IOC"
                price=price if order_type.upper() != "MARKET" else 0.0,
                tag="python_sdk_order",
                instrument_token=instrument_key,
                order_type=order_type.upper(),  # "MARKET", "LIMIT", "SL", "SL-M"
                transaction_type=transaction_type.upper(),  # "BUY" or "SELL"
                disclosed_quantity=0,
                trigger_price=stop_loss,
                is_amo=False
            )

            order_api = upstox_client.OrderApiV3(self.client)
            resp = order_api.place_order(order_req)
            order_data = None
            if resp:
                order_data = resp.data.to_dict()
                    
            logger.info(f"Order placed successfully: {order_data}")
            return order_data
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def disconnect_market_data_streamer(self):
        """Disconnects from the market_data_streamer."""
        if self.market_data_streamer:
            self.market_data_streamer.disconnect()
            logger.info("WebSocket disconnected.")

    def get_order_book(self):
        """Gets the current order book."""
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            order_api = upstox_client.OrderApiV3(self.client)
            return order_api.get_order_book()
        except Exception as e:
            logger.error(f"Error getting order book: {e}")
            return None

    def get_positions(self):
        """Gets current positions."""
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        try:
            portfolio_api = upstox_client.PortfolioApi(self.client)
            positions =  portfolio_api.get_positions("2.0")
            if positions:
                positions_data = positions.data
                logger.info(f"Positions Data for User : {self.user_profile['user_name']}: \n{positions_data}")
                return positions_data
            return None
        except Exception as e:
            logger.error(f"Error getting positions for User : {self.user_profile['user_name']}: {e}")
            return None
    
    def protfolio_data_streamer_on_message(self, message, update_portfolio_positions, save_order_details):
        logger.info(f"Portfolio message for User : {self.user_profile['user_name']}: {message}")
        update_portfolio_positions(self.get_positions())

        try:
            order_details_dict = json.loads(message.replace("'", '"'))
            # Get Brokerage For order
            brokerage_details = self.get_brokerage(order_details_dict["instrument_token"],order_details_dict["quantity"],order_details_dict["product"],order_details_dict["transaction_type"],order_details_dict["average_price"])
            if brokerage_details:
                order_details_dict["total_charges"] = brokerage_details["total"]
                order_details_dict["brokerage_charges"] = brokerage_details["brokerage"]
                order_details_dict["gst"]= brokerage_details['taxes']['gst']
                order_details_dict["stt"]= brokerage_details['taxes']['stt']
                order_details_dict["stamp_duty"]= brokerage_details['taxes']['stamp_duty']
                order_details_dict["transaction"]= brokerage_details['other_taxes']['transaction']
                order_details_dict["clearing"]= brokerage_details['other_taxes']['clearing']
                order_details_dict["sebi_turnover"]= brokerage_details['other_taxes']['sebi_turnover']
                order_details_dict["dp_plan_name"]= brokerage_details['dp_plan']['name']
                order_details_dict["dp_plan_min_expense"]= brokerage_details['dp_plan']['min_expense']
            logger.info(f"Order details for User : {self.user_profile['user_name']} for Instrument {order_details_dict['instrument_token']} : {order_details_dict}")
            
            # Save Order Details
            save_order_details(order_details_dict)
        except Exception as e:
            logger.error(f"Error saving order details for User : {self.user_profile['user_name']}: {e}")
        
        
    def protfolio_data_streamer_on_open(self):
        logger.info(f"Portfolio Opened for User : {self.user_profile['user_name']}")

    def connect_portofolio_data_streamer(self, update_portfolio_positions, save_order_details):
        """
        Connects to live market data portofolio_data_streamer via Upstox SDK.

        Args:
            instruments (list[str]): List of instrument keys to subscribe to.
            on_tick_callback (function): Callback to receive live tick data.
        """
        if not self.client:
            raise ConnectionError(f"Upstox client not initialized or authenticated for User : {self.user_profile['user_name']}")

        try:
            self.portfolio_data_streamer = upstox_client.PortfolioDataStreamer(self.client)
            self.portfolio_data_streamer.on("message", lambda msg : self.protfolio_data_streamer_on_message(msg,update_portfolio_positions, save_order_details ))
            self.portfolio_data_streamer.on("open", self.protfolio_data_streamer_on_open)
            logger.info(f"Connecting to portfolio_data_streamer for user : {self.user_profile['user_name']}...")
            self.portfolio_data_streamer.connect()
            
        except Exception as e:
            logger.error(f"Error setting up portfolio_data_streamer for User : {self.user_profile['user_name']}: {e}")
            raise

    def get_intra_day_candle_data(self, instrument_key, unit :str = "minutes", interval :int = 5):
        """Gets get_intra_day_candle_data"""
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            history_api = upstox_client.HistoryV3Api(self.client)
            history =  history_api.get_intra_day_candle_data(instrument_key, unit, interval)
            if history.data:
                history_data = history.data.to_dict()
                history_data_candles = history_data['candles']
                candles_history_list = []
                for candle in history_data_candles[:10]:
                    candle_dict = {
                        "timestamp": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5]
                    }
                    candles_history_list.append(candle_dict)

                return candles_history_list
            return None
        except Exception as e:
            logger.error(f"Error getting positions for User : {self.user_profile['user_name']}: {e}")
            return None
    def  get_brokerage(self, instrument_token: str, quantity: int,product:str,transaction_type :str, price: float = 0.0):
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        charge_data = None
        try:
            charge_api = upstox_client.ChargeApi(self.client)
            charge = charge_api.get_brokerage(instrument_token, quantity,product,transaction_type,price, "2.0")
            if charge:
                charge_data = charge.data.charges.to_dict()
                logger.info(f"Brokerage of {instrument_token} for {transaction_type} of Quantity : {quantity} is {charge_data}")
            return charge_data
        except Exception as e:
            logger.error(f"Error getting Brokerage for User : {self.user_profile['user_name']}: {e}")
            return charge_data
        
    def get_profile(self):
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            profile_api = upstox_client.UserApi(self.client)
            profile = profile_api.get_profile("2.0")
            if(profile and profile.data):
                profile = profile.data.to_dict()
            else:
                raise Exception("Error getting Profile Data")
            logger.info(f"================User Profile================ \n{profile}")
            self.user_profile = profile
            return profile
        except Exception as e:
            logger.error(f"Error getting Profile: {e}")
            return None
    
    def get_user_fund_margin(self):
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            user_api = upstox_client.UserApi(self.client)
            user_fund_margin = user_api.get_user_fund_margin("2.0", segment="SEC")
            if user_fund_margin and user_fund_margin.data and user_fund_margin.data:
                equity_data = user_fund_margin.data['equity']
                margin_data = {
                'adhoc_margin': equity_data.adhoc_margin,
                'available_margin': equity_data.available_margin,
                'exposure_margin': equity_data.exposure_margin,
                'notional_cash': equity_data.notional_cash,
                'payin_amount': equity_data.payin_amount,
                'span_margin': equity_data.span_margin,
                'used_margin': equity_data.used_margin
                }
                logger.info(f"User Funds And Margins for {self.user_profile['user_name']} : {margin_data}")
                self.user_funds = margin_data
                return margin_data
            return None        
        except Exception as e:
            logger.error(f"Error getting User Funds And Margins for {self.user_profile['user_name']} : {e}")
            return None

    def get_instrument_list_from_stocks(self, stocks: list[str]) -> list[str]:
        """
        Given a list of stock names (or partial names), return the matching NSE instrument keys.
        """
        if self.nse_instruments.empty:
            logger.warning("NSE instruments DataFrame is empty!")
            return []

        # Filter for exact match (case-insensitive)
        result = self.nse_instruments[
            self.nse_instruments["trading_symbol"].str.upper().isin([s.upper() for s in stocks])
        ]

        instrument_keys = result["instrument_key"].tolist()
        logger.info(f"Found instrument_key(s) for User : {self.user_profile['user_name']} for {stocks}: {instrument_keys}")
        return instrument_keys    
    
    def get_instrument_info_from_stock(self, stock: str) -> dict:
        """
        Given a stock symbol (trading_symbol), return all details of the stock from NSE instruments.
        """
        if self.nse_instruments.empty:
            logger.warning("NSE instruments DataFrame is empty!")
            return {}

        # Filter for exact match (case-insensitive)
        result = self.nse_instruments[
            self.nse_instruments["trading_symbol"].str.upper() == stock.upper()
        ]

        if result.empty:
            logger.warning(f"No instrument found for stock: {stock}")
            return {}
        instrument_info = result.iloc[0].to_dict()
        logger.info(f"Found instrument info for {stock}: {instrument_info}")
        # Convert the first (and only) row to dictionary
        return instrument_info

    def get_instrument_info_from_instrument_key(self, instrument_key: str) -> dict:
        """
        Given a instrument_key, return all details of the instrument_key from NSE instruments.
        """
        if self.nse_instruments.empty:
            logger.warning("NSE instruments DataFrame is empty!")
            return {}

        # Filter for exact match (case-insensitive)
        result = self.nse_instruments[
            self.nse_instruments["instrument_key"] == instrument_key
        ]

        if result.empty:
            logger.warning(f"No instrument found for instrument_key: {instrument_key}")
            return None
        instrument_info = result.iloc[0].to_dict()
        logger.info(f"Found instrument info for {instrument_key}: {instrument_info}")
        # Convert the first (and only) row to dictionary
        return instrument_info
        
    def get_instrument_key(self, trading_symbol):
        if(self.nse_instruments.empty == False):
            result = self.nse_instruments[
                self.nse_instruments["trading_symbol"] == trading_symbol
            ]
            logger.info(f"Found instrument_key for {trading_symbol}: {result}")
            return result
        return None
    def get_instrument_name(self, instrument_key):
        if(self.nse_instruments.empty == False):
            result = self.nse_instruments[
                self.nse_instruments["instrument_key"] == instrument_key
            ]
            logger.info(f"Found Instrument name for {instrument_key}: {result}")
            return result
        return None

    def fetch_all_nse_instruments(self):
        """
        Fetches the gzipped NSE instrument file from Upstox, unzips it,
        loads the JSON data into a pandas DataFrame, and returns
        selected columns for all instruments within the file.
        """
        url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Decompress the gzipped content
            decompressed_data = gzip.decompress(response.content)

            # Load JSON data from the decompressed content
            instruments_data = json.loads(decompressed_data)

            # Create DataFrame directly from the list of dictionaries
            df = pd.DataFrame(instruments_data)

            # Filter for NSE Equity instruments specifically, if needed (as per original request)
            # Note: The original request was to get "all NSE instruments", this filter is for "NSE_EQ"
            # If you truly want ALL instruments in the file, remove this filter.
            nse_eq_df = df[(df['segment'] == 'NSE_EQ') & (df['instrument_type'] == 'EQ')]

            # Return the desired columns for NSE Equity instruments
            res=  nse_eq_df[["instrument_key", "trading_symbol", "name"]]
            logger.info(f"Found {len(res)} NSE Equity instruments")
            return res

        except requests.exceptions.RequestException as e:
            logger.info(f"Error fetching the instrument file: {e}")
            return pd.DataFrame() # Return an empty DataFrame on error
        except json.JSONDecodeError as e:
            logger.info(f"Error decoding JSON data: {e}")
            return pd.DataFrame()
        except KeyError as e:
            logger.info(f"Missing expected column in instrument data: {e}")
            return pd.DataFrame()
        
    def exit_all_positions(self):
        logger.info("Exiting all positions...")
        try:
            api_instance = upstox_client.OrderApi(self.client)
            api_response = api_instance.exit_positions()
            logger.info(f"Positions exited successfully: {api_response}")
        except Exception as e:
            logger.error(f"Error exiting positions: {e}")
    def get_last_trading_price(self, symbols, api_version : str = "2.0"):
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            api = upstox_client.MarketQuoteApi(self.client)
            ltp = api.ltp(symbols, api_version)
            if(ltp and ltp.data):
                ltp = ltp.data
            else:
                raise Exception("Error getting LTP Data")
            return ltp
        except Exception as e:
            logger.error(f"Error getting LTP: {e}")
            return None
        

    def get_full_market_quote(self, symbols, api_version : str = "2.0"):
        if not self.client:
            raise ConnectionError("Upstox client not initialized.")
        
        try:
            api = upstox_client.MarketQuoteApi(self.client)
            market_quote = api.get_full_market_quote(symbols, api_version)
            if(market_quote and market_quote.data):
                return market_quote.to_dict().get('data')
            return {}
        except Exception as e:
            logger.error(f"Error getting Full market Quote: {e}")
            return None
import os
import base64
import mimetypes
import re
from openai import OpenAI
import json
from datetime import datetime
from config import INTRADAY_TECHNICAL_ANALYZER_CONFIG, LLM_PRICING, RISK_CONFIG, AGENT_CONFIG, LLM_CONFIG
from logger_config import get_logger
from prompts import SYSTEM_PROMPT_NEW_TRADE_EXECUTION, SYSTEM_PROMPT_POSITION_PRESENT, SYSTEM_PROMPT_STOCK_TO_TRADE
logger = get_logger(__name__)
JSON_REQ_RES_DIR = "llm_json_req_res"
class LLMClient:
    """
    Client for interacting with a Large Language Model (LLM) like OpenAI's GPT.
    
    This class formats prompts, sends them to the LLM, and parses the structured
    JSON response to extract trading decisions.
    """

    def __init__(self):
        """
        Initializes the LLM client.

        Args:
            api_key (str): The API key for the LLM service.
            model (str): The specific model to use (e.g., "gpt-4-turbo").
        """
        if not LLM_CONFIG['api_key']:
            raise ValueError("LLM API key not provided.")
        self.client = OpenAI(api_key= LLM_CONFIG['api_key'], base_url=LLM_CONFIG['base_url'])
        self.model =  LLM_CONFIG['model']
        self.temperature = LLM_CONFIG['temperature']
        self.model_for_stock_selection = LLM_CONFIG['model_for_stock_selection']
        self.model_for_stock_qty_selection = LLM_CONFIG['model_for_stock_qty_selection']
                
        os.makedirs(JSON_REQ_RES_DIR, exist_ok=True)


    def generate_decision(self, instrument_key: str, instrument_to_trade: str, market_data_str: str, market_intraday_data_str: str, portfolio_margin_status_str: str, portfolio_position_status_str: str, technical_summary: str, stock_news: str, previous_decision, number_of_instruments_to_trade,chart_plot_image_path, leverage_on_intraday: int = 1) -> dict | None:
        """
        Sends the current market and portfolio data to the LLM and gets a trading decision.
        """
        # User data prompt
        user_data_prompt = f"""
        Here is the current trading data:

        Stock to Trade: {instrument_to_trade}
        Number of Stocks to Trade: {number_of_instruments_to_trade}
        Leverage on Intraday: {AGENT_CONFIG["LEVERAGE_ON_INTRADAY"]} times  
        Portfolio Margin: {portfolio_margin_status_str}
        Portfolio Positions: {portfolio_position_status_str} 
        Current Market Data: {market_data_str}
        Technical Summary: {technical_summary}
        Latest News: {stock_news}
        Previous Decisions: {previous_decision}
        Current Time: {datetime.now().strftime("%H:%M:%S")} IST
        Market Close Time: {AGENT_CONFIG["MARKET_CLOSE_TIME"]} IST
        Decision Interval: {AGENT_CONFIG["DECISION_INTERVAL_SECONDS"]} seconds
        Risk_Percentage: {RISK_CONFIG["RISK_PERCENTAGE_FOR_SINGLE_TRADE"]}%
        Technical Indicator Configuration : {INTRADAY_TECHNICAL_ANALYZER_CONFIG}
        """

        # Assistant format prompt
        assistant_format_prompt = """
        I understand. I'll analyze the data and provide a trading decision in the specified JSON format with appropriate reasoning and confidence level.
        """
        # User question prompt
        user_question_prompt = """
        Based on this data, analyze the current stock and portfolio while respecting leverage and exposure constraints. 
        Determine the optimal next action (BUY, SELL, or HOLD) and provide your decision in JSON format.
        """

        image_data_url = self.encode_image_to_base64(chart_plot_image_path)

        logger.info("================Generating LLM decision======================")
        try:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT_NEW_TRADE_EXECUTION},
                {"role": "user", "content": user_data_prompt},
                {"role": "assistant", "content": assistant_format_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_question_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ]

            response = self.get_llm_response(self.model_for_stock_qty_selection, prompt)
            # response = None
            decision_str = response.choices[0].message.content
            logger.info(f"***************LLM DECISION***************: \n{decision_str}")

            decision_json = json.loads(decision_str)

            # Extract token usage
            usage = getattr(response, "usage", None)
            if usage:
                cost = self.calculate_cost(response.model, usage)
                logger.info(f"====Cost Breakdown====\n{json.dumps(cost)}")

                # Optional: include cost info in decision JSON
                decision_json["cost_info"] = cost
            json_to_save = None
            try : 
                json_to_save = {
                    "request" : prompt,
                    "response" : decision_json
                }
                self.create_json_file(json_to_save, instrument_key)
            except Exception as e:
                logger.error(f"Failed to create JSON file: {e}")

            return json_to_save
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON response: {e}")
            # logger.error(f"Received string: {decision_str}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while communicating with the LLM: {e}")
            return None
        
    
    def generate_decision_for_position_present(self, instrument_key: str, instrument_to_trade: str, market_data_str: str, market_intraday_data_str: str, portfolio_margin_status_str: str, portfolio_position_status_str: str, technical_summary: str, stock_news: str, previous_decision, number_of_instruments_to_trade, chart_plot_image_path, leverage_on_intraday: int = 1) -> dict | None:
        """
        Sends the current market and portfolio data to the LLM and gets a trading decision.
        """

        # System prompt (already defined as SYSTEM_PROMPT_POSITION_PRESENT)

        # User data prompt
        user_data_prompt = f"""
        Current trading scenario with existing position:

        Instrument: {instrument_to_trade}
        Existing Positions: {portfolio_position_status_str}
        Available Margin: {portfolio_margin_status_str}

        Market Data: {market_data_str}
        Intraday Candles: {market_intraday_data_str}
        Technical Analysis: {technical_summary}
        Relevant News: {stock_news}

        Trading Context:
        - Number of instruments to trade: {number_of_instruments_to_trade}
        - Leverage: {AGENT_CONFIG["LEVERAGE_ON_INTRADAY"]}x
        - Current Time: {datetime.now().strftime("%H:%M:%S")} IST
        - Market Closes: {AGENT_CONFIG["MARKET_CLOSE_TIME"]} IST
        - Decision Interval: {AGENT_CONFIG["DECISION_INTERVAL_SECONDS"]} seconds
        - Risk per trade: {RISK_CONFIG["RISK_PERCENTAGE_FOR_SINGLE_TRADE"]}%
        - Technical Indicator Configuration : {INTRADAY_TECHNICAL_ANALYZER_CONFIG}
        
        """

        # User question prompt
        user_question_prompt = """
        Given the existing position and current market conditions, should we hold, add to, or exit the position?
        Consider position sizing, risk management, and time until market close.
        """

        # Assistant guidance prompt
        assistant_guidance_prompt = """
        I'll analyze the existing position in context of current market conditions. Key considerations:
        1. Current P&L and position health
        2. Portfolio exposure and margin safety
        3. Technical signals and trend strength
        4. News impact and volatility
        5. Time decay towards market close
        6. Risk-reward ratio for adding/exiting

        I'll provide a structured decision with clear reasoning about position management.
        """
        image_data_url = self.encode_image_to_base64(chart_plot_image_path)
        logger.info("================Generating LLM decision for existing position======================")
        try:
            prompt = [
                {"role": "system", "content": SYSTEM_PROMPT_POSITION_PRESENT},
                {"role": "user", "content": user_data_prompt},
                {"role": "assistant", "content": "Provide Previous Decision Context Acknowledgement"},
                {"role": "user", "content": f"- Previous decisions: {previous_decision}"},
                {"role": "assistant", "content": assistant_guidance_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_question_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ]

            response = self.get_llm_response(self.model, prompt)
            decision_str = response.choices[0].message.content
            logger.info(f"***************LLM DECISION FOR EXISTING POSITION***************: \n{decision_str}")

            decision_json = json.loads(decision_str)

            # Extract token usage
            usage = getattr(response, "usage", None)
            if usage:
                cost = self.calculate_cost(response.model, usage)
                logger.info(f"====Cost Breakdown====\n{json.dumps(cost)}")

                decision_json["cost_info"] = cost

            json_to_save = None
            try: 
                json_to_save = {
                    "request": prompt,
                    "response": decision_json
                }
                self.create_json_file(json_to_save, instrument_key)
            except Exception as e:
                logger.error(f"Failed to create JSON file: {e}")

            return json_to_save

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while communicating with the LLM: {e}")
            return None

    def get_instrument_to_trade(self, technical_summaries) -> dict | None:
        logger.info("================Generating LLM decision for instrument to trade======================")

        user_prompt = f"""
        Carefully Analyze the technical summaries of multiple stocks provided below with chart Plots.

        Some key considerations:
            - Current Time: {datetime.now().strftime("%H:%M:%S")} IST
            - Market Close Time: {AGENT_CONFIG["MARKET_CLOSE_TIME"]} IST  
            - Number of Stocks to select: {AGENT_CONFIG["NUMBER_OF_STOCKS_TO_TRADE"]}
            - Technical Indicator Configuration : {INTRADAY_TECHNICAL_ANALYZER_CONFIG}
                
        Return your decision strictly in JSON format.
        """
        try:
            user_prompt_content = [{"type": "text", "text": user_prompt}]
            for technical_summary in technical_summaries:
                summary = [{"type": "text", "text": f"===Stock {technical_summary['index']}===\n{technical_summary}"}]
                image_content = self.encode_image_to_base64(technical_summary['chart_plot_image_path'])
                if image_content:
                    summary.append({"type": "image_url", "image_url": {"url": image_content}})
                user_prompt_content.extend(summary)
                


            prompt =[
                    {"role": "system", "content": SYSTEM_PROMPT_STOCK_TO_TRADE},
                    {"role": "user", "content": user_prompt_content}
                ]
            response = self.get_llm_response(self.model_for_stock_selection, prompt)
            # response = None
            decision_str = response.choices[0].message.content
            logger.info(f"***************STOCK TO TRADE*************** \n{decision_str}")

            decision_json = json.loads(decision_str)

            # Extract token usage
            usage = getattr(response, "usage", None)
            if usage:
                cost = self.calculate_cost(response.model, usage)
                logger.info(f"====Cost Breakdown====\n{json.dumps(cost)}")

                # Optional: include cost info in decision JSON
                decision_json["cost_info"] = cost
            try : 
                json_to_save = {
                    "request" : prompt,
                    "response" : decision_json
                }
                self.create_json_file(json_to_save)
            except Exception as e:
                logger.error(f"Failed to create JSON file: {e}")
            decision_dict = decision_json["results"]
            return decision_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON response: {e}")
            # logger.error(f"Received string: {decision_str}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while communicating with the LLM: {e}")
            return None

    def get_llm_response(self, model,prompt):
        response = self.client.chat.completions.create(
                model=model,
                messages=prompt,
                response_format={"type": "json_object"},
                temperature=self.temperature
            )
        return response
    def calculate_cost(self, model: str, usage, usd_to_inr: float = None):
        pricing = LLM_PRICING
        if not usd_to_inr:
            usd_to_inr = LLM_PRICING['usd_to_inr']['inr']
    
        # ✅ Try exact match first
        model_base = next((m for m in pricing if model == m), None)
        # ✅ If not found, try partial match (for versioned model names)
        if not model_base:
            for base_name in pricing:
                if base_name in model:
                    model_base = base_name
                    break
    
        input_rate = pricing[model_base]["input"]
        output_rate = pricing[model_base]["output"]
    
        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
    
        # Handle cached tokens safely
        cached_tokens = 0
        if hasattr(usage, "prompt_tokens_details") and isinstance(usage.prompt_tokens_details, dict):
            cached_tokens = usage.prompt_tokens_details.get("cached_tokens", 0)
    
        # Compute billable tokens
        billable_prompt = max(float(prompt_tokens - cached_tokens), 0.0)
        billable_completion = float(completion_tokens)

        # Debug log
        logger.info(f"Model: {model}")
        logger.info(f"Prompt tokens: {prompt_tokens}, Cached: {cached_tokens}, Completion: {completion_tokens}")
        logger.info(f"Rates: input={input_rate}, output={output_rate}")
        logger.info(f"Billable prompt={billable_prompt}, Billable completion={billable_completion}")

        # Cost computation (force float division)
        cost_usd = (billable_prompt / 1000000.0) * input_rate + (billable_completion / 1000000.0) * output_rate
        cost_inr = cost_usd * usd_to_inr
        logger.info(f"Cost to Execute LLM Decision: ${cost_usd:f} (≈ ₹{cost_inr:f})")
    
        return {
            "model": model,
            "prompt_tokens": prompt_tokens,
            "cached_tokens": cached_tokens,
            "completion_tokens": completion_tokens,
            "billable_prompt": billable_prompt,
            "billable_completion": billable_completion,
            "cost_usd": cost_usd,
            "cost_inr": cost_inr,
        }

    def create_json_file(self, body, prefix:str = "JSON"):
        try:
            logger.info("Creating JSON Prompt file...............")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
            # Sanitize safe_prefix
            safe_prefix = re.sub(r'[\\/*?:"<>|]', "_", prefix)
    
            # Safe path join
            json_file_name = f"{timestamp}_{safe_prefix}.json"
            json_file_path = os.path.join(JSON_REQ_RES_DIR, json_file_name)
    
            # Write JSON file
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(body, json_file, ensure_ascii=False, indent=2)
                logger.info(f"JSON Prompt file created: {json_file_path}")
    
        except Exception as e:
            logger.error(f"Failed to create JSON Prompt file: {e}")

    def get_image_analysis_response(self, image_path: str, instruction: str = "Analyze this chart and describe key insights.") -> str | None:
        """
        Sends an image (e.g., stock chart) to ChatGPT-5 for analysis and returns the textual response.

        Args:
            image_path (str): Path to the image file (local or URL).
            instruction (str): Optional instruction for how the LLM should interpret the image.

        Returns:
            str | None: LLM's response text if successful, else None.
        """
        try:

            logger.info(f"Sending image for analysis: {image_path}")
            image_data_url = self.encode_image_to_base64(image_path)
            # Build prompt with image input
            prompt = [
                {"role": "system", "content": "You are a financial data analyst. You must always respond in JSON format."},
                {"role": "user", "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ]

            # Send to model
            response = self.get_llm_response(self.model_for_stock_qty_selection, prompt)
            result_text = response.choices[0].message.content.strip()

            logger.info(f"===== LLM Image Analysis Response =====\n{result_text}")
            return result_text

        except Exception as e:
            logger.error(f"Error while sending image to LLM: {e}")
            return None

    def encode_image_to_base64(self, image_path: str) -> str | None:
        """
        Converts a local image into a Base64 data URL for LLM multimodal input.

        Args:
            image_path (str): Path to the image file (local).

        Returns:
            str | None: Base64-encoded data URL string, or None if the image is invalid/missing.
        """
        try:
            image_path = os.path.abspath(image_path)

            if not os.path.exists(image_path):
                logger.warning(f"Image not found at: {image_path}")
                return None

            # Guess MIME type (e.g. image/png, image/jpeg)
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type is None:
                mime_type = "image/png"  # default fallback

            # Read and encode the image
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")

            # Return full data URL
            data_url = f"data:{mime_type};base64,{encoded}"
            logger.info(f"Image encoded successfully: {image_path}")
            return data_url

        except Exception as e:
            logger.error(f"Error encoding image to Base64: {e}")
            return None
# --- Usage Example ---
if __name__ == "__main__":
    # Basic usage
    analyzer = LLMClient()
    analyzer.get_image_analysis_response(image_path="IEX.NS_1m_3D_chart.png")
    #     print(analyzer.data_clean.head())
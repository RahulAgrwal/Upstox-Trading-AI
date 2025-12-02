# Upstox Agentic AI

Automated, LLM-powered intraday stock trading agent for the NSE (National Stock Exchange of India).

## Overview

Upstox Agentic AI leverages state-of-the-art Large Language Models (LLMs) and technical analysis to autonomously select, execute, and manage high-probability intraday trades on the NSE. It uses live data feeds, advanced prompt engineering, and robust risk controls to maximize intraday profitability.

## Key Features

- **LLM-Powered Trade Decisioning:** Uses GPT-4/GPT-5 or Gemini models for advanced stock selection, position sizing, and reasoning.
- **Automated Stock Selection:** Identifies the best NSE stock for the day using technical signals and volume/momentum analytics.
- **End-to-End Trade Management:** From analysis to execution (via the Upstox API), including dynamic risk controls and EOD position exits.
- **Multi-Modal Input:** Feeds candlestick charts and news context to the LLM for deeper insight.
- **RESTful API:** Flask-based microservice provides endpoints for external systems or dashboards.
- **Modular Design:** Easily extendable, support for different LLM providers and brokers.
- **Comprehensive Logging & Cost Tracking:** Tracks LLM token usage, inference costs, and trading actions for transparency.

## Project Structure

```
├── config.py                # All API keys, thresholds, agent configs
├── prompts.py               # LLM system/user prompt templates
├── trading_agent.py         # Orchestrates main trade and risk logic
├── llm_integration.py       # OpenAI GPT (or Gemini) integration
├── upstox_wrapper.py        # Upstox SDK wrapper for order/data handling
├── flask_api.py             # RESTful API exposing agent methods
├── intraday_technical_analyzer.py # Technical indicator calculations
├── news_fetcher.py          # NewsAPI wrapper for stock news
├── main.py                  # Main program entrypoint
├── ...                      # Other helpers, models, and utilities
```

## Requirements

- Python 3.10+
- Upstox SDK
- OpenAI Python SDK and/or Google Gemini SDK
- Flask & Flask-RESTful
- yfinance, pandas_ta, pandas, numpy, matplotlib
- NewsAPI Python client
- (See `requirements.txt` for full list)

## Setup & Configuration

1. **Clone This Repository**
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set Up Your `.env` File:**
    - Fill in your OpenAI/Gemini keys, Upstox keys, News API keys, Database credentials, etc.
    - Example variables: `UPSTOX_API_KEY`, `OPENAI_API_KEY`, `NEWS_API_KEY`, etc.
4. **Configure Trading and Risk Parameters:**
    - All tunable agent and indicator configs are in `config.py`.
5. **Run the Main Program:**
   ```bash
   python main.py
   ```
   The trading agent and API will start. Check logs for live progress and errors.

## REST API

A Flask REST API is provided (default port 5000).

**Example Endpoint:**

- `POST /get-stocks-to-trade`
    - Input: `{ "available_margin": 100000 }`
    - Output: `{ "status": "success", "instruments": [...] }`

## Security Caveats

- **DO NOT use real money on a live market without thorough paper trading and review.**
- Store your API keys and secrets securely (`.env`).
- Run in a sandboxed brokerage account or with appropriate risk controls.

## Contributing

Pull requests and discussions are welcome!

## License

MIT License

# Stock Analysis Agent

A modular stock analysis system built using Google ADK (Agent Development Kit) that provides comprehensive stock analysis including price changes, news analysis, and market insights.

## Features

- Stock ticker identification from natural language queries
- Price change analysis over different timeframes
- News analysis and sentiment detection
- Market context and volatility analysis
- Modular architecture for easy extension

## Prerequisites

- Python 3.11 or higher
- Google ADK CLI installed
- API keys for:
  - OpenAI (for LLM)
  - Polygon.io (for stock price data)
  - Finnhub (for company information and news)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd StockAnalysisAgent
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

5. Add your API keys to the `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
POLYGON_API_KEY=your_polygon_api_key
FINNHUB_API_KEY=your_finnhub_api_key
```

## Project Structure

```
stock_analyzer_agent/
├── __init__.py
├── agent.py              # Main agent file
├── config.py            # Configuration and constants
├── models.py            # Pydantic models
└── subagents/
    ├── __init__.py
    ├── identify_ticker/     # Ticker identification subagent
    │   ├── agent.py
    │   └── tools.py
    ├── ticker_analysis/     # Analysis subagent
    │   ├── agent.py
    │   └── tools.py
    ├── ticker_news/         # News subagent
    │   ├── agent.py
    │   └── tools.py
    ├── ticker_price/        # Current price subagent
    │   ├── agent.py
    │   └── tools.py
    └── ticker_price_change/ # Price change subagent
        ├── agent.py
        └── tools.py
```

## Running the Project

1. Ensure you have Google ADK CLI installed:
```bash
pip install google-adk
```

2. Start the ADK web server:
```bash
adk web
```

3. The server will start at `http://localhost:8000` by default.

## API Keys Setup

1. **OpenAI API Key**
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key to your `.env` file

2. **Polygon.io API Key**
   - Visit [Polygon.io](https://polygon.io/dashboard/api-keys)
   - Sign up and create a new API key
   - Copy the key to your `.env` file

3. **Finnhub API Key**
   - Visit [Finnhub](https://finnhub.io/dashboard)
   - Sign up and create a new API key
   - Copy the key to your `.env` file

## Usage

1. Start the ADK web server:
```bash
adk web
```

2. Open your browser and navigate to `http://localhost:8000`

3. You can interact with the agent using natural language queries like:
   - "How has PLTR stock performed in the last week?"
   - "What's the latest news about NVIDIA?"
   - "Analyze the price movement of Tesla stock"

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Contact

📧 Email: [naveenv3112000@gmail.com](mailto:naveenv3112000@gmail.com)

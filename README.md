# Equity Tracker — Layer 1

A free, self-hosted equity tracking suite. Fetches live prices and 1-year historical returns via `yfinance`, merges them with your holdings, and displays a P&L dashboard in the browser.

## Stack

| Layer | Tech |
|-------|------|
| Data  | Python · yfinance · pandas |
| API   | Flask |
| UI    | Vanilla HTML/JS (no build step) |

## Quick start

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit your holdings
#    portfolio.csv  →  Ticker, Shares, Cost Basis

# 4. Run the server
python app.py

# 5. Open the dashboard
open http://localhost:5000
```

## Project layout

```
equity-tracker/
├── app.py            # Flask server + API routes
├── data_engine.py    # yfinance fetching, P&L calculations
├── portfolio.csv     # Your holdings (edit this)
├── requirements.txt
├── templates/
│   └── index.html    # Dashboard (dark-mode table + summary cards)
├── .gitignore
└── README.md
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /api/portfolio` | JSON snapshot — live prices, market value, P&L, 1Y return |

### Sample response

```json
{
  "status": "ok",
  "data": [
    {
      "ticker": "AAPL",
      "shares": 10.0,
      "cost_basis": 150.0,
      "current_price": 189.25,
      "market_value": 1892.50,
      "pnl_dollars": 392.50,
      "pnl_pct": 26.17,
      "return_1y_pct": 18.43
    }
  ]
}
```

## Customising holdings

Edit `portfolio.csv`:

```csv
Ticker,Shares,Cost Basis
AAPL,10,150.00
MSFT,5,280.00
```

- **Ticker** — any symbol supported by Yahoo Finance  
- **Shares** — number of shares held  
- **Cost Basis** — average price paid per share  

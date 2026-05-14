import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def load_portfolio(csv_path: str = "portfolio.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["Ticker"] = df["Ticker"].str.upper().str.strip()
    return df


def save_portfolio(df: pd.DataFrame, csv_path: str = "portfolio.csv") -> None:
    df.to_csv(csv_path, index=False)


def add_holding(ticker: str, shares: float, cost_basis: float, csv_path: str = "portfolio.csv") -> None:
    df = load_portfolio(csv_path)
    ticker = ticker.upper().strip()
    if ticker in df["Ticker"].values:
        df.loc[df["Ticker"] == ticker, "Shares"] = shares
        df.loc[df["Ticker"] == ticker, "Cost Basis"] = cost_basis
    else:
        new_row = pd.DataFrame([{"Ticker": ticker, "Shares": shares, "Cost Basis": cost_basis}])
        df = pd.concat([df, new_row], ignore_index=True)
    save_portfolio(df, csv_path)


def remove_holding(ticker: str, csv_path: str = "portfolio.csv") -> None:
    df = load_portfolio(csv_path)
    df = df[df["Ticker"] != ticker.upper().strip()]
    save_portfolio(df, csv_path)


def fetch_current_prices(tickers: list[str]) -> dict[str, float]:
    data = yf.download(tickers, period="2d", auto_adjust=True, progress=False)
    prices = {}
    if len(tickers) == 1:
        close = data["Close"]
        prices[tickers[0]] = float(close.dropna().iloc[-1])
    else:
        for ticker in tickers:
            try:
                col = data["Close"][ticker].dropna()
                prices[ticker] = float(col.iloc[-1])
            except (KeyError, IndexError):
                prices[ticker] = None
    return prices


def fetch_one_year_returns(tickers: list[str]) -> dict[str, float | None]:
    end = datetime.today()
    start = end - timedelta(days=365)
    data = yf.download(
        tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
        auto_adjust=True, progress=False
    )
    returns = {}
    if len(tickers) == 1:
        close = data["Close"].dropna()
        if len(close) >= 2:
            returns[tickers[0]] = round((float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100, 2)
        else:
            returns[tickers[0]] = None
    else:
        for ticker in tickers:
            try:
                col = data["Close"][ticker].dropna()
                if len(col) >= 2:
                    returns[ticker] = round((float(col.iloc[-1]) / float(col.iloc[0]) - 1) * 100, 2)
                else:
                    returns[ticker] = None
            except KeyError:
                returns[ticker] = None
    return returns


def fetch_price_history(tickers: list[str], period: str = "1y") -> dict:
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    close = data["Close"]

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0])

    dates = [d.strftime("%Y-%m-%d") for d in close.index]
    series = {}
    for ticker in tickers:
        try:
            col = close[ticker]
            first_valid = col.first_valid_index()
            if first_valid is None:
                continue
            base = float(col[first_valid])
            series[ticker] = [
                round((float(v) / base - 1) * 100, 2) if pd.notna(v) else None
                for v in col
            ]
        except KeyError:
            pass

    return {"dates": dates, "series": series}


def build_portfolio_snapshot(csv_path: str = "portfolio.csv") -> list[dict]:
    portfolio = load_portfolio(csv_path)
    tickers = portfolio["Ticker"].tolist()

    prices = fetch_current_prices(tickers)
    returns = fetch_one_year_returns(tickers)

    rows = []
    for _, row in portfolio.iterrows():
        ticker = row["Ticker"]
        shares = float(row["Shares"])
        cost_basis = float(row["Cost Basis"])
        current_price = prices.get(ticker)

        if current_price is None:
            market_value = None
            pnl_dollars = None
            pnl_pct = None
        else:
            market_value = round(shares * current_price, 2)
            total_cost = shares * cost_basis
            pnl_dollars = round(market_value - total_cost, 2)
            pnl_pct = round((pnl_dollars / total_cost) * 100, 2) if total_cost else None

        rows.append({
            "ticker": ticker,
            "shares": shares,
            "cost_basis": cost_basis,
            "current_price": round(current_price, 2) if current_price else None,
            "market_value": market_value,
            "pnl_dollars": pnl_dollars,
            "pnl_pct": pnl_pct,
            "return_1y_pct": returns.get(ticker),
        })

    return rows

import os
import shutil
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

PORTFOLIOS_DIR = "portfolios"


def _ensure_dir():
    os.makedirs(PORTFOLIOS_DIR, exist_ok=True)


def _portfolio_path(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "-_ ")
    return os.path.join(PORTFOLIOS_DIR, f"{safe}.csv")


def list_portfolio_names() -> list[str]:
    _ensure_dir()
    legacy = "portfolio.csv"
    if os.path.exists(legacy) and not any(f.endswith(".csv") for f in os.listdir(PORTFOLIOS_DIR)):
        shutil.copy(legacy, _portfolio_path("Main"))
    return sorted(f[:-4] for f in os.listdir(PORTFOLIOS_DIR) if f.endswith(".csv"))


def load_portfolio(name: str) -> pd.DataFrame:
    path = _portfolio_path(name)
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Ticker", "Shares", "Cost Basis"])
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df["Ticker"] = df["Ticker"].str.upper().str.strip()
    return df


def save_portfolio(df: pd.DataFrame, name: str) -> None:
    _ensure_dir()
    df.to_csv(_portfolio_path(name), index=False)


def create_portfolio(name: str) -> None:
    _ensure_dir()
    path = _portfolio_path(name)
    if os.path.exists(path):
        raise ValueError(f"Portfolio '{name}' already exists")
    pd.DataFrame(columns=["Ticker", "Shares", "Cost Basis"]).to_csv(path, index=False)


def delete_portfolio(name: str) -> None:
    path = _portfolio_path(name)
    if os.path.exists(path):
        os.remove(path)


def add_holding(name: str, ticker: str, shares: float, cost_basis: float) -> None:
    df = load_portfolio(name)
    ticker = ticker.upper().strip()
    if ticker in df["Ticker"].values:
        df.loc[df["Ticker"] == ticker, "Shares"] = shares
        df.loc[df["Ticker"] == ticker, "Cost Basis"] = cost_basis
    else:
        df = pd.concat(
            [df, pd.DataFrame([{"Ticker": ticker, "Shares": shares, "Cost Basis": cost_basis}])],
            ignore_index=True,
        )
    save_portfolio(df, name)


def remove_holding(name: str, ticker: str) -> None:
    df = load_portfolio(name)
    df = df[df["Ticker"] != ticker.upper().strip()]
    save_portfolio(df, name)


def _download_close(tickers: list[str], **kwargs) -> pd.DataFrame:
    data = yf.download(tickers, auto_adjust=True, progress=False, **kwargs)
    close = data["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0])
    return close


def fetch_current_prices(tickers: list[str]) -> dict[str, float | None]:
    if not tickers:
        return {}
    close = _download_close(tickers, period="2d")
    return {t: (float(close[t].dropna().iloc[-1]) if t in close else None) for t in tickers}


def fetch_one_year_returns(tickers: list[str]) -> dict[str, float | None]:
    if not tickers:
        return {}
    end = datetime.today()
    start = end - timedelta(days=365)
    close = _download_close(
        tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
    )
    returns = {}
    for t in tickers:
        try:
            col = close[t].dropna()
            returns[t] = round((float(col.iloc[-1]) / float(col.iloc[0]) - 1) * 100, 2) if len(col) >= 2 else None
        except (KeyError, IndexError):
            returns[t] = None
    return returns


def fetch_price_history(name: str, period: str = "1y") -> dict:
    tickers = load_portfolio(name)["Ticker"].tolist()
    if not tickers:
        return {"dates": [], "series": {}}
    close = _download_close(tickers, period=period)
    dates = [d.strftime("%Y-%m-%d") for d in close.index]
    series = {}
    for t in tickers:
        try:
            col = close[t]
            first = col.first_valid_index()
            if first is None:
                continue
            base = float(col[first])
            series[t] = [round((float(v) / base - 1) * 100, 2) if pd.notna(v) else None for v in col]
        except KeyError:
            pass
    return {"dates": dates, "series": series}


def build_portfolio_snapshot(name: str) -> list[dict]:
    df = load_portfolio(name)
    tickers = df["Ticker"].tolist()
    if not tickers:
        return []
    prices = fetch_current_prices(tickers)
    returns = fetch_one_year_returns(tickers)
    rows = []
    for _, row in df.iterrows():
        t = row["Ticker"]
        shares = float(row["Shares"])
        cb = float(row["Cost Basis"])
        price = prices.get(t)
        if price is None:
            mv = pnl_d = pnl_p = None
        else:
            mv = round(shares * price, 2)
            cost = shares * cb
            pnl_d = round(mv - cost, 2)
            pnl_p = round(pnl_d / cost * 100, 2) if cost else None
        rows.append({
            "ticker": t, "shares": shares, "cost_basis": cb,
            "current_price": round(price, 2) if price else None,
            "market_value": mv, "pnl_dollars": pnl_d, "pnl_pct": pnl_p,
            "return_1y_pct": returns.get(t),
        })
    return rows


def build_portfolios_summary() -> list[dict]:
    names = list_portfolio_names()
    if not names:
        return []
    portfolios = {n: load_portfolio(n) for n in names}
    all_tickers = list({t for df in portfolios.values() for t in df["Ticker"].tolist()})
    prices = fetch_current_prices(all_tickers) if all_tickers else {}
    returns = fetch_one_year_returns(all_tickers) if all_tickers else {}
    summaries = []
    for name, df in portfolios.items():
        total_value = total_cost = weighted_return = 0.0
        for _, row in df.iterrows():
            t = row["Ticker"]
            shares, cb = float(row["Shares"]), float(row["Cost Basis"])
            total_cost += shares * cb
            price = prices.get(t)
            if price:
                mv = shares * price
                total_value += mv
                weighted_return += mv * (returns.get(t) or 0)
        pnl = total_value - total_cost
        summaries.append({
            "name": name,
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "pnl_dollars": round(pnl, 2),
            "pnl_pct": round(pnl / total_cost * 100, 2) if total_cost else None,
            "return_1y_pct": round(weighted_return / total_value, 2) if total_value else None,
        })
    return summaries

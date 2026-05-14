from flask import Flask, jsonify, render_template, request
from data_engine import build_portfolio_snapshot, fetch_price_history, load_portfolio, add_holding, remove_holding

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/portfolio")
def portfolio():
    try:
        data = build_portfolio_snapshot()
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/history")
def history():
    period = request.args.get("period", "1y")
    if period not in ("1mo", "3mo", "6mo", "1y"):
        period = "1y"
    try:
        tickers = load_portfolio()["Ticker"].tolist()
        data = fetch_price_history(tickers, period)
        return jsonify({"status": "ok", **data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/holdings", methods=["POST"])
def add_holding_route():
    body = request.get_json(silent=True) or {}
    ticker = str(body.get("ticker", "")).upper().strip()
    try:
        shares = float(body.get("shares", 0))
        cost_basis = float(body.get("cost_basis", 0))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "shares and cost_basis must be numbers"}), 400
    if not ticker:
        return jsonify({"status": "error", "message": "ticker is required"}), 400
    if shares <= 0 or cost_basis <= 0:
        return jsonify({"status": "error", "message": "shares and cost_basis must be positive"}), 400
    try:
        add_holding(ticker, shares, cost_basis)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/holdings/<ticker>", methods=["DELETE"])
def remove_holding_route(ticker):
    try:
        remove_holding(ticker.upper().strip())
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

from flask import Flask, jsonify, render_template, request
from data_engine import build_portfolio_snapshot, fetch_price_history, load_portfolio

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)

from flask import Flask, jsonify, render_template, request
from data_engine import (
    list_portfolio_names, create_portfolio, delete_portfolio,
    build_portfolios_summary, build_portfolio_snapshot,
    fetch_price_history, add_holding, update_holding, remove_holding,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# --- Portfolio list ---

@app.route("/api/portfolios")
def get_portfolios():
    try:
        return jsonify({"status": "ok", "data": build_portfolios_summary()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolios", methods=["POST"])
def new_portfolio():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"status": "error", "message": "name is required"}), 400
    try:
        create_portfolio(name)
        return jsonify({"status": "ok"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolios/<name>", methods=["DELETE"])
def del_portfolio(name):
    try:
        delete_portfolio(name)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Holdings ---

@app.route("/api/portfolios/<name>/holdings")
def get_holdings(name):
    try:
        return jsonify({"status": "ok", "data": build_portfolio_snapshot(name)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolios/<name>/holdings", methods=["POST"])
def add_holding_route(name):
    body = request.get_json(silent=True) or {}
    ticker = str(body.get("ticker", "")).upper().strip()
    purchase_date = str(body.get("purchase_date", "") or "").strip()
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
        add_holding(name, ticker, shares, cost_basis, purchase_date)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolios/<name>/holdings/<lot_id>", methods=["PUT"])
def update_holding_route(name, lot_id):
    body = request.get_json(silent=True) or {}
    purchase_date = str(body.get("purchase_date", "") or "").strip()
    try:
        shares = float(body.get("shares", 0))
        cost_basis = float(body.get("cost_basis", 0))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "shares and cost_basis must be numbers"}), 400
    if shares <= 0 or cost_basis <= 0:
        return jsonify({"status": "error", "message": "shares and cost_basis must be positive"}), 400
    try:
        update_holding(name, lot_id, shares, cost_basis, purchase_date)
        return jsonify({"status": "ok"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/portfolios/<name>/holdings/<lot_id>", methods=["DELETE"])
def remove_holding_route(name, lot_id):
    try:
        remove_holding(name, lot_id)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- History ---

@app.route("/api/portfolios/<name>/history")
def history(name):
    period = request.args.get("period", "1y")
    if period not in ("1mo", "3mo", "6mo", "1y"):
        period = "1y"
    try:
        data = fetch_price_history(name, period)
        return jsonify({"status": "ok", **data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

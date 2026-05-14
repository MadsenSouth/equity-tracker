from flask import Flask, jsonify, render_template
from data_engine import build_portfolio_snapshot

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)

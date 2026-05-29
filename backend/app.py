from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes import bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["DEBUG"]      = Config.DEBUG

    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/health": {"origins": "*"},
    })

    app.register_blueprint(bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    if not Config.BRIGHT_DATA_API_KEY:
        print(" WARNING: BRIGHT_DATA_API_KEY not set in .env")
    else:
        print("Bright Data API key loaded")

    print(f" OncoMarket backend starting on port {Config.PORT}")
    print(f"   Endpoints: /health | /api/fetch | /api/raw-data | /api/signals | /api/status")

    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)

from flask import Flask, redirect, url_for, jsonify, request, render_template
from datetime import timedelta
from extensions import db, jwt, migrate, limiter
import os
from dotenv import load_dotenv
from flask_socketio import SocketIO

# Load environment variables from .env file
load_dotenv()

# Initialize SocketIO for WebSocket support
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)


def create_app():
    app = Flask(__name__)

    # ---------------- CONFIG ----------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ui-session-secret")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///traffic.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["API_TITLE"] = "Traffic Accident Information System API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/api"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    # ---------------- INIT EXTENSIONS ----------------
    limiter.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # ---------------- AFTER REQUEST (UI TRANSITIONS) ----------------
    @app.after_request
    def add_view_transition_headers(response):
        try:
            if request.path.startswith("/ui"):
                ct = (response.headers.get("Content-Type") or "").lower()
                if ct.startswith("text/html"):
                    response.headers.setdefault("View-Transition", "same-origin")
        except Exception:
            pass
        return response

    # ---------------- ERROR HANDLERS ----------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("404.html"), 500

    from utils.errors import APIError, RateLimitError

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return error.to_response()

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return RateLimitError().to_response()

    # ---------------- REQUEST / RESPONSE LOGGING ----------------
    @app.before_request
    def log_request():
        if not request.path.startswith("/api"):
            return
        from flask import g
        from datetime import datetime

        g.request_start_time = datetime.utcnow()
        g.request_path = request.path
        g.request_method = request.method

    @app.after_request
    def log_response(response):
        if not request.path.startswith("/api"):
            return response
        try:
            from flask import g
            from datetime import datetime
            from models.audit_log import AuditLog
            from flask_jwt_extended import get_jwt_identity

            if hasattr(g, "request_start_time"):
                elapsed = (datetime.utcnow() - g.request_start_time).total_seconds()
                try:
                    user_id = get_jwt_identity()
                except Exception:
                    user_id = None

                if request.method in ("POST", "PATCH", "PUT", "DELETE") or response.status_code >= 400:
                    action_map = {
                        "POST": "create",
                        "PATCH": "update",
                        "PUT": "update",
                        "DELETE": "delete",
                        "GET": "read",
                    }
                    audit_log = AuditLog(
                        user_id=user_id,
                        action=action_map.get(request.method, "api_call"),
                        entity_type="api_request",
                        description=f"{request.method} {request.path} -> {response.status_code} ({elapsed:.2f}s)",
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get("User-Agent", "")[:500],
                    )
                    db.session.add(audit_log)
                    db.session.commit()
        except Exception as e:
            print(f"Audit log error: {e}")
        return response

    # ---------------- DB INIT & SAFETY ----------------
    import sqlalchemy as sa

    with app.app_context():
        from models.user import User
        from models.accident import Accident
        from models.import_batch import ImportBatch
        from models.accident_report import AccidentReport

        db.create_all()

        try:
            with db.engine.connect() as conn:
                insp = conn.execute(sa.text("PRAGMA table_info('accidents')")).fetchall()
            cols = [row[1] for row in insp]

            if "batch_id" not in cols:
                db.engine.execute(sa.text("ALTER TABLE accidents ADD COLUMN batch_id INTEGER"))
        except Exception:
            pass

        from utils.create_gov_user import create_government_user
        create_government_user()

    # ---------------- FILE IMPORT API ----------------
    from resources.import_data import import_api
    app.register_blueprint(import_api)

    # ---------------- SMOREST API ----------------
    from flask_smorest import Api

    api = Api(app)

    from resources.auth import blp as AuthAPI
    from resources.accidents import blp as AccidentAPI
    from resources.stats import blp as StatsAPI
    from resources.meta import blp as MetaAPI

    api.register_blueprint(AuthAPI)
    api.register_blueprint(AccidentAPI)
    api.register_blueprint(StatsAPI)
    api.register_blueprint(MetaAPI)

    # ---------------- OTHER APIS ----------------
    from resources.accident_report import reports_bp
    from resources.users import users_bp
    from resources.export import export_bp
    from resources.upload import upload_bp
    from resources.search import search_bp
    from resources.contact import contact_bp
    from resources.chatbot import chatbot_bp
    from resources.services import services_bp

    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(services_bp)

    # ---------------- UI ----------------
    from ui.auth_ui import auth_ui
    from ui.dashboard_ui import dashboard_ui
    from ui.accidents_ui import accidents_ui
    from ui.import_ui import import_ui
    from ui.account_ui import account_ui
    from ui.register_ui import register_ui
    from ui.users_ui import users_ui
    from ui.report_ui import report_ui
    from ui.gov_reports_ui import gov_reports_ui
    from ui.stats_ui import stats_ui
    from ui.services_ui import services_ui
    from ui.landing_ui import landing_ui
    from ui.info_ui import info_ui
    from ui.oauth_routes import oauth_ui

    from ui.oauth import init_oauth
    init_oauth(app)

    app.register_blueprint(auth_ui, url_prefix="/ui")
    app.register_blueprint(dashboard_ui, url_prefix="/ui")
    app.register_blueprint(accidents_ui, url_prefix="/ui")
    app.register_blueprint(import_ui, url_prefix="/ui")
    app.register_blueprint(account_ui, url_prefix="/ui")
    app.register_blueprint(register_ui, url_prefix="/ui")
    app.register_blueprint(users_ui, url_prefix="/ui")
    app.register_blueprint(report_ui, url_prefix="/ui")
    app.register_blueprint(gov_reports_ui, url_prefix="/ui")
    app.register_blueprint(stats_ui, url_prefix="/ui")
    app.register_blueprint(services_ui, url_prefix="/ui")
    app.register_blueprint(landing_ui)
    app.register_blueprint(info_ui)
    app.register_blueprint(oauth_ui)

    from resources.websocket_handler import init_websocket
    init_websocket(app, socketio)

    return app, socketio


# --------------------------------------------------
# ✅ WSGI ENTRYPOINT (THIS IS WHAT GUNICORN NEEDS)
# --------------------------------------------------
app, socketio = create_app()


# --------------------------------------------------
# LOCAL DEVELOPMENT ONLY (WINDOWS)
# --------------------------------------------------
if __name__ == "__main__":
    socketio.run(
        app,
        debug=True,
        port=5001,
        allow_unsafe_werkzeug=True,
    )

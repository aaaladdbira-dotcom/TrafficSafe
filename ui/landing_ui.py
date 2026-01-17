from flask import Blueprint, render_template

landing_ui = Blueprint("landing_ui", __name__)


@landing_ui.route("/")
def landing():
    """Public landing page with rotating awareness phrases."""
    return render_template("landing.html")

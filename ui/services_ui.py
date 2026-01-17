from flask import Blueprint, render_template, session
from .utils import login_required

services_ui = Blueprint("services_ui", __name__)


@services_ui.route("/services")
@login_required
def services():
    """Main services and tools page"""
    return render_template("services.html")


@services_ui.route("/traffic-news")
@login_required
def traffic_news():
    """Traffic news and alerts page"""
    return render_template("traffic_news.html")

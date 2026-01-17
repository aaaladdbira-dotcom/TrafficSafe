from flask import Blueprint, render_template
from .utils import login_required

stats_ui = Blueprint("stats_ui", __name__)

@stats_ui.route("/stats")
@login_required
def stats():
    return render_template("statistics.html")

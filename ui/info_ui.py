from flask import Blueprint, render_template

info_ui = Blueprint("info_ui", __name__)


@info_ui.route("/about")
def about():
    """About page with company information."""
    return render_template("about.html")


@info_ui.route("/faq")
def faq():
    """FAQ page with frequently asked questions."""
    return render_template("faq.html")


@info_ui.route("/privacy")
def privacy():
    """Privacy policy page."""
    return render_template("privacy.html")


@info_ui.route("/terms")
def terms():
    """Terms of service page."""
    return render_template("terms.html")


@info_ui.route("/contact")
def contact():
    """Contact us page with feedback form."""
    return render_template("contact_us.html")

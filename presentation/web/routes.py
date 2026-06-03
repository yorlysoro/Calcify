from flask import Blueprint, render_template

from presentation.api.auth import login_required

web_bp: Blueprint = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")


@web_bp.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

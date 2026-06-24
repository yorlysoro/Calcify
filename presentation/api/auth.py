# BSD 3-Clause License
#
# Copyright (c) 2026, yorlysoro
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Authentication module for the Calcify application.

Provides session-based PIN authentication via Flask Blueprint (auth_bp),
the login_required decorator for route protection, and login/logout endpoints.
"""

import logging
from functools import wraps
from typing import Callable, Any, Tuple, Dict, Optional

from flask import Blueprint, request, jsonify, session, redirect, url_for, g, Response
from flask_babel import _
from werkzeug.security import check_password_hash

# Infrastructure Imports (Adapters only)
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository

logger: logging.Logger = logging.getLogger(__name__)

auth_bp: Blueprint = Blueprint("auth", __name__)


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to protect routes from unauthenticated access.

    Dynamically responds based on the request path:
    - API endpoints (/api/...) get a 401 Unauthorized JSON response.
    - Web routes get an HTTP 302 redirect to the login interface.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get("authenticated"):
            # REST API rejection
            if request.path.startswith("/api/"):
                return jsonify({"error": _("Unauthorized access. Please log in.")}), 401

            # Browser redirection (Assuming a 'web.login_page' route will exist)
            # Fallback to a plain 401 if you don't have a web blueprint yet
            return redirect(url_for("web.login"))

        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/login", methods=["POST"])
def login() -> Tuple[Response, int]:
    """
    Authenticates the administrative user via a PIN/Password.

    Expects a JSON payload: {"pin": "admin123"}
    On success, upgrades the Flask session to permanent and marks it authenticated.
    """
    payload: Optional[Dict[str, Any]] = request.get_json()

    if not payload or "pin" not in payload:
        return jsonify({"error": _("Missing 'pin' in request payload.")}), 400

    raw_pin: str = str(payload["pin"])

    # Instantiate the repository using the global Flask request context session
    repo = SqlAlchemyConfigRepository(session=g.db_session)

    try:
        # Retrieve the master hash from the SQLite database
        stored_hash: Optional[str] = repo.get_value("admin_password_hash")

        if not stored_hash:
            logger.critical(
                "Authentication bypassed attempt: No admin hash found in DB."
            )
            return (
                jsonify({"error": _("System not initialized. Run security setup.")}),
                500,
            )

        # Cryptographic constant-time comparison to prevent timing attacks
        if check_password_hash(stored_hash, raw_pin):
            # Session Upgrade
            session.clear()  # Prevent session fixation attacks
            session["authenticated"] = True
            session.permanent = True  # Extends cookie life beyond browser close

            logger.info("Admin successfully authenticated.")
            return jsonify({"message": _("Authentication successful.")}), 200
        else:
            # We deliberately use generic error messages to avoid leaking information
            logger.warning("Failed login attempt: Invalid PIN.")
            return jsonify({"error": _("Invalid credentials.")}), 401

    except Exception as e:
        logger.error(f"Login process failed internally: {str(e)}")
        return jsonify({"error": _("Internal server error during authentication.")}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Tuple[Response, int]:
    """
    Terminates the user's active session.
    """
    session.clear()
    return jsonify({"message": _("Logged out successfully.")}), 200

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

"""Tests for app.py uncovered branches: locale, error handler, production path."""

from pathlib import Path
from flask import session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


def test_get_locale_from_session(client):
    """get_locale returns session locale when set."""
    with client.application.test_request_context("/"):
        from app import get_locale
        session["locale"] = "es"
        assert get_locale() == "es"


def test_get_locale_from_accept_header(client):
    """get_locale returns language from Accept-Language header."""
    with client.application.test_request_context(
        "/", headers={"Accept-Language": "es"}
    ):
        from app import get_locale
        assert get_locale() == "es"


def test_get_locale_default(client):
    """get_locale returns 'en' when no preference matches."""
    with client.application.test_request_context(
        "/", headers={"Accept-Language": "fr"}
    ):
        from app import get_locale
        assert get_locale() == "en"


def test_set_locale_json_to_spanish(client):
    """POST /api/v1/locale with locale=es sets session['locale'] to 'es'."""
    response = client.post("/api/v1/locale", json={"locale": "es"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["locale"] == "es"

    with client.session_transaction() as sess:
        assert sess.get("locale") == "es"


def test_set_locale_json_invalid_locale(client):
    """POST /api/v1/locale with unsupported locale does NOT update session."""
    response = client.post("/api/v1/locale", json={"locale": "fr"})
    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert sess.get("locale") is None or sess.get("locale") != "fr"


def test_set_locale_json_empty_payload(client):
    """POST /api/v1/locale with empty payload defaults to 'en'."""
    response = client.post("/api/v1/locale", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data["locale"] == "en"


def test_set_locale_get_spanish(client):
    """GET /api/v1/locale/es sets session locale and redirects."""
    response = client.get("/api/v1/locale/es", headers={"Referer": "/"})
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert sess.get("locale") == "es"


def test_set_locale_get_english(client):
    """GET /api/v1/locale/en sets session locale to 'en'."""
    response = client.get("/api/v1/locale/en", headers={"Referer": "/"})
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert sess.get("locale") == "en"


def test_non_http_exception_handler(client):
    """A non-HTTP exception raised in a route returns JSON 500."""
    app = client.application

    @app.route("/trigger-500")
    def trigger_500():
        raise RuntimeError("Something went wrong")

    response = client.get("/trigger-500")
    assert response.status_code == 500
    data = response.get_json()
    assert data["error"] == "Internal Server Error"


def test_index_renders_with_spanish_locale(client) -> None:
    """Render index.html with Spanish locale to catch i18n rendering errors.

    Validates that the full Jinja2 template pipeline (extends, blocks, gettext)
    completes without ValueError/KeyError when the Spanish locale is active.
    This guards against the 'unsupported format character' bug caused by
    literal '%' in translatable strings.
    """
    with client.session_transaction() as sess:
        sess["authenticated"] = True
        sess["locale"] = "es"

    response = client.get("/")

    assert response.status_code == 200
    assert response.data


def test_create_app_production_path(monkeypatch):
    """create_app() without config_name uses production path successfully."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    monkeypatch.setattr("app.create_engine", lambda uri: test_engine)
    monkeypatch.setattr(
        "app.get_db_path",
        lambda name: Path("/tmp/test_calcify/database.sqlite"),
    )
    monkeypatch.setattr("app.bootstrap_migrations", lambda url, metadata: None)
    monkeypatch.setattr("app.initialize_security", lambda name, engine: None)
    monkeypatch.setattr(
        "infrastructure.repositories.sqlalchemy_repos.SqlAlchemyConfigRepository.get_value",
        lambda self, key: "test_secret_123",
    )
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    from app import create_app

    app = create_app()

    assert not app.config["TESTING"]
    assert app.secret_key == "test_secret_123"

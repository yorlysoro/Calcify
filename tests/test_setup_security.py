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

"""Tests for the setup_security.py initialization script."""

import pytest
from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import StaticPool
from infrastructure.database.models import Base
from infrastructure.repositories.sqlalchemy_repos import SqlAlchemyConfigRepository
from werkzeug.security import check_password_hash


@pytest.fixture
def in_memory_engine() -> Generator[Engine, None, None]:
    engine: Engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_initialize_security_idempotent(in_memory_engine: Engine, monkeypatch) -> None:
    """Calling initialize_security twice does not overwrite existing hash."""
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    from setup_security import initialize_security

    initialize_security("Calcify", engine=in_memory_engine)

    with in_memory_engine.connect() as conn:
        from sqlalchemy.orm import Session
        repo = SqlAlchemyConfigRepository(Session(bind=conn))
        hash1 = repo.get_value("admin_password_hash")
        key1 = repo.get_value("app_secret_key")

    initialize_security("Calcify", engine=in_memory_engine)

    with in_memory_engine.connect() as conn:
        repo._session = Session(bind=conn)
        hash2 = repo.get_value("admin_password_hash")
        key2 = repo.get_value("app_secret_key")

    assert hash1 == hash2
    assert key1 == key2


def test_initialize_security_creates_admin_password(in_memory_engine: Engine, monkeypatch) -> None:
    """First run creates an admin password hash via getpass default."""
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    from setup_security import initialize_security

    initialize_security("Calcify", engine=in_memory_engine)

    with in_memory_engine.connect() as conn:
        from sqlalchemy.orm import Session
        repo = SqlAlchemyConfigRepository(Session(bind=conn))
        stored_hash = repo.get_value("admin_password_hash")

    assert stored_hash is not None
    assert check_password_hash(stored_hash, "admin123")


def test_initialize_security_creates_secret_key(in_memory_engine: Engine, monkeypatch) -> None:
    """First run creates an app secret key."""
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    from setup_security import initialize_security

    initialize_security("Calcify", engine=in_memory_engine)

    with in_memory_engine.connect() as conn:
        from sqlalchemy.orm import Session
        repo = SqlAlchemyConfigRepository(Session(bind=conn))
        secret_key = repo.get_value("app_secret_key")

    assert secret_key is not None
    assert len(secret_key) == 32


def test_initialize_security_with_custom_password(in_memory_engine: Engine, monkeypatch) -> None:
    """Custom password provided via getpass is stored correctly."""
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "my_custom_pin")

    from setup_security import initialize_security
    initialize_security("Calcify", engine=in_memory_engine)

    with in_memory_engine.connect() as conn:
        from sqlalchemy.orm import Session
        repo = SqlAlchemyConfigRepository(Session(bind=conn))
        stored_hash = repo.get_value("admin_password_hash")

    assert check_password_hash(stored_hash, "my_custom_pin")

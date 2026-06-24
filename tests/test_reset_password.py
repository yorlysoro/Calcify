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

"""Tests for the reset_password.py CLI security utility."""

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


def _seed_existing_password(engine: Engine, password: str = "old_pass") -> None:
    from werkzeug.security import generate_password_hash
    from sqlalchemy.orm import Session
    from infrastructure.database.models import ConfigModel
    with Session(engine) as session:
        session.merge(ConfigModel(key="admin_password_hash", value=generate_password_hash(password)))
        session.commit()


def test_reset_password_success(in_memory_engine: Engine, monkeypatch) -> None:
    """Successful password reset with matching confirmation."""
    _seed_existing_password(in_memory_engine, "old_pass")
    inputs = iter(["new_secure_pin", "new_secure_pin"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(inputs))
    monkeypatch.setattr("reset_password.create_engine", lambda uri: in_memory_engine)

    from reset_password import reset_admin_password
    reset_admin_password()

    with in_memory_engine.connect() as conn:
        from sqlalchemy.orm import Session
        repo = SqlAlchemyConfigRepository(Session(bind=conn))
        stored_hash = repo.get_value("admin_password_hash")

    assert check_password_hash(stored_hash, "new_secure_pin")


def test_reset_password_mismatch_exits(in_memory_engine: Engine, monkeypatch) -> None:
    """Password reset exits with code 1 when passwords do not match."""
    _seed_existing_password(in_memory_engine, "old_pass")
    inputs = iter(["new_pin", "different_pin"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(inputs))

    from reset_password import reset_admin_password
    with pytest.raises(SystemExit) as exc_info:
        reset_admin_password()
    assert exc_info.value.code == 1


def test_reset_password_empty_exits(in_memory_engine: Engine, monkeypatch) -> None:
    """Password reset exits with code 1 when password is empty."""
    _seed_existing_password(in_memory_engine, "old_pass")
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")

    from reset_password import reset_admin_password
    with pytest.raises(SystemExit) as exc_info:
        reset_admin_password()
    assert exc_info.value.code == 1

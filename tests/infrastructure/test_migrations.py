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

"""Unit tests for infrastructure/database/migrations.py."""

from pathlib import Path
import pytest
from infrastructure.database.migrations import run_migrations


def test_run_migrations_ini_not_found(monkeypatch):
    """When alembic.ini does not exist, run_migrations raises RuntimeError."""
    fake_path = Path("/tmp/nonexistent/database.sqlite")
    monkeypatch.setattr(
        "infrastructure.database.migrations.get_db_path",
        lambda app_name="Calcify": fake_path,
    )

    with pytest.raises(RuntimeError, match="Critical application failure during schema setup."):
        run_migrations("Calcify")


def test_run_migrations_success(monkeypatch, tmp_path):
    """When alembic.ini exists, run_migrations calls alembic.command.upgrade."""
    fake_db_path = tmp_path / "Calcify" / "database.sqlite"
    fake_db_path.parent.mkdir(parents=True)
    fake_db_path.write_text("")

    alembic_ini = tmp_path / "Calcify" / "alembic.ini"
    alembic_ini.write_text("[alembic]\nscript_location = migrations\n")

    migrations_dir = tmp_path / "Calcify" / "migrations"
    migrations_dir.mkdir()

    monkeypatch.setattr(
        "infrastructure.database.migrations.get_db_path",
        lambda app_name="Calcify": fake_db_path,
    )

    upgrade_called = False

    def mock_upgrade(cfg, target):
        nonlocal upgrade_called
        upgrade_called = True
        assert target == "head"

    monkeypatch.setattr("alembic.command.upgrade", mock_upgrade)

    run_migrations("Calcify")
    assert upgrade_called

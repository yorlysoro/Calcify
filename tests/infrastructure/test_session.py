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

"""Tests for the OS-specific database path resolution."""

from pathlib import Path
from infrastructure.database.session import get_db_path


def test_get_db_path_linux_default(monkeypatch):
    """Linux with no XDG_CONFIG_HOME uses ~/.config."""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    fake_home = Path("/home/testuser")
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    result = get_db_path("Calcify")
    assert result == fake_home / ".config" / "Calcify" / "database.sqlite"


def test_get_db_path_linux_xdg(monkeypatch):
    """Linux with XDG_CONFIG_HOME uses that path."""
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/xdg")
    fake_home = Path("/home/testuser")
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    result = get_db_path("Calcify")
    assert result == Path("/custom/xdg") / "Calcify" / "database.sqlite"


def test_get_db_path_windows_appdata(monkeypatch):
    """Windows with APPDATA uses that path."""
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("APPDATA", "C:\\Users\\test\\AppData\\Roaming")
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    result = get_db_path("Calcify")
    expected = Path("C:\\Users\\test\\AppData\\Roaming") / "Calcify" / "database.sqlite"
    assert result == expected


def test_get_db_path_windows_fallback(monkeypatch):
    """Windows without APPDATA falls back to home/AppData/Roaming."""
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    fake_home = Path("C:\\Users\\test")
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    result = get_db_path("Calcify")
    assert result == fake_home / "AppData" / "Roaming" / "Calcify" / "database.sqlite"


def test_get_db_path_macos(monkeypatch):
    """macOS uses ~/Library/Application Support."""
    monkeypatch.setattr("sys.platform", "darwin")
    fake_home = Path("/Users/test")
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
    monkeypatch.setattr("pathlib.Path.mkdir", lambda self, **kwargs: None)

    result = get_db_path("Calcify")
    assert result == fake_home / "Library" / "Application Support" / "Calcify" / "database.sqlite"

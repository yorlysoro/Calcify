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

"""Tests for correct script loading order and template structure."""

import re
from pathlib import Path

TEMPLATES_DIR: Path = (
    Path(__file__).parent.parent.parent / "presentation" / "templates"
)

# JS dependency graph: each file lists the files that must load before it
JS_DEPENDENCIES: dict[str, set[str]] = {
    "login.js": {"i18n.js", "api-client.js"},
    "utils.js": {"i18n.js"},
    "components.js": {"utils.js"},
    "api-client.js": set(),
    "app.js": {"utils.js", "components.js", "api-client.js"},
    "calculator.js": {"utils.js", "api-client.js"},
    "inventory.js": {"utils.js", "components.js", "api-client.js"},
    "config.js": {"utils.js", "components.js", "api-client.js"},
    "reports.js": {"utils.js", "components.js", "api-client.js"},
    "sales.js": {"utils.js", "components.js", "api-client.js"},
}

# Expected scripts per template (in exact order)
EXPECTED_SCRIPTS: dict[str, list[str]] = {
    "login.html": ["i18n.js", "api-client.js", "login.js"],
    "index.html": [
        "i18n.js",
        "utils.js",
        "components.js",
        "api-client.js",
        "calculator.js",
        "inventory.js",
        "config.js",
        "reports.js",
        "sales.js",
        "app.js",
    ],
}


def _extract_script_srcs(template_path: Path) -> list[str]:
    """Extract JS filenames from script tags in the scripts block of a template."""
    content: str = template_path.read_text(encoding="utf-8")
    scripts_block: str = content.split("{% block scripts %}")[-1].split(
        "{% endblock %}"
    )[0]
    srcs: list[str] = []
    for line in scripts_block.splitlines():
        stripped: str = line.strip()
        if 'src="{{ url_for(' in stripped and "filename=" in stripped:
            start: int = stripped.find("filename='") + len("filename='")
            end: int = stripped.find("'", start)
            if start > len("filename='") - 1 and end > start:
                filename: str = stripped[start:end]
                # Strip the 'js/' prefix for consistent comparison
                if filename.startswith("js/"):
                    filename = filename[3:]
                srcs.append(filename)
    return srcs


def test_login_html_loads_api_client_before_login_js() -> None:
    """Verify api-client.js is loaded before login.js on the login page."""
    template_path: Path = TEMPLATES_DIR / "login.html"
    srcs: list[str] = _extract_script_srcs(template_path)

    assert "api-client.js" in srcs, (
        "login.html is missing api-client.js — login.js calls ApiClient.post() "
        "but ApiClient is never loaded. Add api-client.js before login.js."
    )

    api_idx: int = srcs.index("api-client.js")
    login_idx: int = srcs.index("login.js")
    assert api_idx < login_idx, (
        "api-client.js must be loaded BEFORE login.js in login.html"
    )


def test_index_html_has_all_expected_scripts() -> None:
    """Verify index.html loads the full script list in the correct order."""
    template_path: Path = TEMPLATES_DIR / "index.html"
    actual: list[str] = _extract_script_srcs(template_path)
    expected: list[str] = EXPECTED_SCRIPTS["index.html"]

    assert actual == expected, (
        f"index.html scripts mismatch.\n"
        f"  Expected: {expected}\n"
        f"  Actual:   {actual}"
    )


def test_all_scripts_satisfy_dependencies_in_index() -> None:
    """Verify every JS file's dependencies are loaded before it in index.html."""
    template_path: Path = TEMPLATES_DIR / "index.html"
    srcs: list[str] = _extract_script_srcs(template_path)
    loaded: set[str] = set()

    for filename in srcs:
        deps: set[str] = JS_DEPENDENCIES.get(filename, set())
        missing: set[str] = deps - loaded
        assert not missing, (
            f"{filename} depends on {missing} but they are not loaded "
            f"before it in index.html"
        )
        loaded.add(filename)


def _extract_gettext_strings(text: str) -> list[str]:
    """Extract all message strings from _(\"...\") calls in a file."""
    return re.findall(r'_\("([^"]*?)"\)', text)


def _has_bare_percent(s: str) -> bool:
    """Check if a string contains a literal '%' that is not escaped as '%%'
    or part of a variable substitution like '%(name)s'."""
    i: int = 0
    while i < len(s):
        if s[i] == "%":
            if i + 1 < len(s):
                nxt: str = s[i + 1]
                if nxt == "%":
                    i += 2
                    continue
                if nxt == "(":
                    i += 1
                    continue
            return True
        i += 1
    return False


JS_DIR: Path = Path(__file__).parent.parent.parent / "static" / "js"
TEMPLATE_FILES: list[str] = ["login.html", "index.html", "base.html"]


def test_no_literal_percent_in_gettext_strings() -> None:
    """Verify no translatable string contains a bare '%' that would crash Jinja2.

    Jinja2's gettext extension uses Python's % operator for variable substitution.
    A bare '%' followed by an invalid character (e.g., '%)') raises
    ValueError: unsupported format character. Strings must use '%%' for
    literal percent signs or '%(var)s' for variable substitution.
    """
    errors: list[str] = []

    for filename in TEMPLATE_FILES:
        template_path: Path = TEMPLATES_DIR / filename
        if not template_path.exists():
            continue
        content: str = template_path.read_text(encoding="utf-8")
        strings: list[str] = _extract_gettext_strings(content)

        for s in strings:
            if _has_bare_percent(s):
                errors.append(
                    f"{filename}: _(\"{s}\") contains a bare '%' that will crash "
                    f"Jinja2 rendering. Use '%%' for a literal percent sign "
                    f"instead."
                )

    assert not errors, (
        f"Found {len(errors)} translatable string(s) with unsafe '%' characters:\n"
        + "\n".join(errors)
    )


def _get_function_body(source: str, func_name: str) -> str:
    """Extract the body of a named function from JS source code."""
    pattern: str = func_name + r":\s*function\s*\(\s*\)\s*\{"
    match = re.search(pattern, source)
    assert match, f"Function '{func_name}' not found in JS source"
    brace_start: int = source.index("{", match.start())
    depth: int = 0
    end_idx: int = brace_start
    for i in range(brace_start, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break
    return source[brace_start + 1 : end_idx]


def test_inventory_initModal_has_no_event_listeners() -> None:
    """Verify InventoryView.initModal() does NOT attach event listeners.

    Event listener duplication caused N products to be created per form submit.
    Listeners were moved to _initEventListeners() called once from init().
    Calling initModal() multiple times (e.g. after currency creation in
    ConfigView) must NOT add duplicate submit handlers.
    """
    js_path: Path = JS_DIR / "inventory.js"
    content: str = js_path.read_text(encoding="utf-8")
    body: str = _get_function_body(content, "initModal")

    assert "addEventListener" not in body, (
        "InventoryView.initModal() contains addEventListener() calls. "
        "When initModal() is called multiple times (once from InventoryView.init() "
        "and again from ConfigView after currency creation), each call adds "
        "a duplicate submit handler. Move all addEventListener() calls to "
        "_initEventListeners() which runs once from init()."
    )
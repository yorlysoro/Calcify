# Calcify v0.9.1

Calcify is an open-source financial application for inventory and currency management, built on **Clean Architecture** to ensure maintainability, scalability, and mathematical precision using `Decimal` (preventing floating-point errors).

## Architecture

Calcify follows a strict 4-layer Clean Architecture pattern:

| Layer | Depends on | Banned imports |
|-------|-----------|----------------|
| `domain/` | Python stdlib | Flask, SQLAlchemy, any framework |
| `use_cases/` | Domain entities, abstract repo interfaces | ORM models, Flask |
| `infrastructure/` | SQLAlchemy, domain entities, interfaces | Flask globals (`request`, `g`, `session`) |
| `presentation/` | Flask, domain entities, repo implementations | ORM models directly |

## Project Structure

```text
Calcify/
├── app.py                    # Application Factory (Flask + Babel)
├── domain/                   # Business logic (pure Python, no dependencies)
│   ├── models.py             # Currency, Product, Transaction, CurrencyRate entities
│   ├── exceptions.py         # InvalidExchangeRateError
│   └── services/             # CurrencyConverter (Decimal math, ROUND_HALF_UP)
├── use_cases/                # Orchestration: sales, currency conversion, backup export
├── infrastructure/           # Data layer (SQLAlchemy, SQLite, Alembic migrations)
│   ├── database/
│   │   ├── models.py         # ORM models (5 tables)
│   │   ├── session.py        # OS-agnostic database path resolution
│   │   └── auto_migrate.py   # Automatic schema migrations on startup
│   └── repositories/
│       ├── interfaces.py     # Abstract repository interfaces
│       └── sqlalchemy_repos.py  # Concrete implementations with domain mapping
├── presentation/             # REST API and Web (Flask Blueprints)
│   ├── api/
│   │   ├── auth.py           # Session-based auth, @login_required decorator
│   │   └── routes.py         # 16 REST endpoints + 2 locale endpoints
│   ├── web/
│   │   └── routes.py         # Web routes (/, /login)
│   └── templates/
│       ├── base.html         # Base template with Tailwind CSS
│       ├── index.html        # SPA main view
│       └── login.html        # Login page
├── static/                   # Frontend assets
│   ├── css/                  # 7 view-specific CSS files (cyberpunk theme)
│   ├── js/                   # 11 plain JS modules (no ES modules, global vars)
│   └── dist/tailwind.css     # Built Tailwind CSS
├── tests/                    # 256 tests (159 backend + 97 frontend)
│   ├── domain/               # Currency converter, model tests
│   ├── use_cases/            # Sales, conversion, backup tests
│   ├── infrastructure/       # Migrations, session, repository tests
│   ├── presentation/         # App factory, API routes, auth tests
│   └── frontend/             # Jest + jsdom tests for all JS views
├── translations/             # Babel i18n catalogs (Spanish + English)
├── requirements.txt          # Python dependencies
├── package.json              # Frontend build scripts (Tailwind CSS, Jest)
├── reset_password.py         # CLI tool for PIN recovery
├── setup_security.py         # Bootstrap security (admin PIN, secret key)
└── run_coverage.py           # Cross-platform coverage report
```

## Installation

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)

### Steps (Windows & Linux)

1. Clone or download the project. Open a terminal in the project root.

2. Create a virtual environment:

   **Windows:**
   ```bash
   python -m venv venv
   ```

   **Linux:**
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **Linux:**
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. The database is created and migrated automatically on first startup — no manual setup required.

## Running the Application

Start the server:

**Windows:**
```bash
python app.py
```

**Linux:**
```bash
python3 app.py
```

Open your browser at **http://localhost:5000**.

## Initial Security Setup

### First Run (PIN Creation)

On the first launch, Calcify will prompt you in the terminal to create a master PIN. This PIN is used for all subsequent logins.

### Password Reset

If you forget your PIN, run the following command and follow the on-screen instructions:

```bash
python reset_password.py
```

## Usage Guide

### Login
Enter your master PIN on the login screen.

### Currencies & Exchange Rates
Navigate to **Configuration**. Register your currencies (e.g., USD, VES, EUR) and set the **Base Currency**. Add exchange rates for each currency.

### Inventory
Register products with cost price, currency, and margin percentage. The system automatically calculates the sale price.

### Calculator
Real-time currency conversion based on your registered exchange rates. All calculations use `Decimal` precision.

### Sales
Register inventory outflows. This creates transactions and updates stock quantities automatically.

### Reports
View daily transaction summaries. Filter by date and export to CSV.

### Backup
In the Configuration panel, download a JSON file containing all your data.

## Financial Conversion Logic

Calcify uses fixed-precision arithmetic to prevent banker's rounding errors.

### Formula

```
Converted Amount = (Original Amount × Target Inverse Rate) / Source Inverse Rate
```

### Precision

- Calculations: `Decimal` with `ROUND_HALF_UP` to 4 decimal places
- Display: Rounded to 2 decimal places for user-facing values

If a rate is zero, the system raises `InvalidExchangeRateError`.

## Tests & Coverage

The project maintains **90% backend coverage** (1039/1153 statements).

### Running Tests

```bash
# All backend tests
python -m pytest

# With coverage report
python run_coverage.py

# Frontend tests (Jest + jsdom)
npm test
```

### Test Distribution (256 total)

| Suite | Count | Coverage Target |
|-------|-------|-----------------|
| Domain | 14 | 100% |
| Use cases | 19 | 95-100% |
| Infrastructure | 25 | 81-100% |
| Presentation | 92 | 81-95% |
| Frontend (Jest) | 97 | Defensive JS |

Coverage goals: 100% in `domain/` and `use_cases/` layers.

## Internationalization (i18n)

Calcify supports **English** (default) and **Spanish**, with a system designed for easy addition of new languages.

### How It Works

- **Backend:** Flask-Babel extracts translatable strings from Python code (`_("string")`) and Jinja2 templates (`{{ _("string") }}`).
- **Frontend:** A global `__(key)` function in `static/js/i18n.js` looks up translations from the `_t` object, which is injected by the Flask context processor into every page.
- **Locale selection:** The system checks `session["locale"]` first, then the browser's `Accept-Language` header, falling back to English.

### Adding a New Language

1. **Extract translatable strings:**
   ```bash
   pybabel extract -F babel.cfg -o messages.pot .
   ```

2. **Initialize a new language catalog** (replace `fr` with your language code):
   ```bash
   pybabel init -i messages.pot -d translations -l fr
   ```

3. **Translate:** Edit `translations/fr/LC_MESSAGES/messages.po` — fill in the `msgstr` fields with your translations.

4. **Compile:**
   ```bash
   pybabel compile -d translations
   ```

5. **Register the locale in `app.py`:** Add your language code to the `best_match` list in `get_locale()`:
   ```python
   return request.accept_languages.best_match(["en", "es", "fr"]) or "en"
   ```

### Updating Existing Translations

After adding new translatable strings to the codebase:

```bash
# Convenience script (extract + update + compile)
bash scripts/update_translations.sh
```

Or manually:

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
pybabel compile -d translations
```

### Adding Frontend Translations

When you add a new translatable string to JavaScript:

1. Add the string to the `js_translations` dict in `app.py:inject_i18n_globals()`.
2. Use `__("your_key")` in JavaScript files.
3. Add the corresponding `msgid` to each `.po` file with the translated `msgstr`.
4. Regenerate the `.mo` files with `pybabel compile -d translations`.

## Contributing

Contributions are welcome! Here's how to get started:

### Reporting Issues

If you find a bug or have a feature request, open an issue on the project repository with:
- A clear description of the problem or suggestion
- Steps to reproduce (for bugs)
- Expected vs actual behavior

### Development Setup

1. Fork and clone the repository.
2. Set up the virtual environment as described in [Installation](#installation).
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the test suite to confirm everything works:
   ```bash
   python -m pytest
   npm test
   ```

### Code Conventions

- **Architecture:** Follow the strict 4-layer Clean Architecture — never import Flask/SQLAlchemy in `domain/`.
- **Monetary values:** Always use `decimal.Decimal` with `ROUND_HALF_UP`. Never use `float` for financial amounts.
- **Type hints:** Every function must have complete type annotations.
- **Testing:** All changes should maintain or improve the 90% coverage threshold. Run `python run_coverage.py` to verify.
- **Translations:** Wrap all user-facing strings in `_()` (Python/Jinja2) or `__()` (JavaScript) for i18n support.

### Pull Request Process

1. Create a feature branch from `main`.
2. Write tests first (TDD — Red/Green/Refactor).
3. Implement your changes.
4. Ensure all tests pass: `python -m pytest && npm test`.
5. Verify coverage: `python run_coverage.py`.
6. Submit a pull request with a clear description of the changes.

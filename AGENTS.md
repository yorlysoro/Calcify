# Calcify

Flask 3 + SQLAlchemy 2.0 Clean Architecture desktop app (currency/inventory management).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python setup_security.py
python app.py              # binds 0.0.0.0:5000
```

Password reset: `python reset_password.py`

Frontend build: `npm run build:css` (Tailwind CSS local).
Frontend tests: `npm test` (Jest + jsdom, 97 tests).

Platform launchers: `iniciar_debian.sh` (Linux), `instalar_y_correr.bat` (Windows).

## Tests

```bash
python -m pytest
```

No `pyproject.toml` — deps in `requirements.txt` only.

- In-memory SQLite via `StaticPool`, never touches disk.
- `db_session` fixture uses SAVEPOINTs (nested transactions) for isolation across `commit()`.
- `client` fixture calls `create_app(config_name="testing")`.
- Integration tests use `seed_admin_password` fixture + `with client.session_transaction() as s: s["authenticated"] = True`.

## Architecture layers

| Layer | Depends on | Banned imports |
|-------|-----------|----------------|
| `domain/` | Python stdlib | Flask, SQLAlchemy, any framework |
| `use_cases/` | Domain entities, abstract repo interfaces | ORM models, Flask |
| `infrastructure/` | SQLAlchemy, domain entities, interfaces | Flask globals (request, g, session) |
| `presentation/` | Flask, domain entities, repo implementations | ORM models directly |

Enforced rules (also in `.agents/rules/`):
- `float` banned for monetary/percentage values — use `decimal.Decimal` with `ROUND_HALF_UP`.
- Every function must have complete type hints.
- Repositories return pure domain entities (`domain/models.py`), never ORM models.
- Domain entities use `@dataclass(slots=True)`.
- Timezone-aware datetimes required in domain layer; defective SQLite naive datetime handled defensively in repo mapping (`infrastructure/repositories/sqlalchemy_repos.py:193`).

## Key files

- `app.py`: `create_app()` factory — engine, session, migrations, security, `@app.before_request` injects `g.db_session`.
- `presentation/api/routes.py`: Blueprint `api_bp` at `/api/v1/`, `@login_required` from `presentation/api/auth.py`.
- `presentation/api/auth.py`: Blueprint `auth_bp`, session-based auth (POST `/login` with `{"pin": "..."}`, POST `/logout`).
- `infrastructure/database/migrations.py`: Programmatic Alembic (`run_migrations()`). No CLI needed. Expects `alembic.ini` + `migrations/` at project root (currently absent — only scaffold-level).
- `infrastructure/database/models.py`: ORM models (`CurrencyModel`, `ProductModel`, `TransactionModel`, `ConfigModel`).
- `infrastructure/repositories/interfaces.py`: Abstract repository interfaces.
- `infrastructure/repositories/sqlalchemy_repos.py`: Implementations with domain mapping. Each repo takes a `Session` in `__init__`.
- `domain/services.py`: `CurrencyConverter` service, `InvalidExchangeRateError`.
- `use_cases/export_backup.py`: Injects abstract repos via DI, returns serialized dict.
- `scaffold.py`: Generates the directory structure if missing.
- `static/js/utils.js`: `formatMoney`, `truncate`, `escapeHtml`, `formatDate`, `getBaseCurrency`, `getInverseRate`.
- `static/js/api-client.js`: `ApiClient` (GET/POST/PUT/DELETE) with 401 redirect and error handling.
- `static/js/app.js`: `App.init()` — bootstrap via `Promise.all` across currencies/products/rates/transactions.
- `static/js/calculator.js`: `CalculatorView` — multi-currency conversion calculator.
- `static/js/inventory.js`: `InventoryView` — CRUD products with modals, stock badges, category filter.
- `static/js/config.js`: `ConfigView` — currency/rate management, set base currency, JSON backup export.
- `static/js/reports.js`: `ReportView` — date-filtered transaction table with converted values, CSV export.
- `static/js/sales.js`: `SalesView` — sale registration form with product search and stock validation.
- `static/css/base.css`: Cyberpunk theme variables, background animation, layout, scrollbar.
- `presentation/templates/base.html`: Template base with blocks `title`, `body_class`, `content`, `scripts`, `extra_css`.

## Repo conventions

- All `__init__.py` files exist across packages.
- `g.db_session` injected per-request; always use `g.db_session.commit()` in route handlers (manual Unit of Work).
- `Decimal` values serialized to strings in all JSON responses (JS float corruption prevention).
- Route handlers instantiate repos directly from `g.db_session`: `SqlAlchemyProductRepository(session=g.db_session)`.
- Changelog: `changelog.md`.
- JS modules are plain scripts (no `import`/`export`) — they expose global vars (`var`) referenced via `onclick` in HTML.
- CSS is split by view in `static/css/` (7 files), loaded from `base.html` via `{% block extra_css %}`.
- Tailwind CSS built locally via `npm run build:css` (`static/dist/tailwind.css`).
- Frontend tests load scripts via `(0, eval)(code)` (indirect eval) to inject global scope in Jest.

## Design & Architecture Patterns

| # | Pattern | Category | Key File(s) |
|---|---------|----------|-------------|
| 1 | Clean Architecture (4-layer strict) | Architectural | All packages — domain/ → use_cases/ → infrastructure/ → presentation/ |
| 2 | Dependency Inversion (DIP) | Architectural | `interfaces.py`, `sqlalchemy_repos.py`, `export_backup.py` |
| 3 | Application Factory | Creational | `app.py` — `create_app(config_name=None)` |
| 4 | Repository | Structural | `interfaces.py` (abstract), `sqlalchemy_repos.py` (concrete) |
| 5 | Dependency Injection | Structural | `app.py` (g.db_session), repos (Session ctor), use cases (repo ctor) |
| 6 | Unit of Work | Behavioral | `app.py` (before_request/teardown), repos never commit, routes call `g.db_session.commit()` |
| 7 | Decorator (Auth Middleware) | Structural | `presentation/api/auth.py` — `@login_required` |
| 8 | Adapter (ORM → Domain) | Structural | `sqlalchemy_repos.py` — `_map_to_domain()` |
| 9 | Strategy (Migration) | Behavioral | `auto_migrate.py` (bootstrap) vs `migrations.py` (CLI) |
| 10 | Use Case / Interactor | Behavioral | `use_cases/export_backup.py` — single-purpose `execute()` |
| 11 | Domain Service (Stateless) | Behavioral | `domain/services.py` — `CurrencyConverter.convert()` |
| 12 | SAVEPOINT Test Isolation | Testing | `tests/conftest.py` — nested txns for zero pollution |
| 13 | Session-scoped Fixture (Singleton) | Testing | `tests/conftest.py` — `db_engine` with `scope="session"` |
| 14 | AAA (Arrange-Act-Assert) | TDD | All test files — `# Arrange` / `# Act` / `# Assert` |
| 15 | Red-Green-Refactor | TDD | Test comments + `.agents/rules/backend-python-dev.md` |
| 16 | Upsert (Merge) | Infrastructure | `sqlalchemy_repos.py` — `session.merge()` for currencies/rates/config |
| 17 | Lookup-Then-Update | Infrastructure | `sqlalchemy_repos.py` — explicit query+update for products/transactions |
| 18 | Subquery Aggregation | Infrastructure | `sqlalchemy_repos.py:221-247` — `func.max` per currency_code |
| 19 | Programmatic Alembic | Infrastructure | `auto_migrate.py` — `alembic.command` bypasses CLI |
| 20 | OS-Aware DB Path | Infrastructure | `session.py` — `get_db_path()` for Win/Mac/Linux |
| 21 | Idempotent Bootstrap | Operational | `setup_security.py` — skip if secret/pw exists |
| 22 | Password Hashing (Werkzeug) | Security | `auth.py` / `setup_security.py` — `generate_password_hash` / `check_password_hash` |
| 23 | Session Fixation Prevention | Security | `auth.py:104` — `session.clear()` before login |
| 24 | Anti-Corruption Layer | Clean Code | `domain/models.py` — `__post_init__` validates types |
| 25 | SPA Bootstrap (Promise.all) | Architectural | `static/js/app.js` — parallel fetch of currencies/products/rates/transactions |
| 26 | Module-as-View (Global Var) | Structural | Each `static/js/*.js` exposes a constructor/view object via `var` |
| 27 | Indirect Eval Test Injection | Testing | `tests/frontend/*.test.js` — `(0, eval)(code)` for global scope injection |
| 28 | CSS-per-View | Structural | 7 files in `static/css/`, loaded selectively via `{% block extra_css %}` |
| 29 | Defensive JS (Error States) | Behavioral | All views handle empty state, 401, network failure, NaN, null elements |

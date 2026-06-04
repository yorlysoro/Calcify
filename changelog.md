# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-06-03

### Added

- **Domain:** `stock_quantity: int = 0` field in `Product` entity for inventory tracking (`domain/models.py`).
- **Infrastructure:** `stock_quantity` column in `ProductModel` ORM with `server_default="0"` (`infrastructure/database/models.py`).
- **Infrastructure:** Automatic Alembic migration bootstrap (`infrastructure/database/auto_migrate.py`) — creates `alembic.ini` and `migrations/` on demand, patches `env.py` with `target_metadata`, `render_as_batch=True`, `compare_type=True`, `compare_server_default=True`, and auto-generates/applies schema migrations on every `app.py` startup. Falls back to raw `ALTER TABLE` DDL when Alembic's autogenerate fails to detect SQLite column changes.
- **Infrastructure:** Defensive mapping for legacy rows in `SqlAlchemyProductRepository.get_all` — `stock_quantity` falls back to `0` and `category` to `"Uncategorized"` when the database returns `None` (`infrastructure/repositories/sqlalchemy_repos.py`).
- **API:** `PUT /api/v1/products/<product_id>` endpoint for partial product updates (name, category, cost_price, cost_currency_code, margin_percentage, stock_quantity) with field-level validation and rollback on failure (`presentation/api/routes.py`).
- **API:** `stock_quantity` serialization in `GET /api/v1/products` and `GET /api/v1/products/<id>` responses (`presentation/api/routes.py`).
- **API:** Server-side date filtering via `?date=YYYY-MM-DD` query parameter on `GET /api/v1/transactions` (`presentation/api/routes.py`).
- **API:** Full exception debugging in `GET /api/v1/products` — stack trace printed to Flask terminal via `traceback.print_exc()` and error details (`error`, `type`, `trace`) exposed in the JSON 500 response for browser Network tab inspection.
- **Frontend:** Stock Quantity input field in Add/Edit Product modal and Stock column in inventory table (`presentation/templates/index.html`).
- **Frontend:** Reports tab (📊) with daily transaction ledger, multi-currency conversion display, date filter input, and CSV export (`presentation/templates/index.html`).
- **Testing:** `test_auto_migrate.py` — 4 integration tests covering Alembic schema sync: initial table creation, column addition, column removal, and column type replacement with SQLite batch mode (`tests/infrastructure/test_auto_migrate.py`).
- **Testing:** `test_update_product_success` — integration test for `PUT /api/v1/products/<id>` verifying field updates persist and return correctly (`tests/presentation/test_routes.py`).
- **Testing:** `test_get_transactions_with_date_filter` — integration test for `?date=` query parameter on transaction listing (`tests/presentation/test_routes.py`).

### Changed

- **Core:** Application boot now calls `bootstrap_migrations(str(engine.url), Base.metadata)` instead of manually checking `alembic.ini` existence or falling back to `Base.metadata.create_all`. Migrations are fully automatic on every startup (`app.py`).

### Fixed

- **Migrations:** Removed `KeyError: 'formatters'` crash by delegating alembic.ini creation to Alembic's native `command.init()` instead of a manually written stripped-down INI string.
- **Migrations:** Alembic revisions are no longer auto-generated on boot (was causing hangs); the boot flow uses `command.upgrade("head")` only, and column detection falls back to raw DDL via SQLAlchemy `inspect()`.
- **Repositories:** `SqlAlchemyProductRepository.get_all` now safely handles `None` values from legacy rows for `stock_quantity` and `category` columns.

## [0.6.0] - 2026-06-02

### Added

- **Domain:** `CurrencyRate` pure domain entity with UUID, currency_code, Decimal rate, and timezone-aware datetime (`domain/models.py`).
- **Infrastructure:** `CurrencyRateModel` ORM model with `currency_rates` table using `Numeric(14, 6)` precision (`infrastructure/database/models.py`).
- **Infrastructure:** `ICurrencyRateRepository` interface and `SqlAlchemyCurrencyRateRepository` implementation with `save`, `get_latest_by_code`, `get_all_latest` (grouped-max subquery), and `delete` methods (`infrastructure/repositories/interfaces.py`, `infrastructure/repositories/sqlalchemy_repos.py`).
- **API:** `POST /api/v1/rates` endpoint for creating exchange rate records (`presentation/api/routes.py`).
- **API:** `GET /api/v1/rates/latest` endpoint returning the most recent rate per currency code (`presentation/api/routes.py`).
- **API:** `DELETE /api/v1/rates/<id>` endpoint for removing rate records (`presentation/api/routes.py`).
- **API:** `POST /api/v1/currencies` endpoint for creating new currencies with duplicate detection (`presentation/api/routes.py`).
- **Frontend:** Currency Management panel (💱) in Config view with CRUD form and live grid (`presentation/templates/index.html`).
- **Frontend:** Exchange Rates panel (📈) in Config view with rate creation form, live list, and delete support (`presentation/templates/index.html`).
- **Frontend:** Calculator live conversion now uses backend rates from `GET /api/v1/rates/latest` instead of hardcoded fallbacks (`presentation/templates/index.html`).
- **Frontend:** `web_bp` Blueprint with `GET /` (index) and `GET /login` routes serving `index.html` and `login.html` templates (`presentation/web/routes.py`).
- **Testing:** `test_create_currency_success` and `test_create_currency_duplicate` integration tests for currency creation (`tests/presentation/test_routes.py`).
- **Testing:** `test_create_currency_rate` and `test_get_latest_currency_rates` integration tests for rate management (`tests/presentation/test_routes.py`).

### Fixed

- **Setup:** `Base.metadata.create_all(bind=engine)` called before session usage to prevent "table not found" errors on fresh installs (`setup_security.py`).
- **Migrations:** Graceful fallback to `Base.metadata.create_all()` when `alembic.ini` is absent, preventing crash on fresh installations (`app.py`).
- **Routing:** Added `GET /login` route to resolve HTTP 405 errors when unauthenticated users are redirected to the login page (`presentation/web/routes.py`).
- **Routing:** Flask constructor now explicitly sets `template_folder="presentation/templates"` (`app.py`).
- **Repository:** Added `save` and `get_by_code` methods to `ICurrencyRepository` interface and `SqlAlchemyCurrencyRepository` implementation (`infrastructure/repositories/interfaces.py`, `infrastructure/repositories/sqlalchemy_repos.py`).

## [0.5.0] - 2026-05-31

### Added

- **Domain:** `category` field in `Product` entity with `"Uncategorized"` default, including backward-compatible migrations and API mapping (`domain/models.py`, `infrastructure/database/models.py`, `presentation/api/routes.py`).
- **Use Cases:** `ExportBackupUseCase` orchestrating full system backup with strict Decimal/UUID/DateTime serialization to JSON-safe primitives (`use_cases/export_backup.py`).
- **API:** `GET /api/v1/products` inventory listing endpoint returning serialized product list (`presentation/api/routes.py`).
- **API:** `DELETE /api/v1/products/<id>` hard delete lifecycle for products with repo interface contract (`presentation/api/routes.py`, `infrastructure/repositories/interfaces.py`).
- **API:** Transaction ledger CRUD endpoints (`POST /api/v1/transactions`, `GET /api/v1/transactions`) with strict JSON financial serialization, foreign key integrity checks, and timezone-aware timestamps (`presentation/api/routes.py`).
- **API:** Protected `GET /api/v1/backup/export` endpoint forcing file download with `Content-Disposition` headers (`presentation/api/routes.py`).
- **Frontend:** Responsive single-page application layout with modular mock views and real-time offline JS currency conversion logic (`presentation/templates/index.html`).
- **Frontend:** `ApiClient` interceptor refactoring SPA views to consume real backend API data for calculator matrix, inventory CRUD, and JSON export (`presentation/templates/index.html`).
- **Frontend:** Dual responsive UI for inventory management, live pricing modal, and async daily closing reports (`presentation/templates/index.html`).
- **Ops:** `iniciar_debian.sh` Linux launcher with Python/venv verification, dependency installation, LAN IP resolution, and styled banner.
- **Ops:** `instalar_y_correr.bat` Windows launcher with Python auto-installer, admin elevation, and automatic browser launch.
- **Docs:** `AGENTS.md` with architecture layer rules, testing conventions, repo patterns, and key file references.

### Fixed

- **API:** Resolved `NameError` on `uuid4` in transaction route handlers by adding missing import (`presentation/api/routes.py`).

## [0.4.0] - 2026-05-24

### Added

- **Presentation:** `presentation/api/routes.py` implementing a Flask Blueprint (`api_bp`) for strict JSON CRUD operations routing to domain repositories.
- **Security:** `presentation/api/auth.py` implementing session management (`auth_bp`) and the `@login_required` interceptor decorator to protect API endpoints.
- **Security:** `setup_security.py` idempotent CLI script for bootstrapping the `app_secret_key` via CSPRNG (`secrets` module) and the master admin PIN hash.
- **Security:** `reset_password.py` interactive CLI utility for safe, confirmed master password overrides.
- **Frontend:** `presentation/templates/login.html` featuring a responsive, Cyberpunk-themed dark mode UI (Tailwind CSS) that intercepts native form submissions to communicate with the JSON API.
- **Testing:** `client` fixture in `conftest.py` that spawns a full Flask testing application context bound to an isolated in-memory SQLite database.
- **Testing:** Comprehensive TDD integration suite (`test_routes.py`) verifying security middleware rejections (HTTP 401), session state manipulation, and protected CRUD payload delivery.

### Changed

- **Core Architecture:** Major refactor of `app.py`. Implemented the Application Factory pattern (`create_app`) to eliminate circular dependencies.
- **Database Connection Lifecycle:** Introduced Flask global context `g.db_session` injected via `@app.before_request` and destroyed safely via `@app.teardown_request`, isolating infrastructure concerns from the routing controllers.

## [0.3.0] - 2026-05-21

### Added

- **Domain:** `Transaction` pure Python entity with strict timezone-aware validation and memory-efficient `slots=True` to prevent dictionary overhead.
- **Infrastructure:** `TransactionModel` and `ConfigModel` ORM representations (`infrastructure/database/models.py`) utilizing strict SQLAlchemy 2.0 type hinting (`Mapped[T]`).
- **Infrastructure:** Programmatic Alembic migration runner (`infrastructure/database/migrations.py`) that bypasses CLI requirements for standalone desktop deployments.
- **Infrastructure:** Dynamic OS-agnostic database path resolution resolving to user-specific data directories (e.g., `%APPDATA%`, `~/.config`) avoiding read-only program file crashes.
- **Repositories:** `SqlAlchemyTransactionRepository` and `SqlAlchemyConfigRepository` adapters enforcing strict Domain mapping boundaries and Upsert logic.
- **Testing:** `conftest.py` setup featuring an in-memory SQLite `StaticPool` and nested transaction `SAVEPOINTS` for lightning-fast, zero-I/O test isolation.
- **Testing:** Comprehensive TDD suites for all repositories verifying domain encapsulation, upsert mechanics, and foreign key integrity.

### Fixed

- **Testing:** Resolved TDD "Red Phase" `ImportError` by fully implementing the `Transaction` entity boundary.
- **Infrastructure:** Mitigated SQLite's naive datetime driver bug by defensively injecting `timezone.utc` during ORM-to-Domain mapping, preventing catastrophic time-shift bugs in financial ledgers.

### Added

- `schema.md` to document the Domain-Driven Design (DDD) entities and strictly typed models.

## [0.2.0] - 2026-05-07

### Added

- `domain/models.py`: Introduced pure Python domain entities (`Currency`, `ExchangeRate`, `Product`) utilizing memory-efficient `dataclass(slots=True)`.
- `domain/services.py`: Implemented stateless `CurrencyConverter` domain service handling strict financial math.
- `domain/exceptions.py`: Added custom `InvalidExchangeRateError` to prevent mathematical fallacies at the domain level.
- `tests/test_currency_converter.py`: Comprehensive Pytest suite enforcing Test-Driven Development (TDD) for currency exchange logic.
- `tests/test_product.py`: Pytest suite for `Product` entity margin calculation and service injection.

### Changed

- Enforced system-wide constraint: Financial math now strictly utilizes Python's `decimal.Decimal` with `ROUND_HALF_UP` quantization. `float` types are banned.

### Fixed

- Fixed `pytest` regex failure in `test_product_rejects_invalid_base_currency` by using raw strings (`r""`) and wildcards (`.*`) to properly capture dynamically injected f-string variables.

## [0.1.0] - 2026-04-28

### Added

- Define foundational architecture standards and rules (Clean Architecture, TDD, Strict Typing).
- `scaffold.py` script to generate the core directory structure.
- Initial directory tree layout: `domain/`, `use_cases/`, `infrastructure/repositories/`, `infrastructure/database/`, `presentation/api/`, and `tests/`.
- `__init__.py` files across all directories to establish Python packages.
- Local Area Network (LAN) reachable Flask prototype (`app.py` binding to `0.0.0.0`).
- Isolated Desktop GUI PoC using `pywebview` running Flask on a background daemon thread.

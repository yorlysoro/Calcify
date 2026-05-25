# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

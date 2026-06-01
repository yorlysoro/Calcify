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

## Repo conventions

- All `__init__.py` files exist across packages.
- `g.db_session` injected per-request; always use `g.db_session.commit()` in route handlers (manual Unit of Work).
- `Decimal` values serialized to strings in all JSON responses (JS float corruption prevention).
- Route handlers instantiate repos directly from `g.db_session`: `SqlAlchemyProductRepository(session=g.db_session)`.
- Changelog: `changelog.md`.

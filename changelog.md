# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

---
trigger: always_on
---

# Project Architecture Scaffolding

This document contains the foundational directory structure for our Flask/SQLAlchemy Clean Architecture application.

## Directory Structure

- `domain/`: Pure Python enterprise logic. No external dependencies.
- `use_cases/`: Application business rules.
- `infrastructure/repositories/`: Database implementation of domain interfaces.
- `infrastructure/database/`: ORM models and migrations.
- `presentation/api/`: Flask controllers and routes.
- `tests/`: Pytest suites.

---
trigger: always_on
---

# Domain Models Schema

This document outlines the pure Python entities residing in the `domain/` layer.
Our domain is strictly isolated from infrastructure (no SQLAlchemy or Flask dependencies).

## Architectural Constraints

- **Memory Optimization:** All models utilize `@dataclass(slots=True)` to prevent `__dict__` creation, lowering RAM footprint and speeding up attribute access.
- **Financial Precision:** The `float` primitive is strictly forbidden. All monetary and percentage values must utilize the standard `decimal.Decimal` module.

---

### 1. Currency

Represents a standard currency entity.

| Attribute | Type   | Description                                            |
| :-------- | :----- | :----------------------------------------------------- |
| `code`    | `str`  | ISO 4217 standard currency code (e.g., 'USD', 'VES').  |
| `name`    | `str`  | Full descriptive name (e.g., 'US Dollar').             |
| `symbol`  | `str`  | Graphical symbol (e.g., '$').                          |
| `is_main` | `bool` | Flag designating the reference currency of the system. |

---

### 2. ExchangeRate

Represents the exact mathematical relationship between two currencies at a specific point in time.

| Attribute              | Type       | Description                                        |
| :--------------------- | :--------- | :------------------------------------------------- |
| `base_currency_code`   | `str`      | The source ISO 4217 code.                          |
| `target_currency_code` | `str`      | The target ISO 4217 code.                          |
| `rate`                 | `Decimal`  | Exact conversion multiplier. Must NOT be 0.00.     |
| `date`                 | `datetime` | The temporal snapshot of when this rate was valid. |

---

### 3. Product

Represents a sellable item, containing dynamic pricing logic.

| Attribute            | Type      | Description                                                     |
| :------------------- | :-------- | :-------------------------------------------------------------- |
| `id`                 | `UUID`    | Universally Unique Identifier for database and domain tracking. |
| `name`               | `str`     | Commercial name of the item.                                    |
| `cost_price`         | `Decimal` | The base acquisition/manufacturing cost.                        |
| `cost_currency_code` | `str`     | ISO 4217 code matching a `Currency` entity.                     |
| `margin_percentage`  | `Decimal` | The expected profit margin percentage (e.g., 30.00).            |

#### Core Domain Behaviors (Methods)

- `calculate_sale_price() -> Decimal`: Applies the `margin_percentage` to the `cost_price` using strict `ROUND_HALF_UP` banking rules.
- `get_sale_price_in_currency(...) -> Decimal`: Injects the `CurrencyConverter` domain service to dynamically calculate the sale price in a target foreign currency.

<!-- # <ERD> stands for Entity-Relationship Diagram. Future infrastructure mappings will be documented in the infrastructure layer, not here. -->

# Smart Expense Tracker API

A REST API for managing personal expenses: add, list, filter by category,
calculate totals (overall and by category), and delete.

Built with **FastAPI** and **in-memory storage** (no database required).

## Features

- `POST /expenses` — add an expense (`title`, `amount`, `category`, `date`)
- `GET /expenses` — list all expenses
- `GET /expenses?category=Food` — filter expenses by category (case-insensitive)
- `GET /expenses/total` — overall total and total broken down by category
- `DELETE /expenses/{id}` — delete an expense by id

**Bonus implemented:** interactive OpenAPI/Swagger docs at `/docs` (and
machine-readable schema at `/openapi.json`), generated automatically by
FastAPI from the route and model definitions.

## Requirements

- Python 3.12+

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the server

```bash
uvicorn src.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`.

## Run the tests

```bash
pytest -v
```

## Example usage

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title":"Coffee","amount":"4.50","category":"Food","date":"2026-07-01"}'

curl http://127.0.0.1:8000/expenses

curl "http://127.0.0.1:8000/expenses?category=Food"

curl http://127.0.0.1:8000/expenses/total

curl -X DELETE http://127.0.0.1:8000/expenses/1
```

## Project structure

```
src/
  main.py       # FastAPI app and route handlers
  models.py     # Pydantic request/response schemas and validation
  storage.py    # In-memory expense store
tests/
  test_expenses.py   # pytest suite: CRUD, filtering, totals, edge cases
```

## Architecture

This follows a standard router / schema / repository split:

- **`main.py` (router)** — HTTP layer only: parses requests, calls the store,
  shapes responses. No business logic lives here.
- **`models.py` (schema)** — Pydantic request/response contracts and field
  validation (blank checks, decimal precision, positivity).
- **`storage.py` (repository)** — the only place that knows *how* expenses
  are stored (in-memory dict + lock). Swapping this for a database later
  would mean changing this one file, not the routes.

There's deliberately **no separate service layer**. The "business logic" here
is a filter and a sum — introducing a `services/` layer to wrap two
one-line operations would be structure for its own sake, not for the
codebase's actual complexity. Standard FastAPI production guidance agrees
services/repositories should be introduced when a project's logic actually
needs them, not pre-emptively for an app this size.

## Design notes

- Storage is a plain in-memory dict, reset on every server restart — matches
  the assignment's "in-memory or local JSON file; no database required."
- `amount` must be greater than 0, have at most 2 decimal places, and up to
  12 total digits; `title`/`category` must be non-blank after trimming
  whitespace. All enforced by Pydantic and return `422` on violation.
- Deleting a non-existent id, or one that isn't an integer, returns `404`/`422`
  respectively.
- Category filtering is case-insensitive (`Food` and `food` match the same
  expenses) since categories are free-text user input, not a fixed enum.

## Production-hardening notes

These were added after a self-review to remove failure modes that a
"works on my machine" version wouldn't surface:

- **Monetary precision:** `amount` and totals use Python's `Decimal`, not
  `float`. Summing floats accumulates binary rounding error (e.g.
  `10.10 + 20.20` as floats yields `30.299999999999997`); `Decimal` sums
  exactly. As a result, `amount` and totals are serialized as **decimal
  strings** in JSON responses (e.g. `"30.30"`, not `30.3`) — this is
  intentional, so precision isn't lost again when a client parses the
  response as a float. See `tests/test_expenses.py::test_totals_do_not_accumulate_floating_point_error`.
- **Thread-safety:** `ExpenseStore` guards all reads/writes to its internal
  dict with a `threading.Lock`. FastAPI runs synchronous route handlers in a
  thread pool, so without a lock, concurrent `POST /expenses` requests could
  read the same `next_id` before either wrote it back, silently overwriting
  one expense with another under the same id. Covered by a concurrency stress
  test (`test_concurrent_adds_never_collide_on_id`) that fires 50 adds across
  20 threads and asserts every id is unique.
- **No unhandled exceptions reach the client:** a global exception handler in
  `main.py` catches anything not already handled by FastAPI's built-in 404/422
  paths, logs it server-side with `logging.exception`, and returns a generic
  `500 {"detail": "Internal server error"}` — so a bug never leaks a stack
  trace or internal state to the caller.
- **Blank-but-not-empty input is rejected:** `title`/`category` of `"   "`
  used to pass the old `min_length=1` check (a space has length 1). They're
  now stripped and re-validated as non-blank.

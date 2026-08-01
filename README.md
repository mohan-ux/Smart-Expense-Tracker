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
  -d '{"title":"Coffee","amount":4.5,"category":"Food","date":"2026-07-01"}'

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

## Design notes

- Storage is a plain in-memory dict, reset on every server restart — matches
  the assignment's "in-memory or local JSON file; no database required."
- `amount` must be greater than 0 and `title`/`category` must be non-empty;
  these are enforced by Pydantic and return `422` on violation.
- Deleting a non-existent id returns `404`.
- Category filtering is case-insensitive (`Food` and `food` match the same
  expenses) since categories are free-text user input, not a fixed enum.

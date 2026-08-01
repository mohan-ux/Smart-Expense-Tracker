# AI Notes

## 1. What was AI-generated vs. written by me

I used Claude Code (Anthropic) as a pair-programming tool for essentially the
entire implementation: `src/models.py`, `src/storage.py`, `src/main.py`,
`tests/test_expenses.py`, and the first draft of this README. I didn't
hand-type the boilerplate myself — I directed the design (stack, storage
choice, scope) and then reviewed, ran, and edited what the AI produced rather
than accepting it blindly. The decisions below are mine; the code that
implements them was largely AI-drafted and then verified by me.

## 2. What I validated, tested, or changed, and why

- **Ran the full test suite in a genuinely clean environment.** Before
  writing the README, I created a fresh `.venv`, ran `pip install -r
  requirements.txt` from scratch, then `pytest -v` — all 12 tests passed. I
  did this specifically because the assignment says submissions are
  auto-reviewed by running the README's commands verbatim, so "works on my
  machine" wasn't good enough.
- **Manually smoke-tested every endpoint**, not just the pytest suite: started
  `uvicorn` and used `curl` to POST an expense, GET the list, GET `/expenses/total`,
  and confirmed `/docs` and `/openapi.json` both return `200` (this is what the
  Swagger bonus actually depends on — a route existing isn't enough if FastAPI's
  schema generation silently fails on a bad type hint).
- **Rejected the AI's first draft of category filtering being case-sensitive.**
  The initial `list_all` implementation did an exact string match on
  `category`. I changed it to a case-insensitive comparison
  (`e.category.lower() == category.lower()`) because categories are free-text
  user input, not a fixed enum — an exact-match filter would silently return
  empty results for `"food"` vs `"Food"`, which is a real bug a user would hit
  immediately, not just an edge case.
- **Verified the validation rules actually reject bad input**, not just accept
  good input: added explicit tests for `amount <= 0` and empty `title`
  returning `422`, and deleting a non-existent id returning `404`, because
  Pydantic's `Field(gt=0, min_length=1)` constraints are easy to get wrong
  (e.g. `ge=0` instead of `gt=0`) and I wanted a failing test to catch that,
  not just eyeball the code.

## 2b. A follow-up hardening pass (after a self-review)

After the first working version, I asked Claude Code to review its own
output specifically for structure, functionality, exception handling, and
security, then acted on what came back rather than accepting the review
uncritically:

- **Confirmed and fixed a real concurrency bug**: `ExpenseStore._next_id += 1`
  was not atomic, and FastAPI runs sync route handlers in a thread pool, so
  concurrent `POST /expenses` calls could race and silently overwrite one
  expense with another under a duplicate id. I added a `threading.Lock`
  around all store mutations/reads, and — importantly — didn't just trust
  that the fix worked. I added `test_concurrent_adds_never_collide_on_id`,
  which fires 50 adds across 20 threads and asserts every returned id is
  unique, so the fix is verified by a failing-then-passing test, not just
  code inspection.
- **Accepted the `float` → `Decimal` suggestion** for `amount` and totals,
  since summing floats can accumulate binary rounding error. I verified this
  concretely: I wrote a test with `"10.10"` and `"20.20"` (a pair known to
  misbehave under float addition) and confirmed the API now returns exactly
  `"30.30"`.
- **Noticed and accepted a side effect I hadn't asked for**: switching to
  `Decimal` changed the wire format — `amount`/totals now serialize as JSON
  strings (`"4.50"`) instead of numbers (`4.5`), because Pydantic v2
  serializes `Decimal` as a string by default to avoid reintroducing float
  imprecision on the client side. I re-ran the full suite, saw exactly which
  assertions broke because of this, and updated them deliberately rather than
  loosening them to make failures go away — the string format is the correct
  production choice for money, not a bug to paper over.
- **Added a global exception handler** (`main.py`) that logs unhandled
  errors server-side and returns a generic `500` to the client, so a future
  bug can't leak a stack trace. I verified it doesn't shadow FastAPI's
  existing 404/422 handling by re-running the delete-404 and validation-422
  tests afterward — they still pass, confirming Starlette dispatches to the
  more specific handler first.
- **Tightened blank-input validation**: `title`/`category` of `"   "` used to
  pass the old `min_length=1` check. Added a validator that strips whitespace
  and rejects blank results, with tests for both the rejection and the
  stripping behavior (e.g. `"  Coffee  "` → `"Coffee"`).

## 3. AI suggestions I decided not to use, and why

- **A database (SQLite/Postgres) was not something I asked for or added**,
  even though it's a common instinct to "show more" in a take-home. The
  assignment explicitly states no database is required, and I researched
  general take-home assignment guidance beforehand: adding unrequested
  infrastructure burns time a reviewer won't credit and risks introducing bugs
  in an area that isn't being evaluated. I kept storage as a plain in-memory
  dict.
- **JSON-file persistence** (so data survives a server restart) was suggested
  as a middle ground between pure in-memory and a full database. I decided
  against it — it adds file I/O error handling and test surface area for a
  property (persistence across restarts) the spec doesn't ask for.
- **A `GET /expenses/{id}` single-item endpoint** was proposed as a natural
  companion to `DELETE /expenses/{id}`. I left it out to keep the API surface
  matching exactly what the assignment lists (add, view all, filter, totals,
  delete) rather than expanding scope on a 4-hour-budget assignment.
- **More than one bonus feature** (e.g. combining Swagger docs with a search
  endpoint) was possible since FastAPI makes both easy. The assignment caps
  bonus work at one feature, so I implemented only Swagger/OpenAPI docs, which
  FastAPI generates automatically from the existing route and Pydantic
  definitions at no extra implementation cost.
- **A `/health` endpoint and structured request logging middleware** were
  considered during the hardening pass, since they're common in real
  production services. I left them out — they're operational scaffolding for
  a deployed service, not a fix for a failure mode in the existing 5
  endpoints, and adding them would be scope creep beyond "make it not break,"
  which was the actual ask.

from fastapi import FastAPI, HTTPException, status

from src.models import CategoryTotal, Expense, ExpenseCreate, TotalsResponse
from src.storage import ExpenseStore

app = FastAPI(
    title="Smart Expense Tracker API",
    description="A REST API to add, list, filter, total, and delete personal expenses.",
    version="1.0.0",
)

store = ExpenseStore()


@app.post("/expenses", response_model=Expense, status_code=status.HTTP_201_CREATED, tags=["expenses"])
def add_expense(expense: ExpenseCreate) -> Expense:
    return store.add(expense)


@app.get("/expenses", response_model=list[Expense], tags=["expenses"])
def list_expenses(category: str | None = None) -> list[Expense]:
    return store.list_all(category)


@app.get("/expenses/total", response_model=TotalsResponse, tags=["expenses"])
def total_expenses() -> TotalsResponse:
    overall, by_category = store.totals()
    return TotalsResponse(
        overall_total=overall,
        by_category=[CategoryTotal(category=c, total=t) for c, t in by_category.items()],
    )


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenses"])
def delete_expense(expense_id: int) -> None:
    if not store.delete(expense_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

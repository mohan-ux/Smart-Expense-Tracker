from src.models import Expense, ExpenseCreate


class ExpenseStore:
    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1

    def add(self, data: ExpenseCreate) -> Expense:
        expense = Expense(id=self._next_id, **data.model_dump())
        self._expenses[expense.id] = expense
        self._next_id += 1
        return expense

    def list_all(self, category: str | None = None) -> list[Expense]:
        expenses = list(self._expenses.values())
        if category is not None:
            expenses = [e for e in expenses if e.category.lower() == category.lower()]
        return expenses

    def delete(self, expense_id: int) -> bool:
        return self._expenses.pop(expense_id, None) is not None

    def totals(self, category: str | None = None) -> tuple[float, dict[str, float]]:
        expenses = self.list_all(category)
        overall = sum(e.amount for e in expenses)
        by_category: dict[str, float] = {}
        for e in expenses:
            by_category[e.category] = by_category.get(e.category, 0) + e.amount
        return overall, by_category

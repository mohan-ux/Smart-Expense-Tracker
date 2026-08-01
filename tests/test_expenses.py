import pytest
from fastapi.testclient import TestClient

from src.main import app, store


@pytest.fixture(autouse=True)
def reset_store():
    store._expenses.clear()
    store._next_id = 1
    yield


@pytest.fixture
def client():
    return TestClient(app)


def make_expense(**overrides):
    payload = {
        "title": "Coffee",
        "amount": 4.5,
        "category": "Food",
        "date": "2026-07-01",
    }
    payload.update(overrides)
    return payload


def test_add_expense_returns_created_expense_with_id(client):
    response = client.post("/expenses", json=make_expense())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Coffee"
    assert body["amount"] == 4.5
    assert body["category"] == "Food"
    assert body["date"] == "2026-07-01"


def test_add_expense_rejects_non_positive_amount(client):
    response = client.post("/expenses", json=make_expense(amount=0))

    assert response.status_code == 422


def test_add_expense_rejects_empty_title(client):
    response = client.post("/expenses", json=make_expense(title=""))

    assert response.status_code == 422


def test_list_expenses_returns_all_added_expenses(client):
    client.post("/expenses", json=make_expense(title="Coffee"))
    client.post("/expenses", json=make_expense(title="Bus ticket", category="Transport"))

    response = client.get("/expenses")

    assert response.status_code == 200
    titles = [e["title"] for e in response.json()]
    assert titles == ["Coffee", "Bus ticket"]


def test_list_expenses_empty_when_none_added(client):
    response = client.get("/expenses")

    assert response.status_code == 200
    assert response.json() == []


def test_filter_expenses_by_category(client):
    client.post("/expenses", json=make_expense(title="Coffee", category="Food"))
    client.post("/expenses", json=make_expense(title="Bus ticket", category="Transport"))
    client.post("/expenses", json=make_expense(title="Lunch", category="Food"))

    response = client.get("/expenses", params={"category": "Food"})

    assert response.status_code == 200
    titles = [e["title"] for e in response.json()]
    assert titles == ["Coffee", "Lunch"]


def test_filter_expenses_by_category_is_case_insensitive(client):
    client.post("/expenses", json=make_expense(category="Food"))

    response = client.get("/expenses", params={"category": "food"})

    assert len(response.json()) == 1


def test_filter_expenses_by_unknown_category_returns_empty_list(client):
    client.post("/expenses", json=make_expense(category="Food"))

    response = client.get("/expenses", params={"category": "Nonexistent"})

    assert response.status_code == 200
    assert response.json() == []


def test_totals_overall_and_by_category(client):
    client.post("/expenses", json=make_expense(amount=10, category="Food"))
    client.post("/expenses", json=make_expense(amount=5, category="Food"))
    client.post("/expenses", json=make_expense(amount=20, category="Transport"))

    response = client.get("/expenses/total")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_total"] == 35
    by_category = {c["category"]: c["total"] for c in body["by_category"]}
    assert by_category == {"Food": 15, "Transport": 20}


def test_totals_with_no_expenses_is_zero(client):
    response = client.get("/expenses/total")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_total"] == 0
    assert body["by_category"] == []


def test_delete_expense_removes_it(client):
    created = client.post("/expenses", json=make_expense()).json()

    response = client.delete(f"/expenses/{created['id']}")

    assert response.status_code == 204
    assert client.get("/expenses").json() == []


def test_delete_nonexistent_expense_returns_404(client):
    response = client.delete("/expenses/999")

    assert response.status_code == 404

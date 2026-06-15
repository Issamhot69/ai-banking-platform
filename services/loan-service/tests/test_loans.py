import pytest
import uuid

TEST_ACCOUNT_ID = "55555555-6666-7777-8888-999999999999"

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "loan_types" in data

class TestLoanSimulation:
    async def test_simulate_personal_loan(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 10000,
            "term_months": 24,
            "loan_type": "personal",
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert float(data["amount"]) == 10000
        assert float(data["monthly_payment"]) > 0
        assert float(data["interest_rate"]) > 0
        assert float(data["total_repayment"]) > 10000

    async def test_simulate_mortgage(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 50000,
            "term_months": 60,
            "loan_type": "mortgage",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert float(response.json()["interest_rate"]) < 6.0

    async def test_simulate_invalid_amount(self, client, auth_headers):
        response = await client.post("/api/v1/loans/apply", json={
            "account_id": TEST_ACCOUNT_ID,
            "loan_type": "personal",
            "amount_requested": 50,
            "term_months": 12,
            "purpose": "Test",
            "monthly_income": 3000,
            "employment_status": "employed",
        }, headers=auth_headers)
        assert response.status_code == 422

    async def test_simulate_schedule_returned(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 5000,
            "term_months": 12,
            "loan_type": "auto",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert "schedule" in response.json()

class TestLoanApplication:
    async def test_apply_personal_loan(self, client, auth_headers):
        response = await client.post("/api/v1/loans/apply", json={
            "account_id": TEST_ACCOUNT_ID,
            "loan_type": "personal",
            "amount_requested": 10000,
            "term_months": 24,
            "purpose": "Home renovation",
            "monthly_income": 3500,
            "employment_status": "employed",
        }, headers=auth_headers)
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert data["status"] in ["approved", "rejected"]

    async def test_get_my_loans(self, client, auth_headers):
        response = await client.get("/api/v1/loans/my-loans", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_simulate_unemployed_rejected(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 5000,
            "term_months": 12,
            "loan_type": "personal",
            "monthly_income": 1000,
        }, headers=auth_headers)
        assert response.status_code == 200

    async def test_loan_type_education(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 15000,
            "term_months": 36,
            "loan_type": "education",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert float(response.json()["interest_rate"]) < 7.0

    async def test_loan_type_business(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 20000,
            "term_months": 48,
            "loan_type": "business",
        }, headers=auth_headers)
        assert response.status_code == 200

    async def test_invalid_loan_type(self, client, auth_headers):
        response = await client.post("/api/v1/loans/simulate", json={
            "amount": 5000,
            "term_months": 12,
            "loan_type": "invalid_type",
        }, headers=auth_headers)
        assert response.status_code in [200, 422]

    async def test_invalid_term(self, client, auth_headers):
        response = await client.post("/api/v1/loans/apply", json={
            "account_id": TEST_ACCOUNT_ID,
            "loan_type": "personal",
            "amount_requested": 5000,
            "term_months": 200,
            "purpose": "Test",
            "monthly_income": 3000,
            "employment_status": "employed",
        }, headers=auth_headers)
        assert response.status_code == 422

import pytest

class TestHealth:
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "supported_cryptos" in data

class TestPrices:
    async def test_get_all_prices(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/prices", headers=auth_headers)
        assert response.status_code == 200
        prices = response.json()
        assert len(prices) > 0
        assert any(p["currency"] == "BTC" for p in prices)

    async def test_get_btc_price(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/prices/BTC", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "BTC"
        assert float(data["price_eur"]) > 0

    async def test_get_eth_price(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/prices/ETH", headers=auth_headers)
        assert response.status_code == 200
        assert float(response.json()["price_eur"]) > 0

    async def test_invalid_crypto(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/prices/INVALID", headers=auth_headers)
        assert response.status_code == 404

class TestWallets:
    async def test_create_btc_wallet(self, client, auth_headers):
        response = await client.post("/api/v1/crypto/wallets", json={
            "currency": "BTC"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["currency"] == "BTC"
        assert data["address"].startswith("1")
        assert float(data["balance"]) == 0

    async def test_create_eth_wallet(self, client, auth_headers):
        response = await client.post("/api/v1/crypto/wallets", json={
            "currency": "ETH"
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["currency"] == "ETH"

    async def test_create_duplicate_wallet(self, client, auth_headers):
        await client.post("/api/v1/crypto/wallets", json={"currency": "SOL"}, headers=auth_headers)
        response = await client.post("/api/v1/crypto/wallets", json={"currency": "SOL"}, headers=auth_headers)
        assert response.status_code == 400

    async def test_get_wallets(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/wallets", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_portfolio(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/portfolio", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_value_eur" in data
        assert "wallets" in data

class TestTransactions:
    async def test_buy_crypto(self, client, auth_headers):
        wallet_res = await client.post("/api/v1/crypto/wallets", json={"currency": "BNB"}, headers=auth_headers)
        wallet_id = wallet_res.json()["id"]
        response = await client.post("/api/v1/crypto/transactions", json={
            "wallet_id": wallet_id,
            "tx_type": "buy",
            "amount": 100,
            "description": "Test buy",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["tx_type"] == "buy"
        assert data["status"] == "completed"
        assert float(data["amount_eur"]) == 100

    async def test_get_transactions(self, client, auth_headers):
        response = await client.get("/api/v1/crypto/transactions", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

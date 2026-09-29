import httpx
import pytest

from app.api.main import app
from tests.conftest import FakeRedis


@pytest.fixture
async def api_client(wired_redis: FakeRedis) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_root_health_ok(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "product-api"


async def test_namespaced_health_ok(api_client: httpx.AsyncClient) -> None:
    r = await api_client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] is True


async def test_health_503_when_redis_down(
    api_client: httpx.AsyncClient, wired_redis: FakeRedis
) -> None:
    wired_redis.ping_error = ConnectionError("down")
    r = await api_client.get("/")
    assert r.status_code == 503


async def test_product_crud(api_client: httpx.AsyncClient) -> None:
    created = await api_client.post(
        "/products", json={"name": "Laptop", "price": 999.99, "quantity": 10}
    )
    assert created.status_code == 201
    pk = created.json()["pk"]
    assert pk

    fetched = await api_client.get(f"/products/{pk}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Laptop"

    listed = await api_client.get("/products")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = await api_client.delete(f"/products/{pk}")
    assert deleted.status_code == 204

    missing = await api_client.get(f"/products/{pk}")
    assert missing.status_code == 404


async def test_product_not_found(api_client: httpx.AsyncClient) -> None:
    assert (await api_client.get("/products/nope")).status_code == 404
    assert (await api_client.delete("/products/nope")).status_code == 404


async def test_product_validation(api_client: httpx.AsyncClient) -> None:
    r = await api_client.post("/products", json={"name": "   ", "price": 5, "quantity": 1})
    assert r.status_code == 422
    r = await api_client.post("/products", json={"name": "X", "price": -1, "quantity": 1})
    assert r.status_code == 422

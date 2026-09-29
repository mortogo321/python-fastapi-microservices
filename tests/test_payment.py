from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.libs import redis as redis_module
from app.payment import main as payment_main
from app.payment.order import OrderStatus
from tests.conftest import FakeRedis


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeAsyncClient:
    """Stand-in for httpx.AsyncClient with a scripted product-API response."""

    response: _FakeResponse = _FakeResponse(404)
    raised: Exception | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> "_FakeAsyncClient":
        if type(self).raised is not None:
            raise type(self).raised
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def get(self, url: str) -> _FakeResponse:
        if type(self).raised is not None:
            raise type(self).raised
        return type(self).response


@pytest.fixture
async def pay_client(wired_redis: FakeRedis) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=payment_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fake_product_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    _FakeAsyncClient.raised = None
    _FakeAsyncClient.response = _FakeResponse(404)


def _product_payload(pk: str = "prod-1", price: float = 100.0, quantity: int = 5) -> dict[str, Any]:
    return {"pk": pk, "name": "Widget", "price": price, "quantity": quantity}


async def test_payment_health(pay_client: httpx.AsyncClient) -> None:
    assert (await pay_client.get("/")).status_code == 200
    assert (await pay_client.get("/api/health")).status_code == 200


async def test_create_order_success(
    pay_client: httpx.AsyncClient, fake_product_api: None, wired_redis: FakeRedis
) -> None:
    _FakeAsyncClient.response = _FakeResponse(200, _product_payload())
    r = await pay_client.post("/orders", json={"id": "prod-1", "quantity": 2})
    assert r.status_code == 201
    body = r.json()
    assert body["product_id"] == "prod-1"
    assert body["price"] == 100.0
    assert body["fee"] == 20.0
    assert body["total"] == 220.0
    # Background completion ran inline in tests (delay forced to 0)
    stored = await redis_module.redis_client.get_model(body["pk"], "order", payment_main.Order)
    assert stored is not None
    assert stored.status == OrderStatus.COMPLETED
    assert len(wired_redis.streams.get("order_completed", [])) == 1
    # Completion updated in place — exactly one order key exists
    assert await redis_module.redis_client.get_all_keys("order") == [body["pk"]]


async def test_create_order_product_not_found(
    pay_client: httpx.AsyncClient, fake_product_api: None
) -> None:
    _FakeAsyncClient.response = _FakeResponse(404)
    r = await pay_client.post("/orders", json={"id": "missing", "quantity": 1})
    assert r.status_code == 404


async def test_create_order_insufficient_quantity(
    pay_client: httpx.AsyncClient, fake_product_api: None
) -> None:
    _FakeAsyncClient.response = _FakeResponse(200, _product_payload(quantity=1))
    r = await pay_client.post("/orders", json={"id": "prod-1", "quantity": 2})
    assert r.status_code == 400


async def test_create_order_upstream_error(
    pay_client: httpx.AsyncClient, fake_product_api: None
) -> None:
    _FakeAsyncClient.response = _FakeResponse(500)
    r = await pay_client.post("/orders", json={"id": "prod-1", "quantity": 1})
    assert r.status_code == 502


async def test_create_order_upstream_timeout(
    pay_client: httpx.AsyncClient, fake_product_api: None
) -> None:
    _FakeAsyncClient.raised = httpx.TimeoutException("slow")
    r = await pay_client.post("/orders", json={"id": "prod-1", "quantity": 1})
    assert r.status_code == 504


async def test_get_order_roundtrip(pay_client: httpx.AsyncClient, fake_product_api: None) -> None:
    _FakeAsyncClient.response = _FakeResponse(200, _product_payload())
    created = await pay_client.post("/orders", json={"id": "prod-1", "quantity": 1})
    pk = created.json()["pk"]
    fetched = await pay_client.get(f"/orders/{pk}")
    assert fetched.status_code == 200
    assert fetched.json()["pk"] == pk
    assert (await pay_client.get("/orders/missing")).status_code == 404


async def test_complete_order_missing_is_noop(wired_redis: FakeRedis) -> None:
    await payment_main.complete_order("does-not-exist")
    assert wired_redis.streams.get("order_completed", []) == []

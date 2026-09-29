from app.api.product import Product
from app.libs.redis import RedisClient
from tests.conftest import FakeRedis


async def test_save_get_update_delete_roundtrip(fake_redis: FakeRedis) -> None:
    client = RedisClient()
    client._client = fake_redis  # type: ignore[assignment]

    pk = await client.save_model(Product(name="Laptop", price=999.99, quantity=10), "product")
    assert pk

    loaded = await client.get_model(pk, "product", Product)
    assert loaded is not None
    assert loaded.name == "Laptop"
    assert loaded.price == 999.99

    # update_model must overwrite the SAME key (no duplicate keys)
    await client.update_model(pk, Product(name="Laptop Pro", price=1299.0, quantity=5), "product")
    assert await client.get_all_keys("product") == [pk]
    reloaded = await client.get_model(pk, "product", Product)
    assert reloaded is not None
    assert reloaded.name == "Laptop Pro"

    assert await client.delete_model(pk, "product") == 1
    assert await client.get_model(pk, "product", Product) is None
    assert await client.delete_model(pk, "product") == 0


async def test_get_all_keys_scoped_by_prefix(fake_redis: FakeRedis) -> None:
    client = RedisClient()
    client._client = fake_redis  # type: ignore[assignment]

    pk1 = await client.save_model(Product(name="A", price=1.0, quantity=1), "product")
    pk2 = await client.save_model(Product(name="B", price=2.0, quantity=2), "product")
    keys = await client.get_all_keys("product")
    assert sorted(keys) == sorted([pk1, pk2])


async def test_xadd_returns_entry_id(fake_redis: FakeRedis) -> None:
    client = RedisClient()
    client._client = fake_redis  # type: ignore[assignment]

    entry_id = await client.xadd("order_completed", {"pk": "abc", "total": 120.0})
    assert entry_id == "0-1"
    assert fake_redis.streams["order_completed"][0]["pk"] == "abc"


async def test_save_excludes_pk_from_hash(fake_redis: FakeRedis) -> None:
    client = RedisClient()
    client._client = fake_redis  # type: ignore[assignment]

    pk = await client.save_model(Product(name="A", price=1.0, quantity=1), "product")
    stored = fake_redis.hashes[f"product:{pk}"]
    assert "pk" not in stored

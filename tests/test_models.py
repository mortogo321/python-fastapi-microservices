import pytest
from pydantic import ValidationError

from app.api.product import Product
from app.payment.order import Order, OrderRequest, OrderStatus


def test_product_valid() -> None:
    p = Product(name=" Laptop ", price=999.99, quantity=10)
    assert p.name == "Laptop"
    assert p.pk is None


def test_product_name_blank_rejected() -> None:
    with pytest.raises(ValidationError):
        Product(name="   ", price=10.0, quantity=1)


def test_product_price_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Product(name="X", price=0.0, quantity=1)
    with pytest.raises(ValidationError):
        Product(name="X", price=-5.0, quantity=1)


def test_product_quantity_non_negative() -> None:
    with pytest.raises(ValidationError):
        Product(name="X", price=1.0, quantity=-1)
    assert Product(name="X", price=1.0, quantity=0).quantity == 0


def test_order_defaults_to_pending() -> None:
    o = Order(product_id="abc", price=100.0, fee=20.0, total=220.0, quantity=2)
    assert o.status == OrderStatus.PENDING


def test_order_request_quantity_bounds() -> None:
    with pytest.raises(ValidationError):
        OrderRequest(id="abc", quantity=0)
    with pytest.raises(ValidationError):
        OrderRequest(id="abc", quantity=1001)
    with pytest.raises(ValidationError):
        OrderRequest(id="", quantity=1)
    assert OrderRequest(id="abc", quantity=2).quantity == 2

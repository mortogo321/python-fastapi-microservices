from pydantic import BaseModel
from redis_om import HashModel

from app.libs.redis import database


class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str

    class Meta:
        database = database


class OrderRequest(BaseModel):
    id: str
    quantity: int

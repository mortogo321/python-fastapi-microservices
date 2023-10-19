from redis_om import HashModel

from app.redis import database


class Product(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = database

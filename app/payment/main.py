import time
from os import environ as env

import requests
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.libs.redis import database
from app.payment.order import Order, OrderRequest

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def welcome():
    return {"status": True, "message": "Payment OK"}


@app.get("/orders", response_model=list[Order])
def getOrders():
    return [getOrder(pk) for pk in Order.all_pks()]


@app.post("/orders", response_model=Order)
def createOrder(request: OrderRequest, tasks: BackgroundTasks):
    req = requests.get(f"{env['API_HOST']}/products/{request.id}")
    product = req.json()
    order = Order(
        product_id=product["pk"],
        price=product["price"],
        fee=0.2 * product["price"],
        total=1.2 * product["price"],
        quantity=request.quantity,
        status="pending",
    )
    order.save()

    tasks.add_task(completeOrder, order)

    return order


@app.get("/orders/{pk}", response_model=Order)
def getOrderById(pk: str):
    return getOrder(pk)


def getOrder(pk: str):
    return Order.get(pk)


def completeOrder(order: Order):
    time.sleep(5)
    order.status = "completed"
    order.save()
    database.xadd("order_completed", order.model_dump(), "*")

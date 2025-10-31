import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.libs.config import settings
from app.libs.logger import setup_logger
from app.libs.redis import redis_client
from app.payment.order import Order, OrderRequest, OrderStatus

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle (startup/shutdown)."""
    # Startup
    logger.info("Starting Payment service...")
    await redis_client.connect()
    logger.info("Redis connection established")
    yield
    # Shutdown
    logger.info("Shutting down Payment service...")
    await redis_client.disconnect()
    logger.info("Redis connection closed")


app = FastAPI(
    title="Payment Service",
    description="Microservice for processing orders and payments",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str | bool]:
    """Health check endpoint."""
    try:
        # Test Redis connection
        await redis_client.client.ping()
        return {"status": True, "message": "Payment service is healthy", "service": "payment"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy - Redis connection failed",
        )


@app.get("/orders", response_model=list[Order], tags=["Orders"])
async def get_all_orders() -> list[Order]:
    """Get all orders."""
    try:
        logger.info("Fetching all orders")
        pks = await redis_client.get_all_keys("order")
        orders = []
        for pk in pks:
            order = await redis_client.get_model(pk, "order", Order)
            if order:
                order.pk = pk
                orders.append(order)
        logger.info(f"Retrieved {len(orders)} orders")
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders",
        )


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(request: OrderRequest, background_tasks: BackgroundTasks) -> Order:
    """Create a new order from a product."""
    try:
        logger.info(f"Creating order for product: {request.id}")

        # Fetch product from Product API using httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.api_host}/products/{request.id}")

            if response.status_code == 404:
                logger.warning(f"Product not found: {request.id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {request.id} not found",
                )

            if response.status_code != 200:
                logger.error(f"Failed to fetch product: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch product from API",
                )

            product = response.json()

        # Validate product availability
        if product.get("quantity", 0) < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient product quantity. Available: {product.get('quantity', 0)}",
            )

        # Calculate order details
        price = float(product["price"])
        fee = 0.2 * price
        total = price * request.quantity + fee

        # Create order
        order = Order(
            product_id=product["pk"],
            price=price,
            fee=fee,
            total=total,
            quantity=request.quantity,
            status=OrderStatus.PENDING,
        )

        # Save order to Redis
        pk = await redis_client.save_model(order, "order")
        order.pk = pk

        logger.info(f"Order created with ID: {pk}")

        # Schedule background task to complete order
        background_tasks.add_task(complete_order, pk)

        return order

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


@app.get("/orders/{pk}", response_model=Order, tags=["Orders"])
async def get_order_by_id(pk: str) -> Order:
    """Get an order by ID."""
    try:
        logger.info(f"Fetching order with ID: {pk}")
        order = await redis_client.get_model(pk, "order", Order)
        if not order:
            logger.warning(f"Order not found: {pk}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {pk} not found",
            )
        order.pk = pk
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {pk}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order",
        )


async def complete_order(order_pk: str) -> None:
    """Background task to complete an order after processing."""
    try:
        logger.info(f"Processing order completion for: {order_pk}")

        # Simulate payment processing delay
        await asyncio.sleep(5)

        # Fetch the order
        order = await redis_client.get_model(order_pk, "order", Order)
        if not order:
            logger.error(f"Order not found for completion: {order_pk}")
            return

        # Update order status
        order.status = OrderStatus.COMPLETED
        order.pk = order_pk

        # Save updated order
        await redis_client.save_model(order, "order")

        # Publish event to Redis stream
        await redis_client.xadd("order_completed", order.model_dump())

        logger.info(f"Order completed: {order_pk}")

    except Exception as e:
        logger.error(f"Error completing order {order_pk}: {e}")
        # Update order status to failed
        try:
            order = await redis_client.get_model(order_pk, "order", Order)
            if order:
                order.status = OrderStatus.FAILED
                order.pk = order_pk
                await redis_client.save_model(order, "order")
        except Exception as save_error:
            logger.error(f"Failed to update order status to failed: {save_error}")

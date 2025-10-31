from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.product import Product
from app.libs.logger import setup_logger
from app.libs.redis import redis_client

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle (startup/shutdown)."""
    # Startup
    logger.info("Starting Product API service...")
    await redis_client.connect()
    logger.info("Redis connection established")
    yield
    # Shutdown
    logger.info("Shutting down Product API service...")
    await redis_client.disconnect()
    logger.info("Redis connection closed")


app = FastAPI(
    title="Product API",
    description="Microservice for managing products",
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
        return {"status": True, "message": "Product API is healthy", "service": "product-api"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy - Redis connection failed",
        )


@app.get("/products", response_model=list[Product], tags=["Products"])
async def get_all_products() -> list[Product]:
    """Get all products."""
    try:
        logger.info("Fetching all products")
        pks = await redis_client.get_all_keys("product")
        products = []
        for pk in pks:
            product = await redis_client.get_model(pk, "product", Product)
            if product:
                product.pk = pk
                products.append(product)
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch products",
        )


@app.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
async def create_product(product: Product) -> Product:
    """Create a new product."""
    try:
        logger.info(f"Creating product: {product.name}")
        pk = await redis_client.save_model(product, "product")
        product.pk = pk
        logger.info(f"Product created with ID: {pk}")
        return product
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        )


@app.get("/products/{pk}", response_model=Product, tags=["Products"])
async def get_product_by_id(pk: str) -> Product:
    """Get a product by ID."""
    try:
        logger.info(f"Fetching product with ID: {pk}")
        product = await redis_client.get_model(pk, "product", Product)
        if not product:
            logger.warning(f"Product not found: {pk}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {pk} not found",
            )
        product.pk = pk
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {pk}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product",
        )


@app.delete("/products/{pk}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
async def delete_product(pk: str) -> None:
    """Delete a product by ID."""
    try:
        logger.info(f"Deleting product with ID: {pk}")
        deleted = await redis_client.delete_model(pk, "product")
        if deleted == 0:
            logger.warning(f"Product not found for deletion: {pk}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {pk} not found",
            )
        logger.info(f"Product deleted: {pk}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {pk}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product",
        )

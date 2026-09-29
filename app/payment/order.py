from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(StrEnum):
    """Order status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Order(BaseModel):
    """Order model with validation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "abc123",
                "price": 99.99,
                "fee": 19.99,
                "total": 119.98,
                "quantity": 1,
                "status": "pending",
            }
        }
    )

    pk: str | None = None  # Primary key, set after saving
    product_id: str = Field(..., description="Product ID")
    price: float = Field(..., gt=0, description="Product price")
    fee: float = Field(..., ge=0, description="Processing fee")
    total: float = Field(..., gt=0, description="Total amount")
    quantity: int = Field(..., gt=0, description="Order quantity must be positive")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")


class OrderRequest(BaseModel):
    """Order creation request."""

    model_config = ConfigDict(json_schema_extra={"example": {"id": "abc123", "quantity": 2}})

    id: str = Field(..., min_length=1, max_length=200, description="Product ID to order")
    quantity: int = Field(..., gt=0, le=1000, description="Quantity must be positive")

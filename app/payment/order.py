from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Order(BaseModel):
    """Order model with validation."""

    pk: str | None = None  # Primary key, set after saving
    product_id: str = Field(..., description="Product ID")
    price: float = Field(..., gt=0, description="Product price")
    fee: float = Field(..., ge=0, description="Processing fee")
    total: float = Field(..., gt=0, description="Total amount")
    quantity: int = Field(..., gt=0, description="Order quantity must be positive")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "abc123",
                "price": 99.99,
                "fee": 19.99,
                "total": 119.98,
                "quantity": 1,
                "status": "pending",
            }
        }


class OrderRequest(BaseModel):
    """Order creation request."""

    id: str = Field(..., description="Product ID to order")
    quantity: int = Field(..., gt=0, description="Quantity must be positive")

    class Config:
        json_schema_extra = {"example": {"id": "abc123", "quantity": 2}}

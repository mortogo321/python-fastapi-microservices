from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    """Product model with validation."""

    pk: str | None = None  # Primary key, set after saving
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    price: float = Field(..., gt=0, description="Product price must be positive")
    quantity: int = Field(..., ge=0, description="Product quantity must be non-negative")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name is not empty after stripping."""
        if not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Laptop",
                "price": 999.99,
                "quantity": 10,
            }
        }

"""Product domain models and schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from beanie import Document
from bson import Decimal128
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Product(Document):
    """Product document stored in MongoDB."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        """Beanie document settings."""

        name = "products"
        indexes: ClassVar[list[str]] = [
            "name",
            "category",
            "is_active",
            "created_at",
        ]

    @field_validator("price", mode="before")
    @classmethod
    def convert_decimal128(cls, v: Decimal | Decimal128 | str | float) -> Decimal:
        """Convert Decimal128 from MongoDB to Python Decimal."""
        if isinstance(v, Decimal128):
            return v.to_decimal()
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @field_serializer("id")
    @classmethod
    def serialize_id(cls, v: object) -> str | None:
        """Serialize ObjectId to string."""
        if v is None:
            return None
        return str(v)


class ProductCreate(BaseModel):
    """Schema for creating a new product."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        json_schema_extra={"example": "99.99"},
    )
    stock: int = Field(default=0, ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    is_active: bool = Field(default=True)


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        json_schema_extra={"example": "99.99"},
    )
    stock: int | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Schema for product API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    price: Decimal = Field(json_schema_extra={"example": "99.99"})
    stock: int
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("price")
    @classmethod
    def serialize_price(cls, v: Decimal) -> str:
        """Serialize Decimal to string with 2 decimal places."""
        return f"{v:.2f}"

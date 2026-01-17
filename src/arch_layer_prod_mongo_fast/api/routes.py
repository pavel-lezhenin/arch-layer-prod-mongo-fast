"""API routes for product operations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from arch_layer_prod_mongo_fast.api.dependencies import get_product_service
from arch_layer_prod_mongo_fast.exceptions import NotFoundError
from arch_layer_prod_mongo_fast.models import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from arch_layer_prod_mongo_fast.services import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["products"])


# =============================================================================
# COLLECTION ENDPOINTS (must be before /{product_id} to avoid conflicts)
# =============================================================================


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    category: str | None = None,
    is_active: bool | None = None,
) -> list[ProductResponse]:
    """List products with optional filtering."""
    products = await service.list_all(
        skip=skip,
        limit=limit,
        category=category,
        is_active=is_active,
    )
    return [ProductResponse(**p.model_dump()) for p in products]


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Create a new product."""
    product = await service.create(data)
    return ProductResponse(**product.model_dump())


# =============================================================================
# SEARCH ENDPOINTS (must be before /{product_id})
# =============================================================================


@router.get("/search/text", response_model=list[ProductResponse])
async def search_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    q: str = Query(..., min_length=1),
    size: int = Query(default=10, ge=1, le=100),
) -> list[ProductResponse]:
    """Full-text search using Elasticsearch."""
    results = await service.search(q, size)
    return [ProductResponse(**r) for r in results]


@router.get("/search/category/{category}", response_model=list[ProductResponse])
async def search_by_category(
    category: str,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> list[ProductResponse]:
    """Search products by category using Elasticsearch."""
    results = await service.search_by_category(category)
    return [ProductResponse(**r) for r in results]


@router.get("/search/price", response_model=list[ProductResponse])
async def search_by_price_range(
    service: Annotated[ProductService, Depends(get_product_service)],
    min_price: float = Query(..., ge=0),
    max_price: float = Query(..., ge=0),
) -> list[ProductResponse]:
    """Search products by price range."""
    results = await service.search_by_price_range(min_price, max_price)
    return [ProductResponse(**r) for r in results]


# =============================================================================
# ADMIN ENDPOINTS (must be before /{product_id})
# =============================================================================


@router.post("/reindex", status_code=status.HTTP_200_OK)
async def reindex_products(
    service: Annotated[ProductService, Depends(get_product_service)],
) -> dict[str, int]:
    """Reindex all products in Elasticsearch."""
    count = await service.reindex_all()
    return {"indexed": count}


@router.delete("/cache", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cache(
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    """Clear all product caches."""
    await service.clear_cache()


@router.get("/stats/count", response_model=dict[str, int])
async def get_count(
    service: Annotated[ProductService, Depends(get_product_service)],
) -> dict[str, int]:
    """Get total product count."""
    count = await service.count()
    return {"total": count}


# =============================================================================
# ITEM ENDPOINTS (with path parameter - must be LAST)
# =============================================================================


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Get product by ID (cached)."""
    try:
        product = await service.get_by_id(product_id)
        return ProductResponse(**product.model_dump())
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Update an existing product."""
    try:
        product = await service.update(product_id, data)
        return ProductResponse(**product.model_dump())
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    """Delete a product."""
    try:
        await service.delete(product_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

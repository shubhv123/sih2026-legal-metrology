from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import ProductCategory


class ProductBase(BaseModel):
    product_name: str
    brand_name: str | None = None
    category: ProductCategory = ProductCategory.STANDARD_RETAIL
    net_quantity_declared: str | None = None
    mrp_declared: float | None = None
    country_of_origin: str | None = "India"
    manufacturer_details: str | None = None
    mfg_date: str | None = None
    expiry_date: str | None = None
    consumer_care: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

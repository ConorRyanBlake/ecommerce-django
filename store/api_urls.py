"""
URL patterns for the eCommerce REST API.

All routes here are prefixed with /api/v1/ in the main project urls.py,
so the actual endpoints look like /api/v1/vendors/<id>/stores/ etc.
"""

from django.urls import path
from . import api_views

app_name = "store_api"

urlpatterns = [
    # Public reads
    path(
        "vendors/<int:vendor_id>/stores/",
        api_views.vendor_stores,
        name="vendor_stores",
    ),
    path(
        "stores/<int:store_id>/products/",
        api_views.store_products,
        name="store_products",
    ),
    # Vendor-only read
    path(
        "products/<int:product_id>/reviews/",
        api_views.product_reviews,
        name="product_reviews",
    ),
    # Vendor write endpoints
    path("stores/", api_views.api_store_create, name="store_create"),
    path(
        "stores/<int:store_id>/products/add/",
        api_views.api_store_add_product,
        name="store_add_product",
    ),
]

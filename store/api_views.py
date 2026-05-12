"""
REST API views for the eCommerce app.

These mirror parts of views.py but return JSON/XML instead of HTML,
and use HTTP status codes + Basic Auth instead of Django sessions
and flash messages.
"""

from itertools import product

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Store, Product, Review
from .serializers import StoreSerializer, ProductSerializer, ReviewSerializer
from .views import is_vendor, tweet_about_new_store, tweet_about_new_product

# ============================================================
# PUBLIC READ ENDPOINTS - no auth required
# ============================================================


@api_view(["GET"])
def vendor_stores(request, vendor_id):
    """List all stores belonging to a specific vendor."""
    stores = Store.objects.filter(owner_id=vendor_id)
    serializer = StoreSerializer(stores, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def store_products(request, store_id):
    """List all products in a specific store."""
    # Confirm the store exists, returns 404 if not
    get_object_or_404(Store, id=store_id)
    products = Product.objects.filter(store_id=store_id)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


# ============================================================
# VENDOR-ONLY READ - retrieve reviews on a product you own
# ============================================================


@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def product_reviews(request, product_id):
    """List reviews for a product. Only the vendor who owns the product can access."""
    product = get_object_or_404(Product, id=product_id)

    if not is_vendor(request.user):
        return Response(
            {"error": "Only vendors can retrieve reviews."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if product.store.owner != request.user:
        return Response(
            {"error": "You can only view reviews on your own products."},
            status=status.HTTP_403_FORBIDDEN,
        )

    reviews = product.reviews.all().order_by("-created_at")
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


# ============================================================
# VENDOR WRITE ENDPOINTS - auth + role check
# ============================================================


@api_view(["POST"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def api_store_create(request):
    """Create a new store. The owner is auto-set to the authenticated user."""
    if not is_vendor(request.user):
        return Response(
            {"error": "Only vendors can create stores."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = StoreSerializer(data=request.data)
    if serializer.is_valid():
        # Owner is set server-side, not from the request body
        store = serializer.save(owner=request.user)
        tweet_about_new_store(store)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def api_store_add_product(request, store_id):
    """Add a product to a store. The store must belong to the authenticated vendor."""
    if not is_vendor(request.user):
        return Response(
            {"error": "Only vendors can add products."},
            status=status.HTTP_403_FORBIDDEN,
        )

    store = get_object_or_404(Store, id=store_id)

    if store.owner != request.user:
        return Response(
            {"error": "You can only add products to your own stores."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        # Store comes from the URL, not the request body
        product = serializer.save(store=store)
        tweet_about_new_product(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

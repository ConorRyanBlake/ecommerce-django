from rest_framework import serializers
from .models import Store, Product, Review


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "owner", "name", "description", "logo", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "store",
            "name",
            "description",
            "image",
            "price",
            "stock",
            "created_at",
        ]
        read_only_fields = ["id", "store", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "buyer",
            "rating",
            "comment",
            "verified",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

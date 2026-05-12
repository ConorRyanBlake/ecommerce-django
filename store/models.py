from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Profile(models.Model):
    """Extends the built-in User with a role (vendor or buyer)."""

    ROLE_CHOICES = [
        ("vendor", "Vendor"),
        ("buyer", "Buyer"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Store(models.Model):
    """A vendor's shop. A vendor can own multiple stores."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.URLField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stores")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """A product belonging to a store."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    """A completed order. Created when a buyer checks out."""

    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"


class OrderItem(models.Model):
    """A single product line within an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        product_name = self.product.name if self.product else "[deleted]"
        return f"{self.quantity}x {product_name}"

    def subtotal(self):
        return self.quantity * self.price_at_purchase


class Review(models.Model):
    """A buyer's review on a product. Marked verified if the buyer purchased it."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField()  # 1 to 5
    comment = models.TextField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        tag = "verified" if self.verified else "unverified"
        return f"{self.buyer.username} on {self.product.name} ({tag})"


class ResetToken(models.Model):
    """A password reset token that expires after a short time."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reset_tokens"
    )
    token = models.CharField(max_length=500)
    expiry_date = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.username}"

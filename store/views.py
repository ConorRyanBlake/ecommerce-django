from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Store, Product

from .models import Profile


def is_vendor(user):
    """Check if a user has a vendor profile."""
    return (
        user.is_authenticated
        and hasattr(user, "profile")
        and user.profile.role == "vendor"
    )


def home(request):
    """Public landing page."""
    return render(request, "store/home.html")


def register_user(request):
    """Register a new user as either a vendor or buyer."""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_conf = request.POST.get("password_conf", "")
        role = request.POST.get("role", "")

        # --- Validation ---
        if not username or not email or not password or not role:
            messages.error(request, "All fields are required.")
            return render(request, "store/register.html")

        if password != password_conf:
            messages.error(request, "Passwords do not match.")
            return render(request, "store/register.html")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "store/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "store/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "That email is already registered.")
            return render(request, "store/register.html")

        if role not in ["vendor", "buyer"]:
            messages.error(request, "Please select a valid role.")
            return render(request, "store/register.html")

        # --- Create the user ---
        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        # Create the profile with the chosen role
        Profile.objects.create(user=user, role=role)

        # Add to the right group
        group_name = "Vendors" if role == "vendor" else "Buyers"
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            messages.warning(
                request, f"{group_name} group not found - permissions not set."
            )

        # Log them in straight away
        login(request, user)
        messages.success(
            request, f"Welcome, {username}! Your account has been created."
        )
        return redirect("store:home")

    return render(request, "store/register.html")


def login_user(request):
    """Log a user in with username and password."""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, "store/login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("store:home")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "store/login.html")

    return render(request, "store/login.html")


def logout_user(request):
    """Log the current user out."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("store:home")


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Store, Product

# ============================================================
# VENDOR VIEWS
# ============================================================


@login_required
def vendor_dashboard(request):
    """Show all stores owned by the current vendor."""
    if not is_vendor(request.user):
        messages.error(request, "Only vendors can access the dashboard.")
        return redirect("store:home")

    stores = Store.objects.filter(owner=request.user)
    return render(request, "store/vendor_dashboard.html", {"stores": stores})


@login_required
def store_create(request):
    """Vendor creates a new store."""
    if not is_vendor(request.user):
        messages.error(request, "Only vendors can create stores.")
        return redirect("store:home")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Store name is required.")
            return render(request, "store/store_form.html")

        store = Store.objects.create(
            name=name, description=description, owner=request.user
        )
        messages.success(request, f"Store '{store.name}' created.")
        return redirect("store:vendor_dashboard")

    return render(request, "store/store_form.html")


@login_required
def store_edit(request, store_id):
    """Vendor edits one of their stores."""
    store = get_object_or_404(Store, id=store_id)

    if store.owner != request.user:
        messages.error(request, "You can only edit your own stores.")
        return redirect("store:vendor_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Store name is required.")
            return render(request, "store/store_form.html", {"store": store})

        store.name = name
        store.description = description
        store.save()
        messages.success(request, "Store updated.")
        return redirect("store:vendor_dashboard")

    return render(request, "store/store_form.html", {"store": store})


@login_required
def store_delete(request, store_id):
    """Vendor deletes one of their stores."""
    store = get_object_or_404(Store, id=store_id)

    if store.owner != request.user:
        messages.error(request, "You can only delete your own stores.")
        return redirect("store:vendor_dashboard")

    if request.method == "POST":
        store.delete()
        messages.success(request, "Store deleted.")
        return redirect("store:vendor_dashboard")

    return render(request, "store/store_confirm_delete.html", {"store": store})


@login_required
def store_detail(request, store_id):
    """Show a store and its products. Vendors see edit/delete buttons for their own."""
    store = get_object_or_404(Store, id=store_id)
    products = store.products.all()
    is_owner = request.user == store.owner
    return render(
        request,
        "store/store_detail.html",
        {
            "store": store,
            "products": products,
            "is_owner": is_owner,
        },
    )


@login_required
def product_create(request, store_id):
    """Vendor adds a product to one of their stores."""
    store = get_object_or_404(Store, id=store_id)

    if store.owner != request.user:
        messages.error(request, "You can only add products to your own stores.")
        return redirect("store:vendor_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        stock = request.POST.get("stock", "").strip()

        # Validate
        if not name or not price or not stock:
            messages.error(request, "Name, price, and stock are required.")
            return render(request, "store/product_form.html", {"store": store})

        try:
            price_value = float(price)
            stock_value = int(stock)
            if price_value < 0 or stock_value < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Price and stock must be valid positive numbers.")
            return render(request, "store/product_form.html", {"store": store})

        Product.objects.create(
            name=name,
            description=description,
            price=price_value,
            stock=stock_value,
            store=store,
        )
        messages.success(request, f"Product '{name}' added.")
        return redirect("store:store_detail", store_id=store.id)

    return render(request, "store/product_form.html", {"store": store})


@login_required
def product_edit(request, product_id):
    """Vendor edits one of their products."""
    product = get_object_or_404(Product, id=product_id)

    if product.store.owner != request.user:
        messages.error(request, "You can only edit your own products.")
        return redirect("store:vendor_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        stock = request.POST.get("stock", "").strip()

        if not name or not price or not stock:
            messages.error(request, "Name, price, and stock are required.")
            return render(
                request,
                "store/product_form.html",
                {"product": product, "store": product.store},
            )

        try:
            price_value = float(price)
            stock_value = int(stock)
            if price_value < 0 or stock_value < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Price and stock must be valid positive numbers.")
            return render(
                request,
                "store/product_form.html",
                {"product": product, "store": product.store},
            )

        product.name = name
        product.description = description
        product.price = price_value
        product.stock = stock_value
        product.save()
        messages.success(request, "Product updated.")
        return redirect("store:store_detail", store_id=product.store.id)

    return render(
        request, "store/product_form.html", {"product": product, "store": product.store}
    )


@login_required
def product_delete(request, product_id):
    """Vendor deletes one of their products."""
    product = get_object_or_404(Product, id=product_id)

    if product.store.owner != request.user:
        messages.error(request, "You can only delete your own products.")
        return redirect("store:vendor_dashboard")

    store_id = product.store.id

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("store:store_detail", store_id=store_id)

    return render(request, "store/product_confirm_delete.html", {"product": product})


# ============================================================
# BUYER VIEWS - browsing and cart
# ============================================================


def is_buyer(user):
    """Check if a user has a buyer profile."""
    return (
        user.is_authenticated
        and hasattr(user, "profile")
        and user.profile.role == "buyer"
    )


def product_list(request):
    """Public page showing all products across all stores."""
    products = Product.objects.all().select_related("store").order_by("-created_at")
    return render(request, "store/product_list.html", {"products": products})


def product_detail(request, product_id):
    """Public page showing a single product with reviews."""
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by("-created_at")

    # Check if the current user has already reviewed this product
    user_review = None
    if request.user.is_authenticated and is_buyer(request.user):
        user_review = Review.objects.filter(buyer=request.user, product=product).first()

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "user_review": user_review,
        },
    )


@login_required
def add_to_cart(request, product_id):
    """Add a product to the buyer's cart (stored in session)."""
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can add items to a cart.")
        return redirect("store:product_list")

    product = get_object_or_404(Product, id=product_id)

    # Check stock
    if product.stock < 1:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect("store:product_detail", product_id=product.id)

    # Get quantity from form (default to 1)
    try:
        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    # Get the cart from the session, or start an empty one
    cart = request.session.get("cart", {})

    # Cart is a dict: {product_id_as_string: quantity}
    pid = str(product.id)
    current_quantity = cart.get(pid, 0)
    new_quantity = current_quantity + quantity

    # Don't allow more than stock
    if new_quantity > product.stock:
        messages.warning(
            request,
            f"Only {product.stock} of {product.name} available. Cart updated to max.",
        )
        new_quantity = product.stock

    cart[pid] = new_quantity
    request.session["cart"] = cart
    request.session.modified = True

    messages.success(request, f"Added {product.name} to your cart.")
    return redirect("store:cart")


@login_required
def cart_view(request):
    """Show the items in the buyer's cart."""
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can view a cart.")
        return redirect("store:home")

    cart = request.session.get("cart", {})
    items = []
    total = 0

    for pid, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
            subtotal = product.price * quantity
            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "subtotal": subtotal,
                }
            )
            total += subtotal
        except Product.DoesNotExist:
            # Product was deleted - skip it silently
            continue

    return render(request, "store/cart.html", {"items": items, "total": total})


@login_required
def cart_update(request, product_id):
    """Change the quantity of an item in the cart."""
    if not is_buyer(request.user):
        return redirect("store:home")

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1

        cart = request.session.get("cart", {})
        pid = str(product_id)

        if quantity < 1:
            # Remove if they set quantity to 0
            cart.pop(pid, None)
            messages.info(request, "Item removed from cart.")
        else:
            try:
                product = Product.objects.get(id=product_id)
                if quantity > product.stock:
                    quantity = product.stock
                    messages.warning(
                        request, f"Only {product.stock} available. Quantity capped."
                    )
                cart[pid] = quantity
                messages.success(request, "Cart updated.")
            except Product.DoesNotExist:
                cart.pop(pid, None)

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("store:cart")


@login_required
def cart_remove(request, product_id):
    """Remove an item from the cart entirely."""
    if not is_buyer(request.user):
        return redirect("store:home")

    cart = request.session.get("cart", {})
    pid = str(product_id)
    if pid in cart:
        cart.pop(pid)
        request.session["cart"] = cart
        request.session.modified = True
        messages.info(request, "Item removed from cart.")

    return redirect("store:cart")


# ============================================================
# CHECKOUT
# ============================================================

from django.db import transaction
from django.core.mail import EmailMessage
from .models import Order, OrderItem


@login_required
def checkout(request):
    """Process the buyer's cart into an Order, decrease stock, send invoice."""
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can check out.")
        return redirect("store:home")

    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("store:cart")

    # --- Build the list of items, validating stock and existence ---
    cart_items = []
    total = 0
    for pid, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
        except Product.DoesNotExist:
            messages.warning(
                request, "An item in your cart was removed because it no longer exists."
            )
            continue

        if product.stock < quantity:
            messages.error(
                request,
                f"Not enough stock for {product.name} (only {product.stock} left). "
                f"Please update your cart.",
            )
            return redirect("store:cart")

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "subtotal": product.price * quantity,
            }
        )
        total += product.price * quantity

    if not cart_items:
        messages.error(request, "Your cart is empty after removing missing items.")
        return redirect("store:cart")

    # Show confirmation page on GET, process order on POST
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Create the Order
                order = Order.objects.create(buyer=request.user, total=total)

                # Create OrderItems and decrease stock
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        quantity=item["quantity"],
                        price_at_purchase=item["price"],
                    )
                    # Decrease stock
                    item["product"].stock -= item["quantity"]
                    item["product"].save()

            # Clear the cart from the session
            request.session["cart"] = {}
            request.session.modified = True

            # Try to send the invoice email
            try:
                send_invoice_email(request.user, order, cart_items, total)
            except Exception as e:
                messages.warning(
                    request,
                    "Your order was placed, but we couldn't send the invoice email.",
                )

            messages.success(request, f"Order #{order.id} placed successfully!")
            return redirect("store:order_success", order_id=order.id)

        except Exception as e:
            messages.error(request, f"Something went wrong processing your order: {e}")
            return redirect("store:cart")

    # GET request - show the confirmation page
    return render(
        request,
        "store/checkout.html",
        {
            "items": cart_items,
            "total": total,
        },
    )


def send_invoice_email(user, order, items, total):
    """Build and send the invoice email."""
    subject = f"Invoice for Order #{order.id}"

    # Build the email body
    lines = [
        f"Hi {user.username},",
        "",
        f"Thank you for your order!",
        "",
        f"Order #{order.id}",
        f"Date: {order.created_at.strftime('%d %B %Y, %H:%M')}",
        "",
        "Items:",
        "-" * 50,
    ]
    for item in items:
        lines.append(
            f"  {item['quantity']} x {item['product'].name} "
            f"@ R{item['price']} = R{item['subtotal']}"
        )
    lines.append("-" * 50)
    lines.append(f"Total: R{total}")
    lines.append("")
    lines.append("Thank you for shopping with us!")

    body = "\n".join(lines)

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email="noreply@ecommerce.local",
        to=[user.email],
    )
    email.send()


@login_required
def order_success(request, order_id):
    """Show a success page after a completed order."""
    order = get_object_or_404(Order, id=order_id)

    # Only the buyer of this order can see the success page
    if order.buyer != request.user:
        messages.error(request, "You can only view your own orders.")
        return redirect("store:home")

    return render(request, "store/order_success.html", {"order": order})


@login_required
def order_history(request):
    """Show the buyer their past orders."""
    if not is_buyer(request.user):
        messages.error(request, "Only buyers have order history.")
        return redirect("store:home")

    orders = Order.objects.filter(buyer=request.user).order_by("-created_at")
    return render(request, "store/order_history.html", {"orders": orders})


# ============================================================
# REVIEWS
# ============================================================

from .models import Review


def buyer_has_purchased(user, product):
    """Check if a buyer has any OrderItem for this product."""
    return OrderItem.objects.filter(order__buyer=user, product=product).exists()


@login_required
def review_create(request, product_id):
    """Buyer leaves a review on a product."""
    if not is_buyer(request.user):
        messages.error(request, "Only buyers can leave reviews.")
        return redirect("store:product_detail", product_id=product_id)

    product = get_object_or_404(Product, id=product_id)

    # Check if this buyer has already reviewed this product
    existing = Review.objects.filter(buyer=request.user, product=product).first()
    if existing:
        messages.info(
            request,
            "You've already reviewed this product. You can edit your existing review.",
        )
        return redirect("store:review_edit", review_id=existing.id)

    if request.method == "POST":
        rating = request.POST.get("rating", "").strip()
        comment = request.POST.get("comment", "").strip()

        # Validate
        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Rating must be a number from 1 to 5.")
            return render(request, "store/review_form.html", {"product": product})

        if not comment:
            messages.error(request, "Please add a comment.")
            return render(request, "store/review_form.html", {"product": product})

        # Auto-detect verified status from purchase history
        verified = buyer_has_purchased(request.user, product)

        Review.objects.create(
            product=product,
            buyer=request.user,
            rating=rating_value,
            comment=comment,
            verified=verified,
        )

        if verified:
            messages.success(request, "Verified review posted.")
        else:
            messages.success(
                request,
                "Review posted (unverified — you haven't purchased this product).",
            )

        return redirect("store:product_detail", product_id=product.id)

    return render(request, "store/review_form.html", {"product": product})


@login_required
def review_edit(request, review_id):
    """Buyer edits their own review."""
    review = get_object_or_404(Review, id=review_id)

    if review.buyer != request.user:
        messages.error(request, "You can only edit your own reviews.")
        return redirect("store:product_detail", product_id=review.product.id)

    if request.method == "POST":
        rating = request.POST.get("rating", "").strip()
        comment = request.POST.get("comment", "").strip()

        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Rating must be a number from 1 to 5.")
            return render(
                request,
                "store/review_form.html",
                {"product": review.product, "review": review},
            )

        if not comment:
            messages.error(request, "Please add a comment.")
            return render(
                request,
                "store/review_form.html",
                {"product": review.product, "review": review},
            )

        review.rating = rating_value
        review.comment = comment
        # Re-check verified status in case they've now purchased it
        review.verified = buyer_has_purchased(request.user, review.product)
        review.save()

        messages.success(request, "Review updated.")
        return redirect("store:product_detail", product_id=review.product.id)

    return render(
        request, "store/review_form.html", {"product": review.product, "review": review}
    )


@login_required
def review_delete(request, review_id):
    """Buyer deletes their own review."""
    review = get_object_or_404(Review, id=review_id)

    if review.buyer != request.user:
        messages.error(request, "You can only delete your own reviews.")
        return redirect("store:product_detail", product_id=review.product.id)

    product_id = review.product.id

    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted.")
        return redirect("store:product_detail", product_id=product_id)

    return render(request, "store/review_confirm_delete.html", {"review": review})


# ============================================================
# PASSWORD RESET
# ============================================================

import secrets
from datetime import timedelta
from hashlib import sha1
from django.utils import timezone
from .models import ResetToken


def generate_reset_url(request, user):
    """Generate a tokenised reset URL for a user. Saves the hashed token to the DB."""
    # Create a URL-safe random token
    raw_token = secrets.token_urlsafe(16)

    # Hash it before storing - we never save the raw token in the database
    hashed_token = sha1(raw_token.encode()).hexdigest()

    # Token expires in 5 minutes
    expiry_date = timezone.now() + timedelta(minutes=5)

    # Save to database (linked to the user)
    ResetToken.objects.create(
        user=user, token=hashed_token, expiry_date=expiry_date, used=False
    )

    # Build the absolute URL using request to get the correct host/port
    reset_path = reverse("store:reset_password", args=[raw_token])
    full_url = request.build_absolute_uri(reset_path)

    return full_url


def send_reset_email(user, reset_url):
    """Send a password reset email to the user."""
    subject = "Reset your password"
    body = (
        f"Hi {user.username},\n\n"
        f"Someone (hopefully you) requested a password reset for your account.\n\n"
        f"Click this link to reset your password:\n"
        f"{reset_url}\n\n"
        f"This link will expire in 5 minutes for security.\n"
        f"If you didn't request this, just ignore this email.\n\n"
        f"- The eCommerce Team"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email="noreply@ecommerce.local",
        to=[user.email],
    )
    email.send()


def forgot_password(request):
    """Show the 'forgot password' form and handle email submission."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, "store/forgot_password.html")

        # Look up the user. Important: we don't tell the attacker whether
        # the email exists or not — same message either way.
        try:
            user = User.objects.get(email=email)
            reset_url = generate_reset_url(request, user)

            try:
                send_reset_email(user, reset_url)
            except Exception:
                # Even if email fails, don't expose that to the user
                pass
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist
            pass

        # Always show the same success message regardless
        messages.success(
            request,
            "If an account exists for that email, a reset link has been sent. "
            "Check your inbox (or your terminal in dev mode).",
        )
        return redirect("store:login")

    return render(request, "store/forgot_password.html")


def reset_password(request, token):
    """Handle the reset URL — validate the token and let the user set a new password."""
    # Strip whitespace in case the URL got copied with line breaks
    token = token.strip().replace(" ", "")
    # Hash the incoming token to look it up in the database
    hashed = sha1(token.encode()).hexdigest()

    try:
        reset_token = ResetToken.objects.get(token=hashed)
    except ResetToken.DoesNotExist:
        messages.error(request, "This reset link is invalid.")
        return redirect("store:login")

    # Check if already used
    if reset_token.used:
        messages.error(request, "This reset link has already been used.")
        return redirect("store:login")

    # Check expiry
    if reset_token.expiry_date < timezone.now():
        reset_token.delete()
        messages.error(
            request, "This reset link has expired. Please request a new one."
        )
        return redirect("store:forgot_password")

    # Token is valid. Process new password if submitted.
    if request.method == "POST":
        password = request.POST.get("password", "")
        password_conf = request.POST.get("password_conf", "")

        if not password or not password_conf:
            messages.error(request, "Please fill in both password fields.")
            return render(request, "store/reset_password.html", {"token": token})

        if password != password_conf:
            messages.error(request, "Passwords don't match.")
            return render(request, "store/reset_password.html", {"token": token})

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "store/reset_password.html", {"token": token})

        # Update password
        user = reset_token.user
        user.set_password(password)
        user.save()

        # Mark token as used and delete it
        reset_token.used = True
        reset_token.delete()

        messages.success(request, "Your password has been reset. You can log in now.")
        return redirect("store:login")

    return render(request, "store/reset_password.html", {"token": token})

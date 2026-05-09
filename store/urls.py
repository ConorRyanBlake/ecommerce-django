from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    # Auth
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    # Vendor
    path("dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("store/new/", views.store_create, name="store_create"),
    path("store/<int:store_id>/", views.store_detail, name="store_detail"),
    path("store/<int:store_id>/edit/", views.store_edit, name="store_edit"),
    path("store/<int:store_id>/delete/", views.store_delete, name="store_delete"),
    path(
        "store/<int:store_id>/product/new/", views.product_create, name="product_create"
    ),
    path("product/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path(
        "product/<int:product_id>/delete/", views.product_delete, name="product_delete"
    ),
    # Buyer / public
    path("products/", views.product_list, name="product_list"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/success/", views.order_success, name="order_success"),
    path("orders/", views.order_history, name="order_history"),
    # Reviews
    path("product/<int:product_id>/review/", views.review_create, name="review_create"),
    path("review/<int:review_id>/edit/", views.review_edit, name="review_edit"),
    path("review/<int:review_id>/delete/", views.review_delete, name="review_delete"),
    # Password reset
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("reset_password/<str:token>/", views.reset_password, name="reset_password"),
]

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Store, Product, Review, Order


class Command(BaseCommand):
    """Creates the Vendors and Buyers groups with appropriate permissions.

    Run this once after migrations. Safe to run again - it won't duplicate.
    """

    help = "Set up the Vendors and Buyers groups with correct permissions."

    def handle(self, *args, **options):
        # --- Vendors group ---
        vendors_group, created = Group.objects.get_or_create(name="Vendors")
        if created:
            self.stdout.write(self.style.SUCCESS("Created Vendors group"))
        else:
            self.stdout.write("Vendors group already exists, updating perms")

        # Get all permissions for Store and Product models
        store_perms = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Store)
        )
        product_perms = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Product)
        )

        # Vendors can fully manage their stores and products
        vendors_group.permissions.set(list(store_perms) + list(product_perms))
        self.stdout.write(
            f"  Assigned {vendors_group.permissions.count()} permissions to Vendors"
        )

        # --- Buyers group ---
        buyers_group, created = Group.objects.get_or_create(name="Buyers")
        if created:
            self.stdout.write(self.style.SUCCESS("Created Buyers group"))
        else:
            self.stdout.write("Buyers group already exists, updating perms")

        # Buyers get view-only on Product and Store, plus add Review and Order
        view_product = Permission.objects.get(
            codename="view_product",
            content_type=ContentType.objects.get_for_model(Product),
        )
        view_store = Permission.objects.get(
            codename="view_store", content_type=ContentType.objects.get_for_model(Store)
        )
        review_perms = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Review),
            codename__in=["add_review", "view_review"],
        )
        order_perms = Permission.objects.filter(
            content_type=ContentType.objects.get_for_model(Order),
            codename__in=["add_order", "view_order"],
        )

        buyer_perm_list = (
            [view_product, view_store] + list(review_perms) + list(order_perms)
        )
        buyers_group.permissions.set(buyer_perm_list)
        self.stdout.write(
            f"  Assigned {buyers_group.permissions.count()} permissions to Buyers"
        )

        self.stdout.write(self.style.SUCCESS("\nGroups setup complete!"))

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync data from Paddle"

    def handle(self, *args, **options):
        try:
            # ----------------
            # Address
            from django_paddle_billing.models import Address

            Address.sync_from_paddle()

            # ----------------
            # Business
            from django_paddle_billing.models import Business

            Business.sync_from_paddle()

            # ----------------
            # Products
            from django_paddle_billing.models import Product

            Product.sync_from_paddle()
            # products = Product.objects.all()

            # ----------------
            # Prices
            from django_paddle_billing.models import Price

            Price.sync_from_paddle()

            # ----------------
            # Discounts
            from django_paddle_billing.models import Discount

            Discount.sync_from_paddle()

            # ----------------
            # Customers
            from django_paddle_billing.models import Customer

            Customer.sync_from_paddle()

            # ----------------
            # Subscriptions
            from django_paddle_billing.models import Subscription

            Subscription.sync_from_paddle()

            # ----------------
            # Transactions
            from django_paddle_billing.models import Transaction

            Transaction.sync_from_paddle()

            self.stdout.write(self.style.SUCCESS("Successfully synced data from Paddle"))

        except Exception as e:
            self.stdout.write(self.style.ERROR("Failed to sync data from Paddle"))
            self.stdout.write(self.style.ERROR(e))

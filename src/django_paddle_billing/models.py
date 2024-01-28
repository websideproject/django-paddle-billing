from apiclient import HeaderAuthentication
from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver
from paddle_billing_client.client import PaddleApiClient
from paddle_billing_client.models import (
    address,
    business,
    customer,
    price,
    product,
    subscription,
    transaction,
)
from paddle_billing_client.pagination import paginate

from django_paddle_billing import settings, signals
from django_paddle_billing.encoders import PrettyJSONEncoder
from django_paddle_billing.exceptions import DjangoPaddleBillingError
from django_paddle_billing.utils import get_account_model

paddle_client = PaddleApiClient(
    base_url=settings.PADDLE_API_URL,
    authentication_method=HeaderAuthentication(token=settings.PADDLE_API_TOKEN),
)

UserModel = get_user_model()


class PaddleBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    occurred_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def validate_occurred_at(self, occurred_at):
        # Check if occurred_at is later than the current one
        if occurred_at is not None and self.occurred_at is not None and occurred_at < self.occurred_at:
            print(
                f"{self.__class__.__name__}: The event is invalid, occurred_at is earlier"
                " than the current one - SKIP UPDATE"
            )
            return False
        return True

    @classmethod
    def update_or_create(cls, query, defaults, occurred_at=None):
        created = False
        try:
            instance = cls.objects.get(**query)
            valid = instance.validate_occurred_at(occurred_at)
            if not valid:
                return instance, created

        except cls.DoesNotExist:
            instance = cls(**query)
            created = True

        for k, v in defaults.items():
            setattr(instance, k, v)

        if occurred_at is not None:
            instance.occurred_at = occurred_at

        instance.save()

        return instance, created


class Product(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=[("active", "Active"), ("archived", "Archived")])

    class Meta:
        pass

    def __str__(self):
        return f"{self.pk} - {self.name}"

    def get_data(self):
        if self.data is None:
            return None
        return product.Product.model_validate(self.data)

    @classmethod
    def api_list_products(cls):
        return paddle_client.list_products()

    @classmethod
    def api_list_products_generator(cls, **kwargs):
        yield from paginate(paddle_client.list_products, query_params=product.ProductQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None):
        try:
            _product, created = cls.update_or_create(
                query={"pk": data.id},
                defaults={
                    "name": data.name,
                    "status": data.status,
                    "data": data.dict(),
                    "custom_data": data.custom_data,
                },
                occurred_at=occurred_at,
            )
            return _product, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls):
        print("Sync Products from Paddle")
        created = 0
        updated = 0
        error = 0
        for products in cls.api_list_products_generator():
            for product_data in products.data:
                _product, _created, _error = cls.from_paddle_data(product_data)
                if _error:
                    error += 1
                elif _created:
                    created += 1
                else:
                    updated += 1
            print(f"Product sync progress --- synced: {updated}, created: {created}, errors: {error}")
        return created, updated


class Price(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return price.Price.model_validate(self.data)

    @classmethod
    def api_list_prices(cls):
        return paddle_client.list_prices()

    @classmethod
    def api_list_prices_generator(cls, **kwargs):
        yield from paginate(paddle_client.list_prices, **kwargs)

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None):
        try:
            _price, created = cls.update_or_create(
                query={"pk": data.id},
                defaults={
                    "product_id": data.product_id,
                    "data": data.dict(),
                    "custom_data": data.custom_data,
                },
                occurred_at=occurred_at,
            )
            return _price, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls):
        print("Sync Prices from Paddle")
        created = 0
        updated = 0
        error = 0
        for prices in cls.api_list_prices_generator():
            for price_data in prices.data:
                _price, _created, _error = cls.from_paddle_data(price_data)
                if _error:
                    error += 1
                elif _created:
                    created += 1
                else:
                    updated += 1
            print(f"Price sync progress --- synced: {updated}, created: {created}, errors: {error}")
        return created, updated


class Customer(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    user = models.ForeignKey(
        to=UserModel,
        null=True,
        on_delete=models.SET_NULL,
        related_name="customers",
    )

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return customer.Customer.model_validate(self.data)

    @classmethod
    def api_list_customers(cls):
        return paddle_client.list_customers()

    @classmethod
    def api_list_customers_generator(cls, **kwargs):
        yield from paginate(paddle_client.list_customers, query_params=customer.CustomerQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None):
        try:
            defaults = {
                "name": data.name,
                "email": data.email,
                "data": data.dict(),
                "custom_data": data.custom_data,
            }
            user = UserModel.objects.filter(email=data.email).first()
            if user is not None:
                defaults["user_id"] = user.pk

            instance, created = cls.update_or_create(
                query={"pk": data.id},
                defaults=defaults,
                occurred_at=occurred_at,
            )

            return instance, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls, include_addresses=True, include_businesses=True, include_subscriptions=True):
        print("Sync Customers from Paddle")
        created = 0
        updated = 0
        error = 0
        for customers in cls.api_list_customers_generator():
            for customer_data in customers.data:
                _customer, created, _error = cls.from_paddle_data(customer_data)
                if include_addresses:
                    _customer.sync_addresses_from_paddle()
                if include_businesses:
                    _customer.sync_businesses_from_paddle()
                if include_subscriptions:
                    _customer.sync_subscription_from_paddle()
                if _error:
                    error += 1
                elif created:
                    created += 1
                else:
                    updated += 1
            print(f"Customer sync progress --- synced: {updated}, created: {created}, error: {error}")

    def sync_addresses_from_paddle(self):
        print(f"Address sync from paddle for customer: {self.pk}")
        count = 0
        for addresses in Address.api_list_addresses_for_customer_generator(customer_id=self.pk):
            for address_data in addresses.data:
                Address.from_paddle_data(address_data, self.pk)
                count += 1
            print(f"Address sync progress --- synced: {count}")

    def sync_businesses_from_paddle(self):
        print(f"Business sync from paddle for customer: {self.pk}")
        count = 0
        for businesses in Business.api_list_businesses_for_customer_generator(customer_id=self.pk):
            for business_data in businesses.data:
                Business.from_paddle_data(business_data, self.pk)
                count += 1
            print(f"Business sync progress --- synced: {count}")

    def sync_subscription_from_paddle(self):
        print(f"Subscription sync from paddle for customer: {self.pk}")
        count = 0
        for subscriptions in Subscription.api_list_subscriptions_generator(customer_id=self.pk):
            for subscription_data in subscriptions.data:
                Subscription.from_paddle_data(subscription_data)
                count += 1
            print(f"Subscription sync progress --- synced: {count}")


class Address(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    country_code = models.CharField(max_length=2)

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return address.Address.model_validate(self.data)

    @classmethod
    def api_list_addresses_for_customer(cls, customer_id):
        return paddle_client.list_addresses_for_customer(customer_id=customer_id)

    @classmethod
    def api_list_addresses_for_customer_generator(cls, customer_id, **kwargs):
        yield from paginate(
            paddle_client.list_addresses_for_customer,
            customer_id=customer_id,
            query_params=address.AddressQueryParams(**kwargs),
        )

    @classmethod
    def from_paddle_data(cls, data, customer_id=None, occurred_at=None):
        try:
            defaults = {
                "data": data.dict(),
                "custom_data": data.custom_data,
                "country_code": data.country_code,
            }
            if customer_id is not None:
                defaults["customer_id"] = customer_id
            _address, created = cls.update_or_create(
                query={"pk": data.id},
                defaults=defaults,
                occurred_at=occurred_at,
            )
            return _address, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls):
        print("Address sync from paddle")
        customers = Customer.objects.all()
        for _customer in customers:
            for addresses in cls.api_list_addresses_for_customer_generator(customer_id=_customer.pk):
                for address_data in addresses.data:
                    cls.from_paddle_data(address_data, customer_id=_customer.pk)


class Business(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="businesses", null=True, blank=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return business.Business.model_validate(self.data)

    @classmethod
    def api_list_businesses_for_customer(cls, customer_id):
        return paddle_client.list_businesses_for_customer(customer_id=customer_id)

    @classmethod
    def api_list_businesses_for_customer_generator(cls, customer_id, **kwargs):
        yield from paginate(
            paddle_client.list_businesses_for_customer,
            customer_id=customer_id,
            query_params=business.BusinessQueryParams(**kwargs),
        )

    @classmethod
    def from_paddle_data(cls, data, customer_id, occurred_at=None):
        try:
            defaults = {
                "data": data.dict(),
                "custom_data": data.custom_data,
            }
            if customer_id is not None:
                defaults["customer_id"] = customer_id
            _business, created = cls.update_or_create(
                query={"pk": data.id},
                defaults=defaults,
                occurred_at=occurred_at,
            )
            return _business, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls):
        print("Business sync from paddle")
        customers = Customer.objects.all()
        for _customer in customers:
            for businesses in cls.api_list_businesses_for_customer_generator(customer_id=_customer.pk):
                for business_data in businesses.data:
                    cls.from_paddle_data(business_data, customer_id=_customer.pk)


class Subscription(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    account = models.ForeignKey(
        to=get_account_model(),
        null=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions",
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    address = models.ForeignKey(
        "Address", on_delete=models.CASCADE, null=True, blank=True, related_name="subscriptions"
    )
    business = models.ForeignKey(
        "Business", on_delete=models.CASCADE, null=True, blank=True, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("active", "Active"),
            ("trialing", "Trialing"),
            ("paused", "Paused"),
            ("deleted", "Deleted"),
        ],
    )
    products = models.ManyToManyField(Product, related_name="subscriptions")

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return subscription.Subscription.model_validate(self.data)

    @classmethod
    def api_list_subscriptions(cls):
        return paddle_client.list_subscriptions()

    @classmethod
    def api_list_subscriptions_generator(cls, **kwargs):
        yield from paginate(
            paddle_client.list_subscriptions, query_params=subscription.SubscriptionQueryParams(**kwargs)
        )

    @classmethod
    def api_get_subscription(cls, subscription_id):
        return paddle_client.get_subscription(subscription_id)

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None):
        error = None
        if data.custom_data is None or "account_id" not in data.custom_data:
            error = "Subscription: custom_data is None or account_id not in custom_data"
            # raise Exception('Subscription: custom_data is None or account_id not in custom_data')
            return None, False, error

        if not get_account_model().objects.filter(pk=int(data.custom_data["account_id"])).exists():
            error = "Subscription: Account with id: {} does not exist".format(data.custom_data["account_id"])
            # raise Exception('Subscription: Account with id: {} does not exist'.format(data.custom_data['account_id']))
            return None, False, error

        try:
            _subscription, created = cls.update_or_create(
                query={"pk": data.id},
                defaults={
                    "account_id": data.custom_data["account_id"],
                    "customer_id": data.customer_id,
                    "address_id": data.address_id,
                    "business_id": data.business_id,
                    "status": data.status,
                    "data": data.dict(),
                    "custom_data": data.custom_data,
                },
                occurred_at=occurred_at,
            )
            product_ids = [item.price.product_id for item in data.items]
            _subscription.products.set(product_ids)
            return _subscription, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls, **kwargs):
        print("Sync Subscriptions from Paddle")
        created = 0
        updated = 0
        error = 0
        for subscriptions in cls.api_list_subscriptions_generator(**kwargs):
            for subscription_data in subscriptions.data:
                _subscription, _created, _error = cls.from_paddle_data(subscription_data)
                if _error:
                    error += 1
                elif _created:
                    created += 1
                else:
                    updated += 1
            print(f"Subscription sync progress --- synced: {updated}, created: {created}, error: {error}")
        return created, updated


class Transaction(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="transactions")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True
    )

    class Meta:
        pass

    def __str__(self):
        return str(self.pk)

    def get_data(self):
        if self.data is None:
            return None
        return transaction.Transaction.model_validate(self.data)

    @classmethod
    def api_list_transactions(cls):
        return paddle_client.list_transactions()

    @classmethod
    def api_list_transactions_generator(cls, **kwargs):
        yield from paginate(paddle_client.list_transactions, query_params=transaction.TransactionQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None):
        try:
            _transaction, created = cls.update_or_create(
                query={"pk": data.id},
                defaults={
                    "customer_id": data.customer_id,
                    "subscription_id": data.subscription_id,
                    "data": data.dict(),
                    "custom_data": data.custom_data,
                },
                occurred_at=occurred_at,
            )
            return _transaction, created, None
        except Exception as e:
            print(e)
            return None, False, e

    @classmethod
    def sync_from_paddle(cls):
        print("Sync Transactions from Paddle")
        created = 0
        updated = 0
        error = 0
        for transactions in cls.api_list_transactions_generator():
            for transaction_data in transactions.data:
                _transaction, _created, _error = cls.from_paddle_data(transaction_data)
                if _error:
                    error += 1
                elif _created:
                    created += 1
                else:
                    updated += 1
            print(f"Transaction sync progress --- synced: {updated}, created: {created}, error: {error}")
        return created, updated

    @classmethod
    def sync_from_paddle_for_subscription(cls, subscription_id):
        print(f"Sync Transactions from Paddle for subscription: {subscription_id}")
        created = 0
        updated = 0
        for transactions in cls.api_list_transactions_generator(subscription_id=subscription_id):
            for transaction_data in transactions.data:
                if transaction_data.subscription_id == subscription_id:
                    _transaction, _created = cls.from_paddle_data(transaction_data)
                    if _created:
                        created += 1
                    else:
                        updated += 1
            print(f"Transaction sync progress --- synced: {updated}, created: {created}")
        return created, updated


@receiver(signals.address_created)
@receiver(signals.address_imported)
@receiver(signals.address_updated)
def address_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, address.Address):
        payload = address.Address.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Address.from_paddle_data(payload, None, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.business_created)
@receiver(signals.business_imported)
@receiver(signals.business_updated)
def business_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, business.Business):
        payload = business.Business.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Business.from_paddle_data(payload, None, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.customer_created)
@receiver(signals.customer_imported)
@receiver(signals.customer_updated)
def customer_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, customer.Customer):
        payload = customer.Customer.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Customer.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.price_created)
@receiver(signals.price_imported)
@receiver(signals.price_updated)
def price_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, price.Price):
        payload = price.Price.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Price.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.product_created)
@receiver(signals.product_imported)
@receiver(signals.product_updated)
def product_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, product.Product):
        payload = product.Product.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Product.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.subscription_activated)
@receiver(signals.subscription_canceled)
@receiver(signals.subscription_created)
@receiver(signals.subscription_imported)
@receiver(signals.subscription_past_due)
@receiver(signals.subscription_paused)
@receiver(signals.subscription_resumed)
@receiver(signals.subscription_trialing)
@receiver(signals.subscription_updated)
def subscription_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, subscription.Subscription):
        payload = subscription.Subscription.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Subscription.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.transaction_billed)
@receiver(signals.transaction_cancelled)
@receiver(signals.transaction_completed)
@receiver(signals.transaction_created)
@receiver(signals.transaction_paid)
@receiver(signals.transaction_past_due)
@receiver(signals.transaction_payment_failed)
@receiver(signals.transaction_ready)
@receiver(signals.transaction_updated)
def transaction_event_handler(sender, payload, *args, **kwargs):
    if not isinstance(payload, transaction.Transaction):
        payload = transaction.Transaction.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Transaction.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)

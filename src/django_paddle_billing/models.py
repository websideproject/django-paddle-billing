import logging
from typing import Iterator, TypeVar

from apiclient import HeaderAuthentication
from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver
from paddle_billing_client.client import PaddleApiClient
from paddle_billing_client.models import (
    address,
    business,
    customer,
    discount,
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

logger = logging.getLogger(__name__)

paddle_client = PaddleApiClient(
    base_url=settings.PADDLE_API_URL,
    authentication_method=HeaderAuthentication(token=settings.PADDLE_API_TOKEN),
)

UserModel = get_user_model()

T = TypeVar("T", bound="PaddleBaseModel")


class PaddleBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    occurred_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def validate_occurred_at(self, occurred_at) -> bool:
        # Check if occurred_at is later than the current one
        if occurred_at is not None and self.occurred_at is not None and occurred_at < self.occurred_at:
            logger.info(
                f"{self.__class__.__name__}: The event is invalid, occurred_at is earlier"
                " than the current one - SKIP UPDATE"
            )
            return False
        return True

    @classmethod
    def update_or_create(cls: type[T], query, defaults, occurred_at=None) -> tuple[T, bool]:
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

    def __str__(self) -> str:
        return f"{self.pk} - {self.name}"

    def get_data(self) -> product.Product | None:
        if self.data is None:
            return None
        return product.Product.model_validate(self.data)

    @classmethod
    def api_list_products(cls) -> product.ProductsResponse:
        return paddle_client.list_products()

    @classmethod
    def api_list_products_generator(cls, **kwargs) -> Iterator[product.ProductsResponse]:
        yield from paginate(paddle_client.list_products, query_params=product.ProductQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Product | None", bool, Exception | None]:
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
    def sync_from_paddle(cls) -> tuple[int, int]:
        logger.info("Sync Products from Paddle")
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
            logger.info("Product sync progress --- synced: %s, created: %s, errors: %s", updated, created, error)
        return created, updated


class Price(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")

    class Meta:
        pass

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> price.Price | None:
        if self.data is None:
            return None
        return price.Price.model_validate(self.data)

    @classmethod
    def api_list_prices(cls) -> price.PricesResponse:
        return paddle_client.list_prices()

    @classmethod
    def api_list_prices_generator(cls, **kwargs) -> Iterator[price.PricesResponse]:
        yield from paginate(paddle_client.list_prices, **kwargs)

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Price | None", bool, Exception | None]:
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
    def sync_from_paddle(cls) -> tuple[int, int]:
        logger.info("Sync Prices from Paddle")
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
            logger.info("Price sync progress --- synced: %s, created: %s, errors: %s", updated, created, error)
        return created, updated


class Discount(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)

    class Meta:
        pass

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> discount.Discount | None:
        if self.data is None:
            return None
        return discount.Discount.model_validate(self.data)

    @classmethod
    def api_list_discounts(cls) -> discount.DiscountsResponse:
        return paddle_client.list_discounts()

    @classmethod
    def api_list_discounts_generator(cls, **kwargs) -> Iterator[discount.DiscountsResponse]:
        yield from paginate(paddle_client.list_discounts, query_params=discount.DiscountQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Discount | None", bool, Exception | None]:
        try:
            _discount, created = cls.update_or_create(
                query={"pk": data.id},
                defaults={
                    "data": data.dict(),
                    "custom_data": data.custom_data,
                },
                occurred_at=occurred_at,
            )
            return _discount, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls) -> tuple[int, int]:
        logger.info("Sync Discounts from Paddle")
        created = 0
        updated = 0
        error = 0
        for discounts in cls.api_list_discounts_generator():
            for discount_data in discounts.data:
                _discount, _created, _error = cls.from_paddle_data(discount_data)
                if _error:
                    error += 1
                elif _created:
                    created += 1
                else:
                    updated += 1
            logger.info("Discount sync progress --- synced: %s, created: %s, errors: %s", updated, created, error)
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

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> customer.Customer | None:
        if self.data is None:
            return None
        return customer.Customer.model_validate(self.data)

    @classmethod
    def api_list_customers(cls) -> customer.CustomersResponse:
        return paddle_client.list_customers()

    @classmethod
    def api_list_customers_generator(cls, **kwargs) -> Iterator[customer.CustomersResponse]:
        yield from paginate(paddle_client.list_customers, query_params=customer.CustomerQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Customer | None", bool, Exception | None]:
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
    def sync_from_paddle(cls, include_addresses=True, include_businesses=True, include_subscriptions=True) -> None:
        logger.info("Sync Customers from Paddle")
        created = 0
        updated = 0
        error = 0
        for customers in cls.api_list_customers_generator():
            for customer_data in customers.data:
                _customer, created, _error = cls.from_paddle_data(customer_data)
                if _customer:
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
            logger.info("Customer sync progress --- synced: %s, created: %s, error: %s", updated, created, error)

    def sync_addresses_from_paddle(self) -> None:
        logger.info("Address sync from paddle for customer: %s", self.pk)
        count = 0
        for addresses in Address.api_list_addresses_for_customer_generator(customer_id=self.pk):
            for address_data in addresses.data:
                Address.from_paddle_data(address_data, self.pk)
                count += 1
            logger.info("Address sync progress --- synced: %s", count)

    def sync_businesses_from_paddle(self) -> None:
        logger.info("Business sync from paddle for customer: %s", self.pk)
        count = 0
        for businesses in Business.api_list_businesses_for_customer_generator(customer_id=self.pk):
            for business_data in businesses.data:
                Business.from_paddle_data(business_data, self.pk)
                count += 1
            logger.info("Business sync progress --- synced: %s", count)

    def sync_subscription_from_paddle(self) -> None:
        logger.info("Subscription sync from paddle for customer: %s", self.pk)
        count = 0
        for subscriptions in Subscription.api_list_subscriptions_generator(customer_id=self.pk):
            for subscription_data in subscriptions.data:
                Subscription.from_paddle_data(subscription_data)
                count += 1
            logger.info("Subscription sync progress --- synced: %s", count)


class Address(PaddleBaseModel):
    id = models.CharField(max_length=50, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True)
    data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    custom_data = models.JSONField(null=True, blank=True, encoder=PrettyJSONEncoder)
    country_code = models.CharField(max_length=2)

    class Meta:
        pass

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> address.Address | None:
        if self.data is None:
            return None
        return address.Address.model_validate(self.data)

    @classmethod
    def api_list_addresses_for_customer(cls, customer_id) -> address.AddressesResponse:
        return paddle_client.list_addresses_for_customer(customer_id=customer_id)

    @classmethod
    def api_list_addresses_for_customer_generator(cls, customer_id, **kwargs) -> Iterator[address.AddressesResponse]:
        yield from paginate(
            paddle_client.list_addresses_for_customer,
            customer_id=customer_id,
            query_params=address.AddressQueryParams(**kwargs),
        )

    @classmethod
    def from_paddle_data(
        cls, data, customer_id=None, occurred_at=None
    ) -> tuple["Address | None", bool, Exception | None]:
        try:
            defaults = {
                "data": data.dict(),
                "custom_data": data.custom_data,
                "country_code": data.country_code,
            }
            if customer_id is not None:
                defaults["customer_id"] = customer_id
            elif data.customer_id is not None:
                defaults["customer_id"] = data.customer_id
            _address, created = cls.update_or_create(
                query={"pk": data.id},
                defaults=defaults,
                occurred_at=occurred_at,
            )
            return _address, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls) -> None:
        logger.info("Address sync from paddle")
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

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> business.Business | None:
        if self.data is None:
            return None
        return business.Business.model_validate(self.data)

    @classmethod
    def api_list_businesses_for_customer(cls, customer_id) -> business.BusinessesResponse:
        return paddle_client.list_businesses_for_customer(customer_id=customer_id)

    @classmethod
    def api_list_businesses_for_customer_generator(cls, customer_id, **kwargs) -> Iterator[business.BusinessesResponse]:
        yield from paginate(
            paddle_client.list_businesses_for_customer,
            customer_id=customer_id,
            query_params=business.BusinessQueryParams(**kwargs),
        )

    @classmethod
    def from_paddle_data(cls, data, customer_id, occurred_at=None) -> tuple["Business | None", bool, Exception | None]:
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
    def sync_from_paddle(cls) -> None:
        logger.info("Business sync from paddle")
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
            ("canceled", "Canceled"),
            ("past_due", "Past Due"),
            ("paused", "Paused"),
            ("trialing", "Trialing"),
        ],
    )
    products = models.ManyToManyField(Product, related_name="subscriptions")

    class Meta:
        pass

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> subscription.Subscription | None:
        if self.data is None:
            return None
        return subscription.Subscription.model_validate(self.data)

    @classmethod
    def api_list_subscriptions(cls) -> subscription.SubscriptionsResponse:
        return paddle_client.list_subscriptions()

    @classmethod
    def api_list_subscriptions_generator(cls, **kwargs) -> Iterator[subscription.SubscriptionsResponse]:
        yield from paginate(
            paddle_client.list_subscriptions, query_params=subscription.SubscriptionQueryParams(**kwargs)
        )

    @classmethod
    def api_get_subscription(cls, subscription_id) -> subscription.SubscriptionResponse:
        return paddle_client.get_subscription(subscription_id)

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Subscription | None", bool, Exception | str | None]:
        account_id = None
        try:
            account_id = data.custom_data["account_id"]
        except (KeyError, TypeError):
            pass

        if account_id is not None:
            if not get_account_model().objects.filter(pk=account_id).exists():
                error = f"Subscription: Account with id: {account_id} does not exist"
                return None, False, error

        try:
            defaults = {
                "customer_id": data.customer_id,
                "address_id": data.address_id,
                "business_id": data.business_id,
                "status": data.status,
                "data": data.dict(),
                "custom_data": data.custom_data,
            }
            if account_id is not None:
                defaults["account_id"] = account_id
            _subscription, created = cls.update_or_create(
                query={"pk": data.id},
                defaults=defaults,
                occurred_at=occurred_at,
            )
            product_ids = [item.price.product_id for item in data.items]
            _subscription.products.set(product_ids)
            return _subscription, created, None
        except Exception as e:
            return None, False, e

    @classmethod
    def sync_from_paddle(cls, **kwargs) -> tuple[int, int]:
        logger.info("Sync Subscriptions from Paddle")
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
            logger.info("Subscription sync progress --- synced: %s, created: %s, error: %s", updated, created, error)
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

    def __str__(self) -> str:
        return str(self.pk)

    def get_data(self) -> transaction.Transaction | None:
        if self.data is None:
            return None
        return transaction.Transaction.model_validate(self.data)

    @classmethod
    def api_list_transactions(cls) -> transaction.TransactionsResponse:
        return paddle_client.list_transactions()

    @classmethod
    def api_list_transactions_generator(cls, **kwargs) -> Iterator[transaction.TransactionsResponse]:
        yield from paginate(paddle_client.list_transactions, query_params=transaction.TransactionQueryParams(**kwargs))

    @classmethod
    def from_paddle_data(cls, data, occurred_at=None) -> tuple["Transaction | None", bool, Exception | None]:
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
            logger.info(e)
            return None, False, e

    @classmethod
    def sync_from_paddle(cls) -> tuple[int, int]:
        logger.info("Sync Transactions from Paddle")
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
            logger.info("Transaction sync progress --- synced: %s, created: %s, error: %s", updated, created, error)
        return created, updated

    @classmethod
    def sync_from_paddle_for_subscription(cls, subscription_id) -> tuple[int, int]:
        logger.info("Sync Transactions from Paddle for subscription: %s", subscription_id)
        created = 0
        updated = 0
        error = 0
        for transactions in cls.api_list_transactions_generator(subscription_id=subscription_id):
            for transaction_data in transactions.data:
                if transaction_data.subscription_id == subscription_id:
                    _transaction, _created, _error = cls.from_paddle_data(transaction_data)
                    if _error:
                        error += 1
                    elif _created:
                        created += 1
                    else:
                        updated += 1
            logger.info("Transaction sync progress --- synced: %s, created: %s, error: %s", updated, created, error)
        return created, updated


@receiver(signals.address_created)
@receiver(signals.address_imported)
@receiver(signals.address_updated)
def address_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, address.Address):
        payload = address.Address.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Address.from_paddle_data(payload, None, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.adjustment_created)
@receiver(signals.adjustment_updated)
def adjustment_event_handler(sender, payload, *args, **kwargs) -> None:
    pass


@receiver(signals.business_created)
@receiver(signals.business_imported)
@receiver(signals.business_updated)
def business_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, business.Business):
        payload = business.Business.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Business.from_paddle_data(payload, None, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.customer_created)
@receiver(signals.customer_imported)
@receiver(signals.customer_updated)
def customer_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, customer.Customer):
        payload = customer.Customer.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Customer.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.discount_created)
@receiver(signals.discount_imported)
@receiver(signals.discount_updated)
def discount_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, discount.Discount):
        payload = discount.Discount.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Discount.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.payout_created)
@receiver(signals.payout_paid)
def payout_event_handler(sender, payload, *args, **kwargs) -> None:
    pass


@receiver(signals.price_created)
@receiver(signals.price_imported)
@receiver(signals.price_updated)
def price_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, price.Price):
        payload = price.Price.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Price.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.product_created)
@receiver(signals.product_imported)
@receiver(signals.product_updated)
def product_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, product.Product):
        payload = product.Product.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Product.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)


@receiver(signals.report_created)
@receiver(signals.report_updated)
def report_event_handler(sender, payload, *args, **kwargs) -> None:
    pass


@receiver(signals.subscription_activated)
@receiver(signals.subscription_canceled)
@receiver(signals.subscription_created)
@receiver(signals.subscription_imported)
@receiver(signals.subscription_past_due)
@receiver(signals.subscription_paused)
@receiver(signals.subscription_resumed)
@receiver(signals.subscription_trialing)
@receiver(signals.subscription_updated)
def subscription_event_handler(sender, payload, *args, **kwargs) -> None:
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
def transaction_event_handler(sender, payload, *args, **kwargs) -> None:
    if not isinstance(payload, transaction.Transaction):
        payload = transaction.Transaction.model_validate(payload)
    occurred_at = kwargs.get("occurred_at")

    _, _, error = Transaction.from_paddle_data(payload, occurred_at)
    if error:
        raise DjangoPaddleBillingError(error)

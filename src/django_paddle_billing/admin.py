import typing

from django.conf import settings
from django.contrib import admin
from django.db import models

from django_paddle_billing import settings as app_settings
from django_paddle_billing.models import (
    Address,
    Business,
    Customer,
    Discount,
    Price,
    Product,
    Subscription,
    Transaction,
)

# Check if unfold is in installed apps
if "unfold" in settings.INSTALLED_APPS:
    from unfold.admin import ModelAdmin, StackedInline, TabularInline
else:
    from django.contrib.admin import ModelAdmin, StackedInline, TabularInline


class AddressInline(StackedInline):
    model = Address
    extra = 1


class BusinessInline(StackedInline):
    model = Business
    extra = 1


class PriceInline(StackedInline):
    model = Price
    extra = 1


class ProductInline(TabularInline):
    model = Product.subscriptions.through
    extra = 1
    show_change_link = True


class CustomerInline(StackedInline):
    model = Customer
    extra = 1


class SubscriptionInline(StackedInline):
    model = Subscription
    extra = 1


class TransactionInline(TabularInline):
    model = Transaction
    extra = 1
    show_change_link = True


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ["customer_email", "country_code", "postal_code", "status"]
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def customer_email(self, obj=None):
        if obj and obj.customer:
            return obj.customer.email
        if obj:
            return obj.id
        return ""

    def postal_code(self, obj=None):
        if obj and obj.data:
            return obj.data.get("postal_code", "")
        return ""

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""


@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    list_display = [
        "name",
        "company_number",
        "tax_identifier",
        "status",
    ]
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def name(self, obj=None):
        if obj and obj.data:
            return obj.data.get("name", obj.id)
        if obj:
            return obj.id
        return ""

    def company_number(self, obj=None):
        if obj and obj.data:
            return obj.data.get("company_number", "")
        return ""

    def tax_identifier(self, obj=None):
        if obj and obj.data:
            return obj.data.get("tax_identifier", "")
        return ""

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        "name",
        "status",
        "created_at",
    ]
    search_fields = ["id", "name"]
    inlines = (PriceInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Price)
class PriceAdmin(ModelAdmin):
    list_display = [
        "name",
        "unit_price",
        "description",
        "status",
        "trial_period",
        "billing_cycle",
    ]
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def billing_cycle(self, obj=None):
        if obj and obj.data and obj.data.get("billing_cycle"):
            return f'{obj.data["billing_cycle"]["frequency"]} {obj.data["billing_cycle"]["interval"]}'
        return ""

    def description(self, obj=None):
        if obj and obj.data:
            return obj.data.get("description", "")

    def name(self, obj=None):
        if obj and obj.data:
            return obj.data.get("name", obj.id)
        if obj:
            return obj.id
        return ""

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")

    def trial_period(self, obj=None):
        if obj and obj.data and obj.data.get("trial_period"):
            return f'{obj.data["trial_period"]["frequency"]} {obj.data["trial_period"]["interval"]}'
        return ""

    def unit_price(self, obj=None):
        if obj and obj.data and obj.data.get("unit_price"):
            return f'{int(obj.data["unit_price"]["amount"]) / 100} {obj.data["unit_price"]["currency_code"]}'
        return ""


@admin.register(Discount)
class DiscountAdmin(ModelAdmin):
    list_display = [
        "discount_description",
        "amount",
        "applies_to",
        "status",
        "discount_code",
        "uses_left",
        "expires",
    ]
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def discount_description(self, obj=None):
        if obj and obj.data:
            return obj.data.get("description", obj.id)
        if obj:
            return obj.id
        return ""

    def amount(self, obj=None):
        if obj and obj.data:
            if obj.data.get("type") == "percentage":
                return f"{obj.data.get('amount', '')}%"
            return f'{obj.data.get("amount", "")} {obj.data.get("currency_code", "")}'
        return ""

    def applies_to(self, obj=None):
        if obj and obj.data:
            return obj.data.get("restrict_to", "")
        return ""

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""

    def discount_code(self, obj=None):
        if obj and obj.data:
            return obj.data.get("code", "")
        return ""

    def uses_left(self, obj=None):
        if obj and obj.data:
            return obj.data.get("usage_limit", "")
        return ""

    def expires(self, obj=None):
        if obj and obj.data:
            return obj.data.get("expires_at", "")
        return ""


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = [
        "customer_email",
        "name",
        "price",
        "next_payment",
        "status",
    ]
    inlines = (
        TransactionInline,
        ProductInline,
    )
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    exclude = ["products"]

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def customer_email(self, obj=None):
        if obj and obj.customer:
            return obj.customer.email
        if obj:
            return obj.id
        return ""

    def name(self, obj=None):
        if obj and obj.data:
            try:
                return ", ".join([item["price"]["name"] for item in obj.data["items"]])
            except Exception:
                return ""
        return ""

    def price(self, obj=None):
        if obj and obj.data:
            try:
                unit_price = [int(item["price"]["unit_price"]["amount"]) / 100 for item in obj.data["items"]]
                frequency = [item["price"]["billing_cycle"] for item in obj.data["items"]]
                return ", ".join(
                    [
                        f"{unit_price[i]}/{frequency[i]['frequency']} {frequency[i]['interval']}"
                        for i in range(len(unit_price))
                    ]
                )
            except Exception:
                return ""
        return ""

    def next_payment(self, obj=None):
        if obj and obj.data:
            try:
                return obj.data["next_billed_at"]
            except Exception:
                return ""
        return ""


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = [
        "email",
        "name",
        "status",
        "created_at",
    ]
    inlines = (
        AddressInline,
        BusinessInline,
        SubscriptionInline,
        TransactionInline,
    )
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ["customer_email", "payment_amount", "payment_method", "date_paid", "products", "status"]
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def customer_email(self, obj=None):
        if obj and obj.customer:
            return obj.customer.email
        if obj:
            return obj.id
        return ""

    def payment_amount(self, obj=None):
        if obj and obj.data:
            try:
                return int(obj.data["details"]["totals"]["total"]) / 100
            except Exception:
                return ""
        return ""

    def payment_method(self, obj=None):
        if obj and obj.data:
            try:
                return (
                    f'{obj.data["payments"][0]["method_details"]["card"]["type"]} '
                    f'{obj.data["payments"][0]["method_details"]["card"]["last4"]}'
                )
            except Exception:
                return ""
        return ""

    def date_paid(self, obj=None):
        if obj and obj.data:
            try:
                return obj.data["payments"][0]["captured_at"]
            except Exception:
                return ""
        return ""

    def products(self, obj=None):
        if obj and obj.data:
            items = obj.data.get("items", [])
            # return items
            products = Product.objects.filter(id__in=[item["price"]["product_id"] for item in items])
            return ", ".join([product.name for product in products])
        return ""

    products.short_description = "Product(s)"

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""

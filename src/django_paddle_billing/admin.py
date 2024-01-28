import typing

from django.conf import settings
from django.contrib import admin
from django.db import models

from django_paddle_billing import settings as app_settings
from django_paddle_billing.models import Address, Business, Customer, Price, Product, Subscription, Transaction

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
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return app_settings.ADMIN_READONLY


@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    search_fields = ["id", "name"]
    inlines = (PriceInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Price)
class PriceAdmin(ModelAdmin):
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
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


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
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


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

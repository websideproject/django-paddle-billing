from ninja import ModelSchema, Schema

from django_paddle_billing.models import Product, Subscription


class SubscriptionSchema(ModelSchema):
    class Meta:
        model = Subscription
        fields = "__all__"
        # exclude = ("id",)


class ProductSchema(ModelSchema):
    # subscriptions: list[SubscriptionSchema] = []

    class Meta:
        model = Product
        fields = "__all__"
        # exclude = ("id",)


class ProductSubscriptionSchema(Schema):
    products: list[ProductSchema] = []
    subscriptions: list[SubscriptionSchema] = []

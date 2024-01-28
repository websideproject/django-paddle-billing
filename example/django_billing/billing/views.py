from ninja.router import Router

from django_paddle_billing.models import Product, Subscription

from .schema import ProductSubscriptionSchema

router = Router()


@router.get("/products", response=ProductSubscriptionSchema)
def products(request):
    products = Product.objects.values("id", "name", "created_at", "updated_at", "status")
    subscriptions = Subscription.objects.filter(account_id=1).prefetch_related("products").all()
    result = {"products": list(products), "subscriptions": list(subscriptions)}

    return result

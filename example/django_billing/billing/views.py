from ninja.router import Router

from django_paddle_billing.models import Product, Customer

from .schema import ProductSubscriptionSchema

router = Router()


@router.get("/products", response=ProductSubscriptionSchema)
def products(request):
    products = Product.objects.values("id", "name", "created_at", "updated_at", "status")
    subscriptions = Customer.objects.first().subscriptions.prefetch_related("products").all()
    result = {"products": list(products), "subscriptions": list(subscriptions)}

    return result

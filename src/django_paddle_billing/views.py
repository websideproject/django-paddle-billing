import json
import typing

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from paddle_billing_client.helpers import validate_webhook_signature
from paddle_billing_client.models.notification import NotificationPayload

from django_paddle_billing import settings as app_settings
from django_paddle_billing import signals


@method_decorator(csrf_exempt, name="dispatch")
class PaddleWebhookView(View):
    SUPPORTED_WEBHOOKS: typing.ClassVar = {
        # Address Alerts
        "address.created": signals.address_created,
        "address.updated": signals.address_updated,
        "address.imported": signals.address_imported,
        # Adjustment Alerts
        "adjustment.created": signals.adjustment_created,
        "adjustment.updated": signals.adjustment_updated,
        # Business Alerts
        "business.created": signals.business_created,
        "business.imported": signals.business_imported,
        "business.updated": signals.business_updated,
        # Customer Alerts
        "customer.created": signals.customer_created,
        "customer.imported": signals.customer_imported,
        "customer.updated": signals.customer_updated,
        # Discount Alerts
        "discount.created": signals.discount_created,
        "discount.imported": signals.discount_imported,
        "discount.updated": signals.discount_updated,
        # Payout Alerts  # Payment by Paddle for me (Company)
        "payout.created": signals.payout_created,
        "payout.paid": signals.payout_paid,
        # Price Alerts
        "price.created": signals.price_created,
        "price.imported": signals.price_imported,
        "price.updated": signals.price_updated,
        # Product Alerts
        "product.created": signals.product_created,
        "product.imported": signals.product_imported,
        "product.updated": signals.product_updated,
        # Report Alerts
        "report.created": signals.report_created,
        "report.updated": signals.report_updated,
        # Subscription Alerts
        "subscription.activated": signals.subscription_activated,
        "subscription.canceled": signals.subscription_canceled,
        "subscription.created": signals.subscription_created,
        "subscription.imported": signals.subscription_imported,
        "subscription.past_due": signals.subscription_past_due,
        "subscription.paused": signals.subscription_paused,
        "subscription.resumed": signals.subscription_resumed,
        "subscription.trialing": signals.subscription_trialing,
        "subscription.updated": signals.subscription_updated,
        # Transaction Alerts
        "transaction.billed": signals.transaction_billed,
        "transaction.cancelled": signals.transaction_cancelled,
        "transaction.completed": signals.transaction_completed,
        "transaction.created": signals.transaction_created,
        "transaction.paid": signals.transaction_paid,
        "transaction.past_due": signals.transaction_past_due,
        "transaction.payment_failed": signals.transaction_payment_failed,
        "transaction.ready": signals.transaction_ready,
        "transaction.updated": signals.transaction_updated,
    }

    def post(self, request, *args, **kwargs):
        """
        handle paddle webhook requests by
        - validating the payload signature
        - sending a django signal for each of the SUPPORTED_WEBHOOKS
        """
        payload = request.body.decode("utf-8")
        paddle_ip = request.META.get(app_settings.PADDLE_IP_REQUEST_HEADER, "").split(", ")[0]
        if app_settings.PADDLE_SANDBOX and paddle_ip not in app_settings.PADDLE_SANDBOX_IPS:
            return HttpResponseBadRequest("IP not allowed")
        elif not app_settings.PADDLE_SANDBOX and paddle_ip not in app_settings.PADDLE_IPS:
            return HttpResponseBadRequest("IP not allowed")

        is_valid = validate_webhook_signature(
            request.META.get("HTTP_PADDLE_SIGNATURE", ""), request.body, app_settings.PADDLE_SECRET_KEY
        )

        if not is_valid:
            return HttpResponseBadRequest("Invalid signature")
        notification = NotificationPayload.model_validate(json.loads(payload))

        if not notification.event_type:
            return HttpResponseBadRequest("'event_type' missing")

        if notification.event_type in self.SUPPORTED_WEBHOOKS.keys():
            signal = self.SUPPORTED_WEBHOOKS.get(notification.event_type)
            if signal:  # pragma: no cover
                signal.send(sender=self.__class__, payload=notification.data, occurred_at=notification.occurred_at)

        return HttpResponse()


paddle_webhook_view = PaddleWebhookView.as_view()

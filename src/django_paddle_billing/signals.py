import django.dispatch

# Address Alerts
address_created = django.dispatch.Signal()
address_imported = django.dispatch.Signal()
address_updated = django.dispatch.Signal()

# Adjustment Alerts
adjustment_created = django.dispatch.Signal()
adjustment_updated = django.dispatch.Signal()

# Business Alerts
business_created = django.dispatch.Signal()
business_imported = django.dispatch.Signal()
business_updated = django.dispatch.Signal()

# Customer Alerts
customer_created = django.dispatch.Signal()
customer_imported = django.dispatch.Signal()
customer_updated = django.dispatch.Signal()

# Discount Alerts
discount_created = django.dispatch.Signal()
discount_imported = django.dispatch.Signal()
discount_updated = django.dispatch.Signal()

# Payout Alerts  # Payment by Paddle for me (Company)
payout_created = django.dispatch.Signal()
payout_paid = django.dispatch.Signal()

# Price Alerts
price_created = django.dispatch.Signal()
price_imported = django.dispatch.Signal()
price_updated = django.dispatch.Signal()

# Product Alerts
product_created = django.dispatch.Signal()
product_imported = django.dispatch.Signal()
product_updated = django.dispatch.Signal()

# Report Alerts
report_created = django.dispatch.Signal()
report_updated = django.dispatch.Signal()

# Subscription Alerts
subscription_activated = django.dispatch.Signal()
subscription_canceled = django.dispatch.Signal()
subscription_created = django.dispatch.Signal()
subscription_imported = django.dispatch.Signal()
subscription_past_due = django.dispatch.Signal()
subscription_paused = django.dispatch.Signal()
subscription_resumed = django.dispatch.Signal()
subscription_trialing = django.dispatch.Signal()
subscription_updated = django.dispatch.Signal()

# Transaction Alerts
transaction_billed = django.dispatch.Signal()
transaction_cancelled = django.dispatch.Signal()
transaction_completed = django.dispatch.Signal()
transaction_created = django.dispatch.Signal()
transaction_paid = django.dispatch.Signal()
transaction_past_due = django.dispatch.Signal()
transaction_payment_failed = django.dispatch.Signal()
transaction_ready = django.dispatch.Signal()
transaction_updated = django.dispatch.Signal()

from django.contrib import admin

# Register your models here.
from billing.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    pass

from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'email', 'amount', 'currency', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'currency', 'created_at')
    search_fields = ('transaction_id', 'email', 'user_uid', 'phone_number')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'status', 'payment_method', 'created_at', 'updated_at')
        }),
        ('User Info', {
            'fields': ('user_uid', 'email', 'name', 'phone_number')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'purpose')
        }),
        ('Provider Details', {
            'fields': ('mpesa_checkout_request_id', 'mpesa_receipt', 'flutterwave_flw_ref', 'failure_reason')
        }),
    )

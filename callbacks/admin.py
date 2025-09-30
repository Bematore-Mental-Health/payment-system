from django.contrib import admin
from .models import CallbackLog


@admin.register(CallbackLog)
class CallbackLogAdmin(admin.ModelAdmin):
    list_display = ('provider', 'transaction_id', 'processed', 'created_at')
    list_filter = ('provider', 'processed', 'created_at')
    search_fields = ('transaction_id',)
    readonly_fields = ('created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('provider', 'transaction_id', 'raw_data')
        return self.readonly_fields

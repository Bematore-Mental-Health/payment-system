from django.contrib import admin
from .models import SyncLog


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('sync_type', 'transaction_id', 'user_uid', 'success', 'created_at')
    list_filter = ('sync_type', 'success', 'created_at')
    search_fields = ('transaction_id', 'user_uid')
    readonly_fields = ('created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('sync_type', 'transaction_id', 'user_uid', 'data_synced')
        return self.readonly_fields

from django.contrib import admin
from .models import FirebaseUser


@admin.register(FirebaseUser)
class FirebaseUserAdmin(admin.ModelAdmin):
    list_display = ('uid', 'email', 'display_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'display_name', 'uid')
    readonly_fields = ('uid', 'created_at', 'updated_at')

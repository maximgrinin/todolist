from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from core.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    readonly_fields = ('last_login', 'date_joined')
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined',
                           'last_login')}),
    )


admin.site.unregister(Group)

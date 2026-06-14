from django.contrib import admin
from users.models import CustomUser, UserHistory


# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'second_last_name',
        'email', 'departament', 'is_superuser', 'username', 'group',
    )
    exclude = 'user_permissions',
    ordering = ('-id',)
    fields = (
        'username', 'password', 'first_name', 'last_name', 'second_last_name',
        'email', 'departament', 'groups', 'is_superuser', 'is_staff', 'is_active',
    )

    def group(self, obj):
        return obj.groups.first()

    group.short_description = 'Group'


@admin.register(UserHistory)
class UserHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'action', 'model', 'object_id', 'change', 'ip_address', 'user_agent')
    search_fields = ['users', 'model', 'timestamp', ]
    readonly_fields = ('id', 'timestamp', 'user', 'action', 'model', 'object_id', 'change', 'ip_address', 'user_agent')
    ordering = ('-timestamp',)

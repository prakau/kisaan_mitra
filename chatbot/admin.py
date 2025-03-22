from django.contrib import admin
from .models import ChatHistory

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'language', 'created_at']
    list_filter = ['language', 'created_at', 'user']
    search_fields = ['message', 'response', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

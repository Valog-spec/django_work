from django.contrib import admin

from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "created_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["name", "user__telegram_id"]
    readonly_fields = ["created_at"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at", "due_date", "is_completed"]
    list_filter = ["is_completed", "created_at", "due_date", "categories", "user"]
    search_fields = ["title", "description", "user__telegram_id"]
    readonly_fields = ["created_at"]
    filter_horizontal = ["categories"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("categories")

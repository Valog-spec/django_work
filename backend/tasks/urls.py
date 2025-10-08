from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import CategoryViewSet, TaskViewSet, send_telegram_message

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"categories", CategoryViewSet, basename="category")

urlpatterns = [
    path("", include(router.urls)),
    path("send-telegram-message/", send_telegram_message, name="send-telegram-message"),
    path("bot/token/", views.BotTokenView.as_view(), name="bot-token"),
    path(
        "bot/register-user/",
        views.RegisterTelegramUserView.as_view(),
        name="register-telegram-user",
    ),
]

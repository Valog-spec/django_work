import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BotProfile, Category, Task
from .serializers import CategorySerializer, TaskSerializer
from .services.jwt_service import BotJWTService

logger = logging.getLogger(__name__)
User = get_user_model()


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с категориями"""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение queryset категорий с фильтрацией по telegram_user_id"""
        if self.action == "list":
            telegram_user_id = self.request.query_params.get("telegram_user_id")
            if telegram_user_id:
                return Category.objects.filter(
                    user=self.request.user, telegram_user_id=telegram_user_id
                )

        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Сохранение категории с привязкой к пользователю"""
        serializer.save(user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с задачами"""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получение queryset задач с фильтрацией для бота и по статусу"""
        queryset = Task.objects.filter(user=self.request.user)

        if self.request.user.username == "telegram_bot_user":
            telegram_user_id = self.request.query_params.get("telegram_user_id")
            if telegram_user_id:
                return Task.objects.filter(
                    user=self.request.user, telegram_user_id=telegram_user_id
                ).order_by("-created_at")
            return Task.objects.filter(user=self.request.user).order_by("-created_at")

        is_completed = self.request.query_params.get("is_completed")
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == "true")

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        """Сохранение задачи с привязкой к пользователю"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle_complete(self, request, pk=None):
        """Переключение статуса выполнения задачи"""
        task = self.get_object()
        task.is_completed = not task.is_completed
        task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def send_telegram_message(request):
    """Отправка сообщения через Telegram бота"""
    try:
        telegram_id = request.data.get("telegram_id")
        message = request.data.get("message")

        if not telegram_id or not message:
            return Response({"error": "telegram_id и message обязательны"}, status=400)

        bot_api_url = getattr(settings, "BOT_API_URL", "http://bot:8001/send_message")

        response = requests.post(
            bot_api_url,
            json={"telegram_id": int(telegram_id), "message": message},
            timeout=10,
        )

        if response.status_code == 200:
            return Response(
                {"status": "success", "message": "Уведомление отправлено успешно"}
            )
        else:
            return Response(
                {"error": f"Ошибка Bot API: {response.status_code}"}, status=500
            )
    except requests.exceptions.Timeout:
        logger.error("Таймаут подключения к Bot API")
        return Response({"error": "Таймаут сервиса бота"}, status=504)
    except Exception as e:
        logger.error(f"Ошибка в send_telegram_message: {e}")
        return Response({"error": "Внутренняя ошибка сервера"}, status=500)


class BotTokenView(APIView):
    """Получение JWT токенов для бота"""

    permission_classes = [AllowAny]

    def get(self, request):
        tokens = BotJWTService.create_bot_tokens()
        return Response(tokens)


class RegisterTelegramUserView(APIView):
    """Регистрация Telegram пользователя"""

    permission_classes = [AllowAny]

    def post(self, request):
        # Проверяем, что запрос от системного пользователя бота
        if request.user.username != "telegram_bot_user":
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        telegram_user_id = request.data.get("telegram_user_id")
        chat_id = request.data.get("chat_id")

        if not telegram_user_id or not chat_id:
            return Response(
                {"error": "telegram_user_id and chat_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаем или обновляем профиль
        bot_profile, created = BotProfile.objects.update_or_create(
            telegram_user_id=telegram_user_id,
            defaults={
                "user": request.user,
                "chat_id": chat_id,
                "first_name": request.data.get("first_name"),
                "last_name": request.data.get("last_name"),
                "username": request.data.get("username"),
            },
        )

        return Response(
            {
                "status": "created" if created else "updated",
                "telegram_user_id": bot_profile.telegram_user_id,
                "chat_id": bot_profile.chat_id,
            }
        )

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class BotJWTService:
    @staticmethod
    def get_bot_user():
        """Получаем системного пользователя бота"""
        try:
            return User.objects.get(username="telegram_bot_user")
        except User.DoesNotExist:
            bot_user = User.objects.create(
                username="telegram_bot_user",
                email="bot@example.com",
                is_active=True,
                is_staff=False,
            )
            bot_user.set_unusable_password()
            bot_user.save()
            return bot_user

    @staticmethod
    def create_bot_tokens():
        """Создаем JWT токены для системного пользователя бота"""
        bot_user = BotJWTService.get_bot_user()
        refresh = RefreshToken.for_user(bot_user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

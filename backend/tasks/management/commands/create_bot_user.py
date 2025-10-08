from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = "Create system bot user"

    def handle(self, *args, **options):
        # Создаем или получаем системного пользователя для бота
        bot_user, created = User.objects.get_or_create(
            username="telegram_bot_user",
            defaults={
                "email": "bot@example.com",
                "is_active": True,
                "is_staff": False,
            },
        )
        if created:
            bot_user.set_unusable_password()  # Пароль не нужен, т.к. авторизация по JWT
            bot_user.save()
            self.stdout.write(
                self.style.SUCCESS("Successfully created bot system user")
            )
        else:
            self.stdout.write(self.style.WARNING("Bot system user already exists"))

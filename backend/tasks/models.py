import datetime
import hashlib

from django.conf import settings
from django.db import models


def generate_id(prefix: str, *args) -> str:
    """Генерация уникального ID на основе префикса и аргументов"""
    date_part = datetime.date.today().strftime("%Y%m%d")
    base = "_".join(map(str, args))
    hash_part = hashlib.sha1(base.encode()).hexdigest()[:6]
    return f"{prefix}_{date_part}_{hash_part}"


class Category(models.Model):
    """Модель категории задач"""

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    name = models.CharField(max_length=100, verbose_name="Название категории")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Пользователь",
    )
    telegram_user_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, verbose_name="Telegram пользователь"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def save(self, *args, **kwargs):
        """Сохранение категории с генерацией ID"""
        if not self.id:
            self.id = generate_id("cat", self.telegram_user_id, self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Категория"
        unique_together = ["name", "user"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    """Модель задачи"""

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    title = models.CharField(max_length=200, verbose_name="Заголовок задачи")
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание задачи"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    due_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Срок выполнения"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Выполнена")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Пользователь",
    )
    categories = models.ManyToManyField(
        Category, related_name="tasks", blank=True, verbose_name="Категории"
    )

    notification_sent = models.BooleanField(
        default=False, verbose_name="Уведомление отправлено"
    )
    telegram_user_id = models.BigIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """Сохранение задачи с генерацией ID"""
        if not self.id:
            # включаем timestamp, чтобы ID не повторялись, если названия одинаковые
            timestamp = self.created_at or datetime.datetime.now()
            self.id = generate_id(
                "task", self.telegram_user_id, self.title, timestamp.isoformat()
            )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Задача"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["is_completed"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return self.title


from django.conf import settings
from django.db import models


class BotProfile(models.Model):
    """Модель профиля Telegram бота"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bot_profiles"
    )
    telegram_user_id = models.BigIntegerField(unique=True)
    chat_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"tg_user={self.telegram_user_id}"

    class Meta:
        indexes = [
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["chat_id"]),
        ]

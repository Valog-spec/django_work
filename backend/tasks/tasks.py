import logging

import requests
from celery import shared_task
from django.utils import timezone

from .models import Task

logger = logging.getLogger(__name__)


@shared_task
def send_due_task_notifications() -> None:
    """Фоновая задача для отправки уведомлений о просроченных задачах"""
    try:

        now = timezone.now()

        due_tasks = (
            Task.objects.filter(
                due_date__lte=now, is_completed=False, notification_sent=False,
                telegram_user_id__isnull=False
            )
            .prefetch_related("categories")
        )

        logger.info(f"Найдено {due_tasks.count()} просроченных задач для уведомления")

        notification_count = 0
        for task in due_tasks:
            try:
                message = format_task_notification(task)

                success = send_telegram_notification(
                    task.telegram_user_id, message
                )

                if success:
                    task.notification_sent = True
                    task.save()

                    notification_count += 1
                    logger.info(
                        f"Уведомление отправлено для задачи {task.id} пользователю {task.telegram_user_id}"
                    )
                else:
                    logger.error(
                        f"Не удалось отправить уведомление для задачи {task.id}"
                    )

            except Exception as e:
                logger.error(f"Ошибка обработки задачи {task.id}: {e}")

        logger.info(f"Успешно отправлено {notification_count} уведомлений")

    except Exception as e:
        logger.error(f"Ошибка в send_due_task_notifications: {e}")


def send_telegram_notification(telegram_id: int, message: str) -> bool:
    """Отправка уведомления через Telegram API"""
    try:
        api_url = f"http://backend:8000/api/send-telegram-message/"

        response = requests.post(
            api_url, json={"telegram_id": telegram_id, "message": message}, timeout=10
        )

        return response.status_code == 200

    except Exception as e:
        logger.error(f"Ошибка при отправке Telegram уведомления: {e}")
        return False


def format_task_notification(task) -> str:
    """Форматирование сообщения уведомления о задаче"""
    categories = ", ".join([cat.name for cat in task.categories.all()])
    categories_text = f"🏷️ {categories}" if categories else ""

    message = (
        f"⏰ Напоминание о задаче\n\n"
        f"📝 {task.title}\n"
        f"📅 Срок: {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"{categories_text}\n"
        f"\nЗадача просрочена! ⚠️"
    )

    return message

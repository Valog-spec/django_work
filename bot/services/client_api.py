import logging
from typing import List, Optional

import httpx

from config.settings import settings
from models.schemas import (
    Category,
    CreateCategoryRequest,
    CreateTaskRequest,
    Task,
    UpdateTaskRequest,
)

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.timeout = settings.API_TIMEOUT
        self.access_token = None
        self.bot_user_id = "telegram_bot_user"  # системный пользователь

    async def _ensure_authenticated(self) -> bool:
        """Обеспечивает аутентификацию бота"""
        if self.access_token:
            return True
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/bot/token/")
                if response.status_code == 200:
                    tokens = response.json()
                    self.access_token = tokens["access"]
                    logger.info("Бот успешно аутентифицирован")
                    return True
                else:
                    logger.error(f"Ошибка аутентификации бота: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Ошибка при аутентификации бота: {e}")
            return False

    def _get_headers(self) -> dict:
        """Возвращает заголовки с JWT токеном"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def register_telegram_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> bool:
        """Регистрация Telegram пользователя в системе"""
        print('hello')
        if not await self._ensure_authenticated():
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/bot/register-user/",
                    headers=self._get_headers(),
                    json={
                        "telegram_user_id": telegram_id,
                        "chat_id": telegram_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"Telegram пользователь зарегистрирован: {data}")
                    return True
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка регистрации Telegram пользователя: {response.status_code} - {error_text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error("Таймаут при регистрации Telegram пользователя")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при регистрации: {e}")
            return False

    async def get_tasks(
        self, telegram_id: int, completed: Optional[bool] = None
    ) -> List[Task]:
        """Получение задач для конкретного Telegram пользователя"""
        if not await self._ensure_authenticated():
            return []

        try:
            params = {"telegram_user_id": str(telegram_id)}
            if completed is not None:
                params["completed"] = str(completed).lower()

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/tasks/",
                    headers=self._get_headers(),
                    params=params,
                )
                if response.status_code == 200:
                    data = response.json()
                    tasks_data = data.get("results", [])
                    tasks = [Task(**task) for task in tasks_data]
                    logger.info(
                        f"Получено {len(tasks)} задач для Telegram пользователя {telegram_id}"
                    )
                    return tasks
                elif response.status_code == 404:
                    logger.warning(f"Telegram пользователь {telegram_id} не найден")
                    return []
                else:
                    logger.error(
                        f"Ошибка получения задач: статус {response.status_code}"
                    )
                    return []

        except httpx.TimeoutException:
            logger.error(f"Таймаут при получении задач для пользователя {telegram_id}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении задач: {e}")
            return []

    async def get_task_detail(self, telegram_id: int, task_id: str) -> Optional[Task]:
        """Получение деталей конкретной задачи"""
        if not await self._ensure_authenticated():
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/tasks/{task_id}/",
                    headers=self._get_headers(),
                    params={"telegram_user_id": telegram_id},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Получены детали задачи: {data.get('title')}")
                    return Task(**data)
                else:
                    logger.error(f"Ошибка получения задачи: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении задачи: {e}")
            return None

    async def update_task(
        self, telegram_id: int, task_id: str, task_data: UpdateTaskRequest
    ) -> bool:
        """Обновление задачи"""
        if not await self._ensure_authenticated():
            return False

        try:
            # Преобразуем данные задачи для API
            api_task_data = {
                "telegram_user_id": telegram_id,
                "title": task_data.title,
                "description": task_data.description,
                "due_date": (
                    task_data.due_date.isoformat() if task_data.due_date else None
                ),
                "category_ids": task_data.category_ids or [],
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/api/tasks/{task_id}/",
                    headers=self._get_headers(),
                    json=api_task_data,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Задача обновлена: {data.get('title')}")
                    return True
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка обновления задачи: {response.status_code} - {error_text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении задачи: {e}")
            return False

    async def get_categories(self, telegram_id: int) -> List[Category]:
        """Получение категорий (теперь через системного пользователя)"""
        if not await self._ensure_authenticated():
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/categories/",
                    headers=self._get_headers(),
                    params={"telegram_user_id": str(telegram_id)},
                )
                if response.status_code == 200:
                    data = response.json()
                    categories_data = data.get("results", data)
                    categories = [Category(**category) for category in categories_data]
                    logger.info(f"Получено {len(categories)} категорий")
                    return categories
                else:
                    logger.error(
                        f"Ошибка получения категорий: статус {response.status_code}"
                    )
                    return []

        except httpx.TimeoutException:
            logger.error("Таймаут при получении категорий")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении категорий: {e}")
            return []

    async def get_category_detail(
        self, telegram_id: int, category_id: str
    ) -> Optional[Category]:
        """Получение деталей конкретной задачи"""
        if not await self._ensure_authenticated():
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/categories/{category_id}/",
                    headers=self._get_headers(),
                    params={"telegram_user_id": telegram_id},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Получены детали категории: {data.get('title')}")
                    return Category(**data)
                else:
                    logger.error(f"Ошибка получения категории: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении категории: {e}")
            return None

    async def update_category(
        self, telegram_id: int, category_id: str, category_data: CreateCategoryRequest
    ) -> bool:
        """Обновление категории"""
        if not await self._ensure_authenticated():
            return False
        try:
            api_task_data = {
                "telegram_user_id": telegram_id,
                "name": category_data.name,
            }
            # api_data = category_data.model_dump()
            # api_data['telegram_user_id'] = telegram_id

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/api/categories/{category_id}/",
                    headers=self._get_headers(),
                    json=api_task_data,
                )
                if response.status_code == 200:
                    logger.info(f"Категория обновлена: {category_data.name}")
                    return True
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка обновления категории: {response.status_code} - {error_text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Неожиданная ошибка при обновлении категории: {e}")
            return False

    async def delete_category(self, telegram_id: int, category_id: str) -> bool:
        """Удаление категории"""
        if not await self._ensure_authenticated():
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/categories/{category_id}/",
                    headers=self._get_headers(),
                    params={"telegram_user_id": telegram_id},
                )

                if response.status_code == 204:
                    logger.info(f"Категория {category_id} удалена")
                    return True
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка удаления категории: {response.status_code} - {error_text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении категории: {e}")
            return False

    async def create_task(self, telegram_id: int, task_data: CreateTaskRequest) -> bool:
        """Создание задачи для конкретного Telegram пользователя"""
        if not await self._ensure_authenticated():
            return False

        try:
            # Преобразуем данные задачи для API
            api_task_data = {
                "telegram_user_id": telegram_id,
                "title": task_data.title,
                "description": task_data.description,
                "due_date": (
                    task_data.due_date.isoformat() if task_data.due_date else None
                ),
                "category_ids": task_data.category_ids or [],
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/tasks/",
                    headers=self._get_headers(),
                    json=api_task_data,
                )

                if response.status_code == 201:
                    data = response.json()
                    logger.info(
                        f"Задача создана: {data.get('title')} (ID: {data.get('task_id')})"
                    )
                    # Создаем объект Task из ответа
                    return True
                elif response.status_code == 404:
                    logger.error(f"Telegram пользователь {telegram_id} не найден")
                    return False
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка создания задачи: статус {response.status_code} - {error_text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Таймаут при создании задачи для пользователя {telegram_id}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании задачи: {e}")
            return False

    async def create_category(
        self, telegram_id: int, category_data: CreateCategoryRequest
    ) -> Optional[Category]:
        """Создание категории через системного пользователя"""
        if not await self._ensure_authenticated():
            return None
        try:
            api_data = category_data.model_dump()
            api_data["telegram_user_id"] = telegram_id
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/categories/",
                    headers=self._get_headers(),
                    json=api_data,
                )

                if response.status_code == 201:
                    data = response.json()
                    logger.info(f"Категория создана: {data.get('name')}")
                    return Category(**data)
                else:
                    error_text = response.text
                    logger.error(
                        f"Ошибка создания категории: статус {response.status_code} - {error_text}"
                    )
                    return None

        except httpx.TimeoutException:
            logger.error("Таймаут при создании категории")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании категории: {e}")
            return None

    async def toggle_task_completion(
        self, telegram_id: int, task_id: str
    ) -> Optional[Task]:
        """Переключение статуса выполнения задачи"""
        if not await self._ensure_authenticated():
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/tasks/{task_id}/toggle_complete/",
                    headers=self._get_headers(),
                    json={"telegram_user_id": telegram_id},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Статус задачи обновлен: {data.get('title')}")
                    return Task(**data)
                elif response.status_code == 404:
                    logger.error(
                        f"Задача {task_id} не найдена для пользователя {telegram_id}"
                    )
                    return None
                else:
                    logger.error(f"Ошибка переключения задачи: {response.status_code}")
                    return None

        except httpx.TimeoutException:
            logger.error("Таймаут при переключении статуса задачи")
            return None
        except Exception as e:
            logger.error(f"Исключение в toggle_task_completion: {e}")
            return None

    async def delete_task(self, telegram_id: int, task_id: str) -> bool:
        """Удаление задачи"""
        if not await self._ensure_authenticated():
            return False
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/tasks/{task_id}/",
                    headers=self._get_headers(),
                )

                if response.status_code == 204:
                    logger.info(f"Задача {task_id} удалена")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"Задача {task_id} не найдена")
                    return False
                else:
                    logger.error(f"Ошибка удаления задачи: {response.status_code}")
                    return False

        except httpx.TimeoutException:
            logger.error("Таймаут при удалении задачи")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи: {e}")
            return False

from rest_framework import serializers

from .models import BotProfile, Category, Task


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""

    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "telegram_user_id"]
        read_only_fields = ["id", "created_at"]

    def update(self, instance, validated_data):
        """Обновление категории"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""

    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "due_date",
            "is_completed",
            "user",
            "categories",
            "category_ids",
            "telegram_user_id",
        ]

        read_only_fields = ["id", "created_at", "user"]

    def create(self, validated_data):
        """Создание задачи с привязкой категорий"""
        category_ids = validated_data.pop("category_ids", [])
        task = Task.objects.create(**validated_data)

        if category_ids:
            categories = Category.objects.filter(
                id__in=category_ids, user=validated_data["user"]
            )
            task.categories.set(categories)

        return task

    def update(self, instance, validated_data):
        """Обработка обновления задачи"""
        category_ids = validated_data.pop("category_ids", None)
        telegram_user_id = validated_data.pop("telegram_user_id", None)

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Обновляем telegram_user_id если передан
        if telegram_user_id is not None:
            instance.telegram_user_id = telegram_user_id

        instance.save()

        # Обновляем категории если переданы
        if category_ids is not None:
            categories = Category.objects.filter(
                id__in=category_ids, user=instance.user
            )
            instance.categories.set(categories)

        return instance


class BotProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля бота"""

    class Meta:
        model = BotProfile
        fields = [
            "id",
            "telegram_user_id",
            "chat_id",
            "first_name",
            "last_name",
            "username",
            "created_at",
            "last_activity",
        ]
        read_only_fields = ["id", "created_at", "last_activity"]

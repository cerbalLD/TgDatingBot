from datetime import datetime
from pathlib import Path
import shutil

import sys

sys.path.append(".")

from store import Store
from store.elastic.indexer import index_profile


def seed() -> None:
    base_image = Path("assets/downloads/test_image.png")
    base_image.parent.mkdir(parents=True, exist_ok=True)
    if not base_image.exists():
        raise RuntimeError("test_image.png not found")

    profiles = [
        (100000001, "Анна", 15, "Ростов-на-Дону"),
        (100000002, "Мария", 16, "Ростов-на-Дону"),
        (100000003, "Екатерина", 18, "Ростов-на-Дону"),
        (100000004, "Ольга", 20, "Ростов-на-Дону"),
        (100000005, "София", 22, "Ростов-на-Дону"),
        (100000006, "Дарья", 19, "Таганрог"),
        (100000007, "Полина", 24, "Москва"),
        (100000008, "Алиса", 27, "Сочи"),
        (100000009, "Виктория", 21, "Казань"),
        (100000010, "Наталья", 23, "Минск"),
    ]

    for user_id, name, age, city in profiles:
        existing = Store.user.get_by_user_id(user_id)
        if existing:
            Store.user.update(
                existing.id,
                name=name,
                age=age,
                city=city,
                sex=False,
                text="Тестовая анкета",
                is_approved=True,
                moderation_status="approved",
                is_enabled=True,
                is_anonymous=True,
                profile_version=(existing.profile_version or 1) + 1,
            )
            user = Store.user.get_by_user_id(user_id)
        else:
            Store.user.create(
                user_id=user_id,
                name=name,
                age=age,
                city=city,
                sex=False,
                text="Тестовая анкета",
                is_approved=True,
                moderation_status="approved",
                is_enabled=True,
                is_anonymous=True,
                profile_version=1,
                expire_subscription_date=datetime.utcnow(),
            )
            user = Store.user.get_by_user_id(user_id)

        media_name = f"{user_id}_test_image.png"
        media_path = Path("assets/downloads") / media_name
        if not media_path.exists():
            shutil.copyfile(base_image, media_path)

        existing_media = Store.media.list(user_id=user_id, limit=1)
        if not existing_media:
            Store.media.create(user_id=user_id, path=str(media_path))

        if user:
            index_profile(user)


if __name__ == "__main__":
    seed()

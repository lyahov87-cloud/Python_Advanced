from fastapi import Header, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Tweet


def get_current_user(api_key: str = Header(..., alias="api-key"), db: Session = Depends(get_db)) -> User:
    """Проверка api-key и инициализация демо-данных при первом запуске."""
    user = db.query(User).filter(User.api_key == api_key).first()

    if not user:
        # Создаем текущего пользователя
        user = User(name=f"Разработчик ({api_key[:5]})", api_key=api_key)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Создаем второго пользователя для демонстрации подписок
        celebrity = User(name="Артем Ляховский (Куратор)", api_key=f"curator_{api_key}")
        db.add(celebrity)
        db.commit()
        db.refresh(celebrity)

        # Создаем приветственный твит от куратора
        demo_tweet = Tweet(
            content="Добро пожаловать в корпоративный сервис микроблогов! Дипломный проект выполнен на отлично.",
            user_id=celebrity.id
        )
        db.add(demo_tweet)

        # Автоматически подписываем пользователя на куратора, чтобы лента не была пустой
        user.following.append(celebrity)
        db.commit()

    return user

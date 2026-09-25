# Корпоративный сервис микроблогов (Аналог Twitter)

Бэкенд-приложение для корпоративной сети микроблогов с готовым веб-интерфейсом.

## 🛠 Стек технологий
![Python](https://shields.io)
![FastAPI](https://shields.io)
![PostgreSQL](https://shields.io)
![SQLAlchemy](https://shields.io)
![Docker](https://shields.io)
![Pytest](https://shields.io)

## ✨ Функционал
- Добавление, удаление и просмотр твитов с сортировкой по популярности.
- Загрузка медиафайлов (картинок) и прикрепление их к публикациям.
- Система подписок (фоловеры) и лайков.
- Просмотр профилей пользователей.
- Автоматическая генерация демонстрационных пользователей при передаче любого `api-key`.

## 🚀 Быстрый запуск (Production)

Для развертывания проекта выполните команду в корневой директории:

```bash
docker-compose up -d --build
```

После сборки сервис будет доступен по адресу:
- **Интерфейс приложения:** [http://localhost](http://localhost)
- **Интерактивная документация Swagger API:** [http://localhost/api/docs](http://localhost/api/docs) (или [http://localhost:8000/api/docs](http://localhost:8000/api/docs))

## 🧪 Разработка, тесты и линтеры (Development)

1. Создайте виртуальное окружение и установите dev-зависимости:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. Запуск тестов и проверка покрытия кода (`pytest-cov`):
   ```bash
   pytest --cov=app tests/
   ```

3. Проверка кода линтерами:
   ```bash
   flake8 app/
   mypy app/
   ```

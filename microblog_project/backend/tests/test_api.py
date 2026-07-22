import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app, get_db
from app.models import Base
# Используем SQLite в памяти исключительно для быстрой прогонки unit-тестов
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="module")
def test_db():
    from sqlalchemy import create_engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_tweet(client) -> None:
    """Тест успешного создания твита."""
    headers = {"api-key": "test_token"}
    response = client.post(
        "/api/tweets",
        json={"tweet_data": "Hello World!", "tweet_media_ids": []},
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["result"] is True
    assert "tweet_id" in response.json()


def test_get_me_profile(client) -> None:
    """Тест получения информации о своем профиле."""
    headers = {"api-key": "test_token"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["result"] == "true"
    assert "user" in response.json()

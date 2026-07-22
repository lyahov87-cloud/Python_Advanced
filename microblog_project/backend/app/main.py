import os
import uuid
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db, engine
from .models import Base, Tweet, Media, User, likes
from .schemas import (
    TweetCreate, TweetCreateResponse, BaseResponse,
    MediaResponse, TweetListResponse, TweetSchema, AuthorSchema, LikeSchema,
    UserProfileResponse, UserProfileSchema, UserShortSchema, ErrorResponse
)
from .dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


app = FastAPI(title="Сервис Микроблогов API", docs_url="/api/docs", lifespan=lifespan)


# --- ОБРАБОТКА ОШИБОК ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error_type=f"HTTP_{exc.status_code}", error_message=exc.detail).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error_type="ValidationError", error_message=str(exc.errors())).model_dump()
    )


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error_type="ServerError", error_message=str(exc)).model_dump()
    )


# --- ЭНДПОИНТЫ ПРОФИЛЕЙ ---
@app.get("/api/users/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    user_data = UserProfileSchema(
        id=current_user.id, name=current_user.name,
        followers=[UserShortSchema(id=u.id, name=u.name) for u in current_user.followers_list],
        following=[UserShortSchema(id=u.id, name=u.name) for u in current_user.following]
    )
    return UserProfileResponse(user=user_data)


@app.get("/api/users/{id}", response_model=UserProfileResponse)
def get_user_profile(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> UserProfileResponse:
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user_data = UserProfileSchema(
        id=user.id, name=user.name,
        followers=[UserShortSchema(id=u.id, name=u.name) for u in user.followers_list],
        following=[UserShortSchema(id=u.id, name=u.name) for u in user.following]
    )
    return UserProfileResponse(user=user_data)


# --- ЭНДПОИНТЫ ТВИТОВ И МЕДИА ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "../media")
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../static"))
os.makedirs(MEDIA_DIR, exist_ok=True)


@app.post("/api/medias", response_model=MediaResponse, status_code=201)
def upload_media(
    file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MediaResponse:
    file_ext = os.path.splitext(file.filename or ".jpg")
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    with open(os.path.join(MEDIA_DIR, unique_filename), "wb") as buffer:
        buffer.write(file.file.read())
    db_media = Media(file_path=f"/media/{unique_filename}")
    db.add(db_media)
    db.commit()
    return MediaResponse(media_id=db_media.id)


@app.post("/api/tweets", response_model=TweetCreateResponse, status_code=201)
def create_tweet(
    tweet_in: TweetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TweetCreateResponse:
    new_tweet = Tweet(content=tweet_in.tweet_data, user_id=current_user.id)
    db.add(new_tweet)
    db.commit()
    if tweet_in.tweet_media_ids:
        db.query(Media).filter(Media.id.in_(tweet_in.tweet_media_ids)).update(
            {"tweet_id": new_tweet.id}, synchronize_session=False
        )
        db.commit()
    return TweetCreateResponse(tweet_id=new_tweet.id)


@app.delete("/api/tweets/{id}", response_model=BaseResponse)
def delete_tweet(id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)) -> BaseResponse:
    tweet = db.query(Tweet).filter(Tweet.id == id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")
    if tweet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нельзя удалить чужой твит")
    db.delete(tweet)
    db.commit()
    return BaseResponse()


@app.post("/api/tweets/{id}/likes", response_model=BaseResponse)
def like_tweet(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BaseResponse:
    tweet = db.query(Tweet).filter(Tweet.id == id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")
    if current_user not in tweet.liked_by:
        tweet.liked_by.append(current_user)
        db.commit()
    return BaseResponse()


@app.delete("/api/tweets/{id}/likes", response_model=BaseResponse)
def unlike_tweet(id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)) -> BaseResponse:
    tweet = db.query(Tweet).filter(Tweet.id == id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")
    if current_user in tweet.liked_by:
        tweet.liked_by.remove(current_user)
        db.commit()
    return BaseResponse()


@app.post("/api/users/{id}/follow", response_model=BaseResponse)
def follow_user(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BaseResponse:
    if current_user.id == id:
        raise HTTPException(status_code=400, detail="Нельзя подписаться на себя")
    user_to_follow = db.query(User).filter(User.id == id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user_to_follow not in current_user.following:
        current_user.following.append(user_to_follow)
        db.commit()
    return BaseResponse()


@app.delete("/api/users/{id}/follow", response_model=BaseResponse)
def unfollow_user(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> BaseResponse:
    user_to_unfollow = db.query(User).filter(User.id == id).first()
    if not user_to_unfollow:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user_to_unfollow in current_user.following:
        current_user.following.remove(user_to_unfollow)
        db.commit()
    return BaseResponse()


@app.get("/api/tweets", response_model=TweetListResponse)
def get_tweets_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TweetListResponse:
    following_ids = [u.id for u in current_user.following] + [current_user.id]
    tweets_list = (
        db.query(Tweet)
        .filter(Tweet.user_id.in_(following_ids))
        .outerjoin(likes)
        .group_by(Tweet.id)
        .order_by(func.count(likes.c.user_id).desc(), Tweet.created_at.desc())
        .all()
    )
    result_tweets = []
    for t in tweets_list:
        result_tweets.append(TweetSchema(
            id=t.id, content=t.content, attachments=[m.file_path for m in t.attachments],
            author=AuthorSchema(id=t.user.id, name=t.user.name),
            likes=[LikeSchema(user_id=u.id, name=u.name) for u in t.liked_by]
        ))
    return TweetListResponse(tweets=result_tweets)


app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def read_index() -> FileResponse:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

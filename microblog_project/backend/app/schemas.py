from pydantic import BaseModel
from typing import List, Optional


class BaseResponse(BaseModel):
    result: bool = True


class TweetCreate(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]] = []


class TweetCreateResponse(BaseResponse):
    tweet_id: int


class MediaResponse(BaseResponse):
    media_id: int


class AuthorSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LikeSchema(BaseModel):
    user_id: int
    name: str


class TweetSchema(BaseModel):
    id: int
    content: str
    attachments: List[str]
    author: AuthorSchema
    likes: List[LikeSchema]


class TweetListResponse(BaseResponse):
    tweets: List[TweetSchema]


class ProfileResponseBase(BaseModel):
    result: str = "true"


class UserShortSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserProfileSchema(BaseModel):
    id: int
    name: str
    followers: List[UserShortSchema]
    following: List[UserShortSchema]


class UserProfileResponse(ProfileResponseBase):
    user: UserProfileSchema


class ErrorResponse(BaseModel):
    result: bool = False
    error_type: str
    error_message: str

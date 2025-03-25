from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class InstagramUser(BaseModel):
    """Instagram user data model."""
    username: str
    full_name: Optional[str] = None
    user_id: str

class InstagramPost(BaseModel):
    """Instagram post data model."""
    post_id: str
    user: InstagramUser
    caption: Optional[str] = None
    likes_count: int
    timestamp: datetime
    media_type: str  # image, video, carousel
    media_urls: list[str]
    taken_at: datetime
    code: str  # Instagram's shortcode for the post

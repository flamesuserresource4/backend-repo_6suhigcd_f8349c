"""
Database Schemas for Ashen

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase class name.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class Link(BaseModel):
    label: str = Field(..., description="Link label shown on profile")
    url: HttpUrl
    icon: Optional[str] = Field(None, description="Optional icon name for UI")

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user"
    """
    username: str = Field(..., min_length=3, max_length=24, pattern=r"^[a-zA-Z0-9_]+$", description="Unique handle")
    display_name: str = Field(..., min_length=1, max_length=64)
    email: str = Field(..., description="Email address")
    bio: Optional[str] = Field(None, max_length=180)
    avatar_url: Optional[str] = Field(None, description="Optional avatar image URL")
    links: List[Link] = Field(default_factory=list)
    is_active: bool = True

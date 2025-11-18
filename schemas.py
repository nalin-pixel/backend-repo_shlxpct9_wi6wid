"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Class name lowercased becomes the collection name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """
    Users collection schema
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")
    password_salt: str = Field(..., description="Salt used for hashing")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    is_active: bool = Field(True, description="Whether user is active")

class Blogpost(BaseModel):
    """
    Blog posts
    Collection: "blogpost"
    """
    title: str = Field(..., description="Post title")
    slug: str = Field(..., description="URL slug")
    excerpt: Optional[str] = Field(None, description="Short summary")
    content: str = Field(..., description="Markdown/HTML content")
    author: Optional[str] = Field(None, description="Author name")
    tags: List[str] = Field(default_factory=list, description="Tags")
    published: bool = Field(True, description="Visibility flag")
    published_at: Optional[datetime] = Field(None, description="Publish date")

class Contactmessage(BaseModel):
    """
    Contact messages from the site
    Collection: "contactmessage"
    """
    name: str = Field(..., description="Sender name")
    email: EmailStr = Field(..., description="Sender email")
    subject: Optional[str] = Field(None, description="Subject")
    message: str = Field(..., description="Message body")

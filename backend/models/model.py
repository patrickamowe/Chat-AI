from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    username = Column(String(20), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    access_token = Column(String(100), nullable=True)
    refresh_token = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title}>"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # "user-username""
    user_prompt= Column(Text, nullable=False) # The actual message content
    AI_response = Column(Text, nullable=False) # The AI's response to the message
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} sender={self.sender}>"
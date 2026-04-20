import uuid
import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, func
from sqlalchemy. orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


# 1개의 conversation <-> N개의 Message가 대응하는 관계 : 일대다 관계
class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=uuid.uuid4,
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),

    )

class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversation.id")
    )

    role : Mapped[str] = mapped_column(String(10)) # user / assistant
    contenet : Mapped[str] = mapped_column(Text)

    created_at : Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),

    )


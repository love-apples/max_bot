from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Insert, Link, before_event
from beanie.operators import Set
from beanie.odm.actions import Save, Replace
from pydantic import Field, BaseModel
from pymongo import ASCENDING, DESCENDING, IndexModel

from bot.utils.bot import kick_user
from core.logger import db_logger
from core.bot import bot


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class BaseDocument(Document):
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    @before_event(Save)
    @before_event(Replace)
    async def update_updated_at(self) -> None:
        self.updated_at = now_utc()


class User(BaseDocument):
    user_id: int
    full_name: str
    is_bot: bool = False

    class Settings:
        name = 'users'
        
    @before_event(Insert)
    async def log_save_user(self):
        db_logger.info('Регистрация пользователя: full_name=%s, user_id=%s', self.full_name, self.user_id)
        
        
class ChatSettings(BaseModel):
    welcome_user_text: str = 'Привет, {name}! Ознакомься с правилами через /rules'
    buy_user_text: str = 'Прощай, {name}!'
    warns_limit: int = 3
    

class Chat(BaseDocument):
    chat_id: int
    title: Optional[str] = None
    settings: ChatSettings = ChatSettings()

    class Settings:
        name = 'chats'
        
    @before_event(Insert)
    async def log_save_chat(self):
        db_logger.info('Регистрация чата: title=%s, chat_id=%s', self.title, self.chat_id)
        
        
class Kick(BaseDocument):
    user: Link[User]
    chat: Link[Chat]
    admin: Optional[Link[User]] = None
    reason: Optional[str] = None

    class Settings:
        name = 'kicks'
        

class Warn(BaseDocument):
    user: Link[User]
    chat: Link[Chat]
    admin: Optional[Link[User]] = None
    reason: Optional[str] = None
    is_relevant: bool = True
    
    class Settings:
        name = 'warns'
        indexes = [['user', 'chat']]
    
    @before_event(Insert)
    async def check_warns(self):
        warns = Warn.find(
            Warn.user.id == self.user.id,
            Warn.chat.id == self.chat.id,
            Warn.is_relevant == True
        )
        
        warns_count = await warns.count()
        
        if warns_count >= self.chat.settings.warns_limit:
            await kick_user(
                chat_id=self.chat.chat_id, 
                user_id=self.user.user_id, 
                reason=self.reason
            )
            await bot.send_message(
                chat_id=self.chat.chat_id,
                text=f'<b>{self.user.full_name} исключен!</b>\nПричина: {self.reason if self.reason else "не указана"}'
            )
            await warns.update_many(Set({Warn.is_relevant: False}))
            
            
class ReputationEvent(BaseDocument):
    chat: Link[Chat]
    giver: Link[User]
    receiver: Link[User]
    delta: int  # -1 или +1
    reason: Optional[str] = None
    message_id: Optional[str] = None

    class Settings:
        name = 'reputation_events'
        indexes = [
            IndexModel(
                [('chat', ASCENDING), ('created_at', DESCENDING)],
                name='ix_chat_created_desc',
            ),
            IndexModel(
                [('chat', ASCENDING), ('receiver', ASCENDING), ('created_at', DESCENDING)],
                name='ix_receiver_recent',
            ),
            IndexModel(
                [('chat', ASCENDING), ('giver', ASCENDING), ('created_at', DESCENDING)],
                name='ix_giver_recent',
            ),
        ]
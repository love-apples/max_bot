from typing import Any, Awaitable, Callable, Dict

from maxapi.filters.middleware import BaseMiddleware
from maxapi.types import UpdateUnion
from maxapi.enums.chat_type import ChatType

from db.models import Chat, User


class EventMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event_object: UpdateUnion,
        data: Dict[str, Any],
    ) -> Any:
        
        data['chat'] = None
        data['user'] = None

        if event_object.chat:
        
            if not event_object.chat.type == ChatType.DIALOG:
                
                chat_id = event_object.chat.chat_id
                chat = await Chat.find_one(Chat.chat_id == chat_id)
                data['chat'] = chat
                
                if not chat:
                    
                    await Chat(
                        chat_id=chat_id,
                        title=event_object.chat.title
                    ).insert()
                    
        if event_object.from_user:
            
            user_id = event_object.from_user.user_id
            user = await User.find_one(User.user_id == user_id)
            data['user'] = user
            
            if not user:
                
                await User(
                    user_id=user_id,
                    full_name=event_object.from_user.full_name,
                    is_bot=event_object.from_user.is_bot
                ).insert()
                
        await handler(event_object, data)
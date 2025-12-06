from maxapi.filters import BaseFilter
from maxapi.types import UpdateUnion, MessageCreated
from maxapi.enums.chat_type import ChatType
from bot.utils.bot import check_is_admin


class IsChat(BaseFilter):
    async def __call__(self, event: UpdateUnion):
        if not event.chat:
            return False
        
        elif not event.chat.type == ChatType.CHAT:
            return False
        
        return True
    
    
class IsChatAdmin(BaseFilter):
    async def __call__(self, event: UpdateUnion):
        if not event.chat or not event.from_user:
            return False
        
        elif not event.chat.type == ChatType.CHAT:
            return False
        
        return await check_is_admin(
            chat=event.chat,
            chat_id=event.chat.chat_id, 
            user_id=event.from_user.user_id
        )
        

class LinkSenderIsNotAdmin(BaseFilter):
    async def __call__(self, event: UpdateUnion):
        if not isinstance(event, MessageCreated):
            return False
        
        if not event.chat or not event.message.link:
            return False
        
        elif not event.chat.type == ChatType.CHAT:
            return False
        
        return not await check_is_admin(
            chat=event.chat,
            chat_id=event.chat.chat_id, 
            user_id=event.message.link.sender.user_id
        )
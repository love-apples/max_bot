from typing import Optional
from core.bot import bot
from core.logger import bot_logger
from maxapi.types.chats import Chat
from maxapi.enums.chat_type import ChatType


async def kick_user(chat_id: int, user_id: int, reason: Optional[str] = None):
    try:
        await bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
    except Exception as e:
        bot_logger.error(
            'Произошла ошибка при кике user_id=%s из чата chat_id=%s - %s', 
            user_id, chat_id, e
        )
    finally:
        bot_logger.info(
            'Кик - user_id=%s из чата chat_id=%s reason=%s', 
            user_id, chat_id, reason
        )
        
        
async def check_is_admin(chat: Chat, chat_id: int, user_id: int):
    if chat.type == ChatType.DIALOG:
        return True
    
    admin_list = await bot.get_list_admin_chat(chat_id)
    
    for admin in admin_list.members:
        if admin.user_id == user_id:
            return True
        
    return False
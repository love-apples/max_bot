from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict

from maxapi.filters.middleware import BaseMiddleware
from maxapi.types import MessageCreated

from bot.utils.bot import check_is_admin
from core.logger import bot_logger as logger
from db.models import Warn


class SimpleAntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, interval: int = 10) -> None:
        self.limit = limit
        self.interval = interval
        self._user_messages: Dict[int, list[float]] = defaultdict(list)

    async def __call__(self, handler, event: MessageCreated, data: Dict[str, Any]) -> Any:  # type: ignore[override]
        if not isinstance(event, MessageCreated) or not event.from_user:
            return await handler(event, data)
        
        is_admin = await check_is_admin(
            chat=event.chat,
            chat_id=event.chat.chat_id,
            user_id=event.from_user.user_id
        )
        
        now = time.time()
        user_id = event.from_user.user_id
        timestamps = self._user_messages[user_id]

        self._user_messages[user_id] = [ts for ts in timestamps if now - ts < self.interval]
        self._user_messages[user_id].append(now)
        
        user_db = data['user']
        chat_db = data['chat']

        if len(self._user_messages[user_id]) > self.limit and not is_admin:
            try:
                await event.message.delete()
                
                await Warn(
                    user=user_db,
                    chat=chat_db,
                    reason='Спам'
                ).insert()
                            
                await event.message.answer(f'{event.from_user.full_name}, получает warn за спам!')
                del self._user_messages[user_id]
                return
            except Exception as e:
                logger.exception(f'Ошибка при обработке спама для пользователя {user_id}: {e}')
                return None

        return await handler(event, data)

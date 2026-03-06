from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from maxapi.filters import BaseFilter
from maxapi.types import UpdateUnion, MessageCreated
from maxapi.enums.chat_type import ChatType

from bot.utils.bot import check_is_admin
from db.models import Chat, ReputationEvent, User


def format_rep_notification(receiver_name: str, giver_name: str, delta: int) -> str:
    if delta > 0:
        action = 'повысил'
    else:
        action = 'понизил'
    return f'{receiver_name}, {giver_name} {action} вашу репутацию'


async def can_change_reputation(chat_id: int, receiver_id: int) -> bool:
    chat = await Chat.find_one(Chat.chat_id == chat_id)
    if chat is None:
        return True
    
    receiver = await User.find_one(User.user_id == receiver_id)
    if receiver is None:
        return True
    
    last_event = await ReputationEvent.find(
        ReputationEvent.chat.id == chat.id,
        ReputationEvent.receiver.id == receiver.id,
    ).sort(-ReputationEvent.created_at).first_or_none()

    if last_event is None:
        return True

    now = datetime.now()
    if now - last_event.created_at >= timedelta(hours=1):
        return True

    return False


@dataclass(frozen=True, slots=True)
class ReputationEventData:
    giver_id: int
    receiver_id: int
    delta: int
    reason: str
    message_id: Optional[int]


class IsEventReputation(BaseFilter):
    """
    Триггерится на сообщение в чате, если:
      - есть link на сообщение другого пользователя (receiver)
      - текст начинается с '+' или '-'
    Опционально можно требовать права админа у отправителя.
    """

    def __init__(self, require_admin: bool = False, max_reason_len: int = 500) -> None:
        self.require_admin = require_admin
        self.max_reason_len = max_reason_len

    async def __call__(self, event: UpdateUnion) -> bool | dict[str, Any]:
        if not isinstance(event, MessageCreated):
            return False

        chat = event.chat
        msg = event.message
        sender = event.from_user

        if chat is None or msg is None or sender is None:
            return False
        if chat.type != ChatType.CHAT:
            return False

        link = getattr(msg, 'link', None)
        if link is None or link.sender is None:
            return False

        receiver = link.sender
        if receiver.user_id == sender.user_id:
            return False

        body = getattr(msg, 'body', None)
        text = getattr(body, 'text', None)
        if not text:
            return False

        txt = text.lstrip()
        if not txt:
            return False

        first = txt[0]
        if first in ('＋',):
            first = '+'
        elif first in ('−', '—', '–', '-'):
            first = '-'

        if first not in ('+', '-'):
            return False

        delta = 1 if first == '+' else -1
        reason = txt[1:].strip()
        if len(reason) > self.max_reason_len:
            reason = reason[: self.max_reason_len].rstrip()

        if self.require_admin:
            is_admin = await check_is_admin(chat_id=chat.chat_id, user_id=sender.user_id)
            if not is_admin:
                return False
            
        if not await can_change_reputation(chat_id=chat.chat_id, receiver_id=receiver.user_id):
            return False

        data = ReputationEventData(
            giver_id=sender.user_id,
            receiver_id=receiver.user_id,
            delta=delta,
            reason=reason,
            message_id=getattr(msg, 'message_id', None),
        )
        return {'rep_event': data}

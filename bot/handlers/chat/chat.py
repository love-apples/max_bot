from typing import List
from maxapi import F, Router
from maxapi.types import UserAdded, BotAdded, Command, MessageCreated
from maxapi.enums.message_link_type import MessageLinkType

from bot.filters.chat import IsChat, IsChatAdmin, LinkSenderIsNotAdmin
from bot.filters.reputation import IsEventReputation, ReputationEventData, format_rep_notification
from bot.utils.bot import kick_user
from db.models import Chat, Kick, ReputationEvent, User, Warn

router = Router('chat')
router.filter(IsChat())


@router.message_created(IsEventReputation())
async def handle_reputation_event(m: MessageCreated, rep_event: ReputationEventData):
    
    chat = await Chat.find_one(Chat.chat_id == m.chat.chat_id)
    if not chat:
        chat = await Chat(
            chat_id=m.chat.chat_id,
            title=m.chat.title,
        ).insert()
        
    giver = await User.find_one(User.user_id == m.from_user.user_id)
    if not giver:
        giver = await User(
            user_id=m.from_user.user_id,
            full_name=m.from_user.full_name,
            is_bot=m.from_user.is_bot
        ).insert()
        
    receiver = await User.find_one(User.user_id == rep_event.receiver_id)
    if not receiver:
        receiver = await User(
            user_id=rep_event.receiver_id,
            full_name=m.message.link.sender.full_name,
            is_bot=m.message.link.sender.is_bot
        ).insert()
    
    await ReputationEvent(
        chat=chat,
        giver=giver,
        receiver=receiver,
        reason=rep_event.reason,
        delta=rep_event.delta,
        message_id=rep_event.message_id
    ).insert()
    
    await m.bot.send_message(
        chat_id=m.chat.chat_id,
        text=format_rep_notification(
            receiver_name=m.message.link.sender.first_name,
            giver_name=m.from_user.first_name,
            delta=rep_event.delta,
        ),
    )


@router.message_created(Command(['start', 'menu']))
async def start(m: MessageCreated):
    """commands_info: Меню бота"""
    pass


@router.user_added()
async def user_added(event: UserAdded, chat: Chat):
    await event.bot.send_message(
        chat_id=event.chat.chat_id,
        text=chat.settings.welcome_user_text.format(name=event.from_user.first_name),
    )
    
    
@router.user_removed()
async def user_removed(event: UserAdded, chat: Chat):
    await event.bot.send_message(
        chat_id=event.chat.chat_id,
        text=chat.settings.buy_user_text.format(name=event.from_user.first_name),
    )
    

@router.bot_added()
async def bot_added(event: BotAdded):
    await event.bot.send_message(
        chat_id=event.chat.chat_id,
        text=(
            'Привет всем! Я — Max Bot. 🤖\n\n'
            'Я помогаю управлять чатом и слежу за репутацией пользователей.\n'
            'Чтобы узнать, что я умею, введите <code>/help</code>.'
        )
    )
    

@router.message_created(
    IsChatAdmin(),
    LinkSenderIsNotAdmin(),
    Command('warn'), 
    F.message.link.type == MessageLinkType.REPLY
)
async def warn(m: MessageCreated, user: User, chat: Chat, args: List[str]):
    """commands_info: выдать предупреждение (ответом на сообщение)"""
    
    link_sender = m.message.link.sender
    
    user_link_db = await User.find_one(
        User.user_id == link_sender.user_id
    )
    
    if not user_link_db:
        user_link_db = await User(
            user_id=link_sender.user_id,
            full_name=link_sender.full_name,
            is_bot=link_sender.is_bot
        ).insert()
    
    reason = None
    args_without_command = args[1:]
    if args_without_command:
        reason = ' '.join(args_without_command)
    
    await Warn(
        user=user_link_db,
        chat=chat,
        admin=user,
        reason=reason
    ).insert()

    await m.message.answer(
        text=f'{link_sender.full_name}, вам выдвинуто предупреждение!\nПричина: {reason if reason else "не указана"}'
    )
    
    
@router.message_created(
    IsChatAdmin(),
    LinkSenderIsNotAdmin(),
    Command('kick'), 
    F.message.link.type == MessageLinkType.REPLY
)
async def kick(m: MessageCreated, user: User, chat: Chat, args: List[str]):
    """commands_info: выгнать из чата (ответом на сообщение)"""
    
    link_sender = m.message.link.sender
    
    user_link_db = await User.find_one(
        User.user_id == link_sender.user_id
    )
    
    if not user_link_db:
        user_link_db = await User(
            user_id=link_sender.user_id,
            full_name=link_sender.full_name,
            is_bot=link_sender.is_bot
        ).insert()
    
    reason = None
    args_without_command = args[1:]
    if args_without_command:
        reason = ' '.join(args_without_command)
        
    await kick_user(
        chat_id=chat.chat_id, 
        user_id=link_sender.user_id,
        reason=reason
    )
    
    await Kick(
        user=user_link_db,
        chat=chat,
        admin=user,
        reason=reason
    ).insert()

    await m.message.answer(
        text=f'<b>{link_sender.full_name} исключен!</b>\nПричина: {reason if reason else "не указана"}'
    )
from typing import List
from maxapi import Router
from maxapi.types import Command, MessageCreated
from maxapi.exceptions import MaxApiError

from db.models import Kick, ReputationEvent, User, Warn

router = Router('all')


@router.message_created(Command('tech_info'))
async def _(m: MessageCreated, args: List[str]):
    """commands_info: получить тех. информацию о пользователе"""
    
    linked = m.message.link
    
    if linked:
        user = linked.sender
    
    elif len(args) > 1:
        value = args[1]
        
        if value.isdigit():
            
            try:
                user = await m.bot.get_chat_by_id(int(value))
            except MaxApiError:
                return await m.message.reply('Пользователь не найден!')
        
        else:
            return await m.message.reply('Некорректное использование команды!\n\n/info [ID]')
        
    else:
        return await m.message.reply('Использование команды:\n\n/info [ID]')
        
    parts = [
        f'<b>Тех. информация о {user.full_name}:</b>\n',
        f'ID: {user.user_id}',
        f'Имя: {user.full_name}'.strip(),
        f'@{user.username}' if user.username else '',
        f'Бот: {"Да" if user.is_bot else "Нет"}',
        f'Последняя активность: {user.last_activity_time}',
        f'Описание: {user.description}' if user.description else '',
        f'Аватар: {user.avatar_url}' if user.avatar_url else '',
        f'Полный аватар: {user.full_avatar_url}' if user.full_avatar_url else '',
    ]

    if user.commands:
        cmd_list = ', '.join(f'/{cmd.command}' for cmd in user.commands)
        parts.append(f'Команды: {cmd_list}')
        
    await m.message.reply('\n'.join(filter(None, parts)))
    
    
@router.message_created(Command('info'))
async def _(m: MessageCreated, args: List[str]):
    """commands_info: получить информацию о пользователе из БД"""
    
    linked = m.message.link
    
    if linked:
        user = linked.sender
    
    elif len(args) > 1:
        value = args[1]
        
        if value.isdigit():
            
            try:
                user = await m.bot.get_chat_by_id(int(value))
            except MaxApiError:
                return await m.message.reply('Пользователь не найден!')
            
        else:
            return await m.message.reply('Некорректное использование команды!\n\n/info [ID]')
        
    else:
        return await m.message.reply('Использование команды:\n\n/info [ID]')
    
    user_db = await User.find_one(User.user_id == user.user_id)
    
    warns_count = await Warn.find(Warn.user.id == user_db.id).count()
    kicks_count = await Kick.find(Kick.user.id == user_db.id).count()
    
    reps_plus_count = await ReputationEvent.find(
        ReputationEvent.receiver.id == user_db.id,
        ReputationEvent.delta == 1
    ).count()
    
    reps_minus_count = await ReputationEvent.find(
        ReputationEvent.receiver.id == user_db.id,
        ReputationEvent.delta == -1
    ).count()
    
    reps = reps_plus_count + reps_minus_count
    reps_text = ('+' if reps > 0 else '-') if not reps == 0 else ''
    
    parts = [
        f'<b>Информация о {user.full_name}:</b>\n',
        f'Кол-во варнов в чатах: {warns_count}',
        f'Кол-во изгнаний из чатов: {kicks_count}\n',
        f'Репутация: {reps_text}{reps}'
    ]

    if user.commands:
        cmd_list = ', '.join(f'/{cmd.command}' for cmd in user.commands)
        parts.append(f'Команды: {cmd_list}')
        
    await m.message.reply('\n'.join(filter(None, parts)))
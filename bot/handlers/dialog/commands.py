from maxapi import Router
from maxapi.types import Command, MessageCreated
from bot.templates.help import help_text


router = Router('commands')


@router.message_created(Command('help'))
async def help(m: MessageCreated):
    await m.message.reply(help_text.format(full_name=m.from_user.full_name))
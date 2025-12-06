from maxapi import Router
from maxapi.types import Command, MessageCreated


router = Router('commands')


@router.message_created(Command('help'))
async def help(m: MessageCreated):
    pass
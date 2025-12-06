import asyncio

from bot.middleware.antispam import SimpleAntiSpamMiddleware
from maxapi import Dispatcher

from bot.handlers import routers
from bot.middleware.outer import EventMiddleware

from config import cnf
from core.bot import bot
from core.logger import bot_logger as logger
from db.crud import init_mongo

dp = Dispatcher(use_create_task=True)
dp.include_routers(*routers)
dp.outer_middleware(EventMiddleware())
dp.middleware(SimpleAntiSpamMiddleware())


@dp.on_started()
async def startup() -> None:
    await init_mongo()
    
    await bot.delete_webhook()
    await bot.set_my_commands(*cnf.bot.COMMANDS)
    for command_info in bot.handlers_commands:
        print(command_info.commands, command_info.info)
    
    logger.info('=== Bot started ===')


async def main() -> None:
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Exit')

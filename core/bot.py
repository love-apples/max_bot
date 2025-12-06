from maxapi import Bot
from maxapi.enums.parse_mode import ParseMode

from config import cnf

bot = Bot(
    token=cnf.bot.TOKEN,
    parse_mode=ParseMode.HTML
)


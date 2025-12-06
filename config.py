from typing import List

from maxapi.types import BotCommand
from pydantic import field_validator
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    TOKEN: str
    ADMINS: List[int] | None = []
    COMMANDS: List[BotCommand] = [
        BotCommand(
            name='start',
            description='Меню'
        )
    ]

    class Config:
        env_prefix = 'BOT_'
        env_file = '.env'
        extra = 'ignore'

    @field_validator('ADMINS', mode='before')
    def split_admins(cls, v):
        try:
            return [int(admin_id) for admin_id in str(v).split(',')]

        except Exception:
            raise ValueError('ADMINS value must be int,int,int')


class MongoConfig(BaseSettings):
    NAME: str
    PORT: int
    HOST: str

    class Config:
        env_prefix = 'Mongo_'
        env_file = '.env'
        extra = 'ignore'

    @property
    def URL(self) -> str:
        return f"mongodb://{self.HOST}:{self.PORT}/{self.NAME}"


class Config:
    mongo = MongoConfig()  # type: ignore
    bot = BotConfig()  # type: ignore


cnf = Config()

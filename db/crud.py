
from beanie import init_beanie

from db import document_models
from core.mongo import client
from config import cnf


async def init_mongo():
    await init_beanie(
        database=client[cnf.mongo.NAME],
        document_models=document_models
    )
from .dialog.commands import router as commands
from .chat.chat import router as chat
from .all import router as all_


routers = [
    commands,
    chat,
    all_,
]

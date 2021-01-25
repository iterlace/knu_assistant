
from typing import List, Tuple, Dict, Optional, Any

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest, SetBotCallbackAnswerRequest
from telethon.tl.custom import (
    MessageButton,
    Conversation,
)


def flatten_keyboard(reply_markup: List[List[MessageButton]]) -> List[MessageButton]:
    result = []
    for row in reply_markup:
        for btn in row:
            result.append(btn)
    return result

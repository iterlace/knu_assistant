from typing import List

from telethon.tl.custom import MessageButton


def flatten_keyboard(reply_markup: List[List[MessageButton]]) -> List[MessageButton]:
    result = []
    for row in reply_markup:
        for btn in row:
            result.append(btn)
    return result

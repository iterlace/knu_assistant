
import logging

import telegram as tg
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

from knu_helper_bot.config import bot
from knu_helper_bot.database import Session, User

logger = logging.getLogger(__name__)


def build_keyboard_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """
    Построить меню
    :param buttons: список кнопок
    :param n_cols: к-во колонок
    :param header_buttons: дополнительные кнопки сверху
    :param footer_buttons: дополнительные кнопки снизу
    :return:
    """
    menu = [buttons[i:i+n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# def basic_home_keyboard(user: User):


# def admin_home_keyboard(user: User):




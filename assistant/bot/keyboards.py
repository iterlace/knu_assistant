import logging

logger = logging.getLogger(__name__)


def build_keyboard_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """
    Построить меню
    :param buttons: list of buttons
    :param n_cols: maximal q-ty of columns in a row
    :param header_buttons: additional buttons above
    :param footer_buttons: additional buttons below
    :return:
    """
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# def basic_home_keyboard(user: User):


# def admin_home_keyboard(user: User):

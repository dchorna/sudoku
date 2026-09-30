from model.user import User

def can_access_level(user: User, mode: str, level: str) -> bool:
    """
    Перевіряє, чи доступний рівень користувачу.
    Легкий — доступний завжди.
    Середній — після 5 перемог на легкому в ТОМУ Ж режимі.
    Складний — після 10 перемог на середньому в ТОМУ Ж режимі.
    """
    if level == "easy":
        return True

    if mode == "classic":
        if level == "medium":
            return user.classic_easy_wins >= 5
        if level == "hard":
            return user.classic_medium_wins >= 10

    elif mode == "consecutive":
        if level == "medium":
            return user.consecutive_easy_wins >= 5
        if level == "hard":
            return user.consecutive_medium_wins >= 10

    return False


def record_win(user: User, mode: str, level: str) -> None:
    """
    Оновлює статистику перемог користувача після успішного розв'язання.
    Рахуємо тільки легкі та середні, бо складні рівні нічого не розблоковують.
    """
    if mode == "classic":
        if level == "easy":
            user.classic_easy_wins += 1
        elif level == "medium":
            user.classic_medium_wins += 1
            
    elif mode == "consecutive":
        if level == "easy":
            user.consecutive_easy_wins += 1
        elif level == "medium":
            user.consecutive_medium_wins += 1
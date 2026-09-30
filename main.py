import time
import getpass
from model.database import init_db, SessionLocal  # Імпортуємо з database.py
from model.user import User                       # А саму модель User з user.py
from generator.board_generator import generate_full_board
from generator.difficulty import generate_puzzle
from generator.wall_generator import compute_walls
from utils.renderer import render_board

def get_available_levels(user: User, mode: str) -> list[str]:
    levels = ["easy"]
    
    if mode == "classic":
        if user.classic_easy_wins >= 5:
            levels.append("medium")
        if user.classic_medium_wins >= 10:
            levels.append("hard")
    elif mode == "consecutive":
        if user.consecutive_easy_wins >= 5:
            levels.append("medium")
        if user.consecutive_medium_wins >= 10:
            levels.append("hard")
            
    return levels

def main():
    init_db()
    db = SessionLocal()

    print("=" * 50)
    print("      ІНТЕРАКТИВНА ГРА СУДОКУ ТА ШІ-ПОМІЧНИК")
    print("=" * 50)
    
    # 1. Авторизація / Реєстрація акаунта
    username = input("Введіть ваше ім'я користувача (логін): ").strip()
    if not username:
        username = "Гравець"
        
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        # getpass приховує введення символів у терміналі
        password = getpass.getpass("Введіть ваш пароль: ").strip()
        if not user.check_password(password):
            print("❌ Невірний пароль! Доступ заборонено.")
            db.close()
            return
        print(f"\n👋 З поверненням, {username}! Ваш прогрес успішно завантажено з бази даних.")
    else:
        print(f"Обліковий запис '{username}' не знайдено. Створюємо новий профіль...")
        password = getpass.getpass("Створіть пароль для входу: ").strip()
        
        user = User(username=username)
        user.set_password(password)  # Зберігається в зашифрованому вигляді (хеш)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"\n🎉 Реєстрація успішна! Ласкаво просимо, {username}.")

    # 2. Вибір виду судоку (Режиму)
    print("\n--- ВИБІР РЕЖИМУ ГРИ ---")
    print("1. Класичне судоку")
    print("2. Судоку з перегородками (Consecutive Sudoku)")
    
    mode_choice = input("Введіть номер режиму (1 або 2): ").strip()
    mode = "consecutive" if mode_choice == "2" else "classic"
    mode_name = "З перегородками" if mode == "consecutive" else "Класичне"

    # 3. Перевірка прогресу та доступних рівнів
    available_levels = get_available_levels(user, mode)
    
    print(f"\n📊 Ваш прогрес у режимі '{mode_name}':")
    if mode == "classic":
        print(f" • Перемог на легкому: {user.classic_easy_wins}")
        print(f" • Перемог на середньому: {user.classic_medium_wins}")
    else:
        print(f" • Перемог на легкому: {user.consecutive_easy_wins}")
        print(f" • Перемог на середньому: {user.consecutive_medium_wins}")
        
    print(f"🔓 Доступні вам рівні складності: {', '.join([lvl.capitalize() for lvl in available_levels])}")

    # 4. Вибір рівня складності
    print(f"\nЗа замовчуванням гра починається з легкого рівня ('easy').")
    level_input = input(f"Оберіть рівень складності ({' / '.join(available_levels)}): ").strip().lower()
    
    if level_input in available_levels:
        level = level_input
    else:
        print("⚠️ Рівень ще не розблокований або введено невірне значення. Встановлено рівень за замовчуванням: easy.")
        level = "easy"

    print(f"\n🚀 Запуск гри | Режим: {mode_name} | Рівень: {level.capitalize()}")
    print("Генеруємо унікальну головоломку...")

    # 5. Генерація головоломки
    started = time.perf_counter()
    solution = generate_full_board()
    puzzle = generate_puzzle(mode, level, solution)
    elapsed = time.perf_counter() - started

    walls = compute_walls(solution) if mode == "consecutive" else None

    # 6. Виведення результату
    print(f"\nЧас генерації: {elapsed:.3f} секунд")
    print(f"Відкритих клітинок (стартових цифр): {sum(1 for row in puzzle.grid for value in row if value != 0)}")
    print("\nВаше ігрове поле:")
    print(render_board(puzzle, mode=mode, walls=walls))
    print("\n✨ Головоломка готова до розв'язання!")
    
    db.close()

if __name__ == "__main__":
    main()
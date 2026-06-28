import json
import os
import webbrowser
import requests
import io
import shutil
import csv

from PIL import Image, ImageOps
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY") # Тепер ми беремо ключ з безпечного файлу

# Кольори для консолі
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
PURPLE = "\033[35m"

FILE_NAME = "movies.json"

# ── Робота з файлами ──────────────────────────────────────────

def load_data():
    if not os.path.exists(FILE_NAME):
        return []

    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError:
        print("Помилка: файл бази даних пошкоджений.")
        return []

    except Exception as e:
        print(f"Помилка завантаження: {e}")
        return []

def save_data(data):
    """Зберігає записи у JSON-файл з резервною копією."""
    # Якщо файл існує, робимо копію перед перезаписом
    if os.path.exists(FILE_NAME):
        shutil.copy(FILE_NAME, FILE_NAME + ".bak")
    
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ── Основні функції ───────────────────────────────────────────

def add_movie(movies):
    """Додає новий об'єкт (фільм або серіал) до списку з перевіркою на дублікати."""
    try:
        # Вибір типу
        m_type_choice = input("Що додаємо? (1 - Фільм, 2 - Серіал): ")
        m_type = "Серіал" if m_type_choice == '2' else "Фільм"
        
        name = input(f"Назва ({m_type}): ")
        
        # Перевірка на існування
        if any(m['name'].lower() == name.lower() for m in movies):
            print(f"Помилка: '{name}' вже є в списку!")
            return

        genre = input("Жанр: ")
        year = int(input("Рік випуску: "))
        trailer_ua = input("Посилання на трейлер (UA): ")
        trailer_en = input("Посилання на трейлер (EN): ")
        poster_url = input("Посилання на постер: ")
        description = input("Короткий опис (сюжет): ")
        status = input("Переглянуто? (так/ні): ").lower() == 'так'
        
        rating = 0.0
        if status:
            rating = float(input("Оцінка (1-10): "))
            if not (1 <= rating <= 10): 
                raise ValueError
        
        movies.append({
            "name": name, 
            "type": m_type, # Збереження типу
            "genre": genre, 
            "year": year, 
            "status": status, 
            "rating": rating,
            "poster_url": poster_url,
            "description": description,
            "trailers": {"ua": trailer_ua, "en": trailer_en}
        })
        save_data(movies)
        print(f"{m_type} успішно додано!")
    except ValueError:
        print("Помилка: введіть коректні дані (рік та оцінка мають бути числами).")

def delete_movie(movies):
    if not movies:
        print(f"{RED}Список порожній!{RESET}")
        return

    print("\n--- ВИДАЛЕННЯ ---")
    print("[1] Видалити за номером")
    print("[2] Видалити за назвою")

    choice = input("Обери спосіб: ")

    if choice == '1':
        print("\n№ | Тип      | Назва")
        print("-" * 40)

        for i, m in enumerate(movies):
            print(
                f"{i + 1:<2} | "
                f"{m.get('type', 'Фільм'):<8} | "
                f"{m['name']}"
            )

        num = input("\nВведіть номер: ")

        if num.isdigit():
            idx = int(num) - 1

            if 0 <= idx < len(movies):
                removed = movies.pop(idx)
                save_data(movies)
                print(f"'{removed['name']}' видалено.")
            else:
                print("Невірний номер.")
        else:
            print("Введіть число.")

    elif choice == '2':
        name = input("Введіть назву: ").lower()

        for i, movie in enumerate(movies):
            if movie['name'].lower() == name:
                removed = movies.pop(i)
                save_data(movies)
                print(f"'{removed['name']}' видалено.")
                return

        print("Не знайдено.")

    else:
        print("Невірний вибір.")

def edit_movie(movies):
    name = input(
        "Назва фільму або серіалу для редагування: "
    )

    for m in movies:
        if m['name'].lower() == name.lower():

            new_type = input(
                f"Новий тип [{m.get('type', 'Фільм')}]: "
            )

            if new_type:
                m['type'] = new_type

            new_name = input(
                f"Нова назва [{m['name']}]: "
            )

            if new_name:

                if any(
                    movie['name'].lower() == new_name.lower()
                    and movie != m
                    for movie in movies
                ):
                    print("Така назва вже існує.")
                    return

                m['name'] = new_name

            genre = input(
                f"Новий жанр [{m['genre']}]: "
            )

            if genre:
                m['genre'] = genre

            try:
                year = input(
                    f"Новий рік [{m['year']}]: "
                )

                if year:
                    year = int(year)

                    if year < 1888 or year > 2100:
                        print("Некоректний рік.")
                        return

                    m['year'] = year

            except ValueError:
                print("Рік повинен бути числом.")
                return

            status = input(
                f"Переглянуто (так/ні): "
            ).lower()

            if status:
                m['status'] = status == "так"

            try:
                rating = input(
                    f"Нова оцінка [{m['rating']}]: "
                )

                if rating:
                    rating = float(rating)

                    if 0 <= rating <= 10:
                        m['rating'] = rating
                    else:
                        print("Оцінка від 0 до 10.")
                        return

            except ValueError:
                print("Оцінка повинна бути числом.")
                return

            save_data(movies)

            print("Оновлено.")
            return

    print("Не знайдено.")

def list_movies(movies, filter_key=None, filter_val=None):
    """Виводить список з вирівнюванням 14 для статусу."""
    if not movies:
        print("Каталог порожній.")
        return
    
    # Заголовок (Статус тепер 14)
    print(f"\n{BOLD}{CYAN}{'№':<3} | {'Тип':<8} | {'Назва':<40} | {'Рік':<5} | {'Оцінка':<6} | {'Статус':<14} | {'Трейлер'}{RESET}")
    print("-" * 115) 
    
    display_list = []
    for m in movies:
        if filter_key and str(m.get(filter_key)).lower() != str(filter_val).lower():
            continue
        display_list.append(m)
        
        m_type = m.get('type', 'Фільм')
        
        score = m.get('rating', 0)
        score_color = GREEN if score >= 8 else (YELLOW if score >= 5 else RED)
        
        # Статус тепер займає 14 символів
        status_text = "ПЕРЕГЛЯНУТО" if m.get('status') else "НЕ ПЕРЕГЛЯНУТО"
        status_color = GREEN if m.get('status') else RED
        
        trailers = m.get('trailers', {})
        has_trailer = "Є" if (trailers.get('ua') or trailers.get('en')) else "—"
        trailer_color = GREEN if has_trailer == "Є" else RED
        
        # Виведення: назва 40 (залишено), Статус 14
        print(f"{YELLOW}{len(display_list):<3}{RESET} | "
              f"{m_type:<8} | "
              f"{m['name'][:39]:<40} | "
              f"{PURPLE}{m['year']:<5}{RESET} | "
              f"{score_color}{score:<6.1f}{RESET} | "
              f"{status_color}{status_text:<14}{RESET} | "
              f"{trailer_color}{has_trailer}{RESET}")
    
    if display_list:
        choice = input("\nВведіть номер для перегляду сюжета/трейлера/постера (або Enter для повернення): ")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(display_list):
                movie = display_list[idx]
                print(f"\n{BOLD}{movie['name']} ({movie.get('type', 'Фільм')}){RESET}")
                print(f"{BOLD}Короткий сюжет:{RESET} {movie.get('description', 'Сюжет відсутній.')}")
                print()
                action = input("Виберіть дію: 1 - Трейлер, 2 - Постер: ")
                if action == "1":
                    lang = input("Оберіть мову (ua/en): ").lower()
                    url = movie.get('trailers', {}).get(lang)
                    if url: 
                        webbrowser.open(url)
                    else: 
                        print(f"{RED}Трейлер не знайдено.{RESET}")
                elif action == "2":
                    show_poster(movie.get('poster_url'))

def search_movie(movies):
    """Пошук фільму або серіалу за назвою."""
    search_query = input("Введіть назву для пошуку: ").lower()
    found = [m for m in movies if search_query in m['name'].lower()]
    
    if found:
        print(f"\nРезультати пошуку:")
        for m in found:
            m_type = m.get('type', 'Фільм')
            print(f"- {m['name']} [{m_type}] (Рік: {m['year']}, Рейтинг: {m['rating']})")
    else:
        print("Не знайдено.")

def show_stats(movies):
    if not movies:
        print("База даних порожня.")
        return

    watched = [m['rating'] for m in movies if m.get('status')]

    avg = sum(watched) / len(watched) if watched else 0

    movies_count = sum(
        1 for m in movies
        if m.get('type') == 'Фільм'
    )

    series_count = sum(
        1 for m in movies
        if m.get('type') == 'Серіал'
    )

    print("\n--- СТАТИСТИКА ---")
    print(f"Всього записів: {len(movies)}")
    print(f"Фільмів: {movies_count}")
    print(f"Серіалів: {series_count}")
    print(f"Переглянуто: {len(watched)}")
    print(f"Середня оцінка: {avg:.2f}")

def filter_movies(movies):
    """Фільтрація за жанром, статусом або типом."""
    print("\n--- ФІЛЬТРАЦІЯ ---")
    print("1 - Жанр")
    print("2 - Статус (Переглянуто)")
    print("3 - Тип (1 - Фільм, 2 - Серіал)")
    choice = input("Оберіть критерій: ")
    
    if choice == '1':
        list_movies(movies, 'genre', input("Введіть жанр: "))
    elif choice == '2':
        is_watched = input("Переглянуто? (так/ні): ").lower() == 'так'
        list_movies(movies, 'status', is_watched)
    elif choice == '3':
        # Логіка вибору цифри 1 або 2
        type_choice = input("Оберіть тип (1 - Фільм, 2 - Серіал): ")
        target_type = "Серіал" if type_choice == '2' else "Фільм"
        list_movies(movies, 'type', target_type)
    else:
        print(f"{RED}Невірний вибір.{RESET}")

def sort_movies(movies):
    """Сортування фільмів та серіалів за рейтингом з вирівнюванням."""
    print(f"\n{'Назва':<25} | {'Тип':<8} | {'Рейтинг'}")
    print("-" * 45)
    for m in sorted(movies, key=lambda x: x['rating'], reverse=True):
        m_type = m.get('type', 'Фільм')
        print(f"{m['name'][:24]:<25} | {m_type:<8} | {m['rating']:.1f}")

def show_poster(image_path):
    """Відображає постер зі збереженням пропорцій (без розтягування)."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
    FIXED_WIDTH = 80 
    
    try:
        if not image_path or image_path == "None":
            print("Постер відсутній.")
            input("\nНатисніть Enter, щоб продовжити...")
            return

        if image_path.startswith("http"):
            response = requests.get(image_path, timeout=10)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
        else:
            if not os.path.exists(image_path):
                print("Помилка: файл постера не знайдено.")
                input("\nНатисніть Enter, щоб продовжити...")
                return
            img = Image.open(image_path)
        
        # Логіка без розтягування:
        width, height = img.size
        # Розраховуємо висоту на основі пропорцій оригіналу
        # 0.55 - це коригування для висоти символів у консолі
        aspect_ratio = height / width
        new_height = int(aspect_ratio * FIXED_WIDTH * 0.55)
        
        # Використовуємо LANCZOS для чіткого зменшення
        img = img.resize((FIXED_WIDTH, new_height), Image.Resampling.LANCZOS)
        img = img.convert("RGB")
        
        pixels = img.getdata()
        
        for i, pixel in enumerate(pixels):
            r, g, b = pixel
            brightness = (r + g + b) // 3
            char = ASCII_CHARS[min(brightness // 25, len(ASCII_CHARS) - 1)]
            
            print(f"\033[38;2;{r};{g};{b}m{char}", end="")
            
            if (i + 1) % FIXED_WIDTH == 0:
                print("\033[0m")
                
        print("\033[0m")
        input("\nНатисніть Enter, щоб повернутися в меню...")
                
    except Exception as e:
        print(f"Помилка при обробці зображення: {e}")
        input("Натисніть Enter, щоб продовжити...")

def export_to_csv():
    movies = load_data()

    if not movies:
        print("Каталог порожній.")
        return

    try:
        with open(
            "movies.csv",
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            writer = csv.writer(f, delimiter=';')

            writer.writerow([
                "Тип",
                "Назва",
                "Жанр",
                "Рік",
                "Оцінка",
                "Статус",
                "Опис",
                "Трейлер UA",
                "Трейлер EN"
            ])

            for m in movies:
                writer.writerow([
                    m.get("type", ""),
                    m.get("name", ""),
                    m.get("genre", ""),
                    m.get("year", ""),
                    m.get("rating", ""),
                    "Переглянуто"
                    if m.get("status")
                    else "Не переглянуто",
                    m.get("description", ""),
                    m.get("trailers", {}).get("ua", ""),
                    m.get("trailers", {}).get("en", "")
                ])

        print("Файл movies.csv успішно створено.")

    except Exception as e:
        print(f"Помилка експорту: {e}")

def check_links(movies):
    """Перевіряє доступність посилань на трейлери з правильними заголовками."""
    if not movies:
        print("Каталог порожній.")
        return

    print(f"\n{RED}--- Перевірка посилань на трейлери ---{RESET}")
    found_broken = False
    
    # Заголовки, щоб YouTube не блокував запит
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for m in movies:
        trailers = m.get('trailers', {})
        for lang, url in trailers.items():
            if url:
                try:
                    # Додаємо headers=headers у запит
                    response = requests.head(url, headers=headers, timeout=3,  allow_redirects=True)
                    
                    # YouTube може повертати 405 (Method Not Allowed) для HEAD, 
                    # тому краще перевіряти статус < 400
                    if response.status_code >= 400:
                        print(f"{RED}Бите посилання ({lang.upper()}) у фільмі '{m['name']}': {url} (Код: {response.status_code}){RESET}")
                        found_broken = True
                except Exception as e:
                    print(f"{RED}Помилка підключення ({lang.upper()}) у фільмі '{m['name']}': {url}{RESET}")
                    found_broken = True
    
    if not found_broken:
        print(f"{GREEN}Усі посилання працюють справно!{RESET}")

def add_movie_by_api(movies):
    # Використовуємо глобальну змінну API_KEY
    query = input("Введіть назву (фільм або серіал): ")
    
    # Пошук
    search_url = f"https://api.themoviedb.org/3/search/multi?api_key={API_KEY}&query={query}"
    response = requests.get(search_url).json()
    all_results = response.get('results', [])

    results = []
    for m in all_results:
        title = m.get('title') or m.get('name') or ""
        # Фільтруємо лише за назвою, якщо запит не порожній
        if title and query.lower() in title.lower():
            results.append(m)

    if not results:
        print(f"{RED}Нічого не знайдено за запитом '{query}'.{RESET}")
        return

    print(f"\nЗнайдено {len(results)} варіантів:")
    for i, m in enumerate(results):
        m_type = m.get('media_type', 'unknown')
        title = m.get('title') or m.get('name')
        year = m.get('release_date') or m.get('first_air_date') or '????'
        print(f"[{i+1}] {title} ({year[:4]}) [{m_type.upper()}]")
    
    choice = input("\nОбери номер (або 0 для відміни): ")
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(results):
        return
        
    movie_data = results[int(choice)-1]
    
    # Визначаємо тип на основі того, що повернуло API
    api_type = movie_data.get('media_type')
    type_str = "Серіал" if api_type == 'tv' else "Фільм"
    
    # Додавання в базу
    new_movie = {
        "name": movie_data.get('title') or movie_data.get('name'),
        "type": type_str, # Додано тип
        "genre": "Невідомо",
        "year": int((movie_data.get('release_date') or movie_data.get('first_air_date') or '0')[:4]),
        "status": False,
        "rating": movie_data.get('vote_average', 0.0),
        "poster_url": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else "",
        "description": movie_data.get('overview', ''),
        "trailers": {"ua": "", "en": ""}
    }
    
    movies.append(new_movie)
    save_data(movies)
    print(f"\nОб'єкт '{new_movie['name']}' ({type_str}) успішно додано!")

def search_by_year_range(movies):
    try:
        start_year = int(input("Початковий рік: "))
        end_year = int(input("Кінцевий рік: "))

        if start_year > end_year:
            start_year, end_year = end_year, start_year

        found = [
            m for m in movies
            if start_year <= m['year'] <= end_year
        ]

        if found:
            print(f"\nЗнайдено записів ({start_year}-{end_year}):")

            for m in sorted(found, key=lambda x: x['year']):
                print(
                    f"- {m['name']} "
                    f"({m['year']}) "
                    f"[{m.get('type', 'Фільм')}]"
                )
        else:
            print("У цьому діапазоні нічого не знайдено.")

    except ValueError:
        print("Помилка: введіть роки числами.")

# ── Меню програми ─────────────────────────────────────────────

def main():
    movies = load_data()
    
    actions = {
        "1": lambda: add_movie(movies),
        "2": lambda: delete_movie(movies),
        "3": lambda: edit_movie(movies),
        "4": lambda: list_movies(movies),
        "5": lambda: search_movie(movies),
        "6": lambda: show_stats(movies),
        "7": lambda: filter_movies(movies),
        "8": lambda: sort_movies(movies),
        "9": export_to_csv,
        "10": lambda: check_links(movies),
        "11": lambda: add_movie_by_api(movies),
        "12": lambda: search_by_year_range(movies)
    }
    
    while True:
        print(f"\n{RED}--- МЕНЮ ПРОГРАМИ ---{RESET}")
        
        print(f"{PURPLE}[1]{RESET}  Додати фільм/серіал (вручну)")
        print(f"{PURPLE}[2]{RESET}  Видалити фільм/серіал")
        print(f"{PURPLE}[3]{RESET}  Редагувати фільм/серіал")
        print(f"{PURPLE}[4]{RESET}  Список фільмів/серіалів")
        print(f"{PURPLE}[5]{RESET}  Пошук фільму/серіалу")
        print(f"{PURPLE}[6]{RESET}  Показати статистику фільмів/серіалів")
        print(f"{PURPLE}[7]{RESET}  Фільтрація (жанр/статус)")
        print(f"{PURPLE}[8]{RESET}  Сортувати за рейтингом")
        print(f"{PURPLE}[9]{RESET}  Експорт в CSV")
        print(f"{PURPLE}[10]{RESET} Перевірка посилань")
        print(f"{PURPLE}[11]{RESET} Додати фільм/серіал через API")
        print(f"{PURPLE}[12]{RESET} Пошук фільмів/серіалів за роками")
        print(f"{PURPLE}[0]{RESET}  Вихід")
        
        choice = input(f"\n{RED}Обери дію: {RESET}")
        
        if choice == '0':
            print("Вихід з програми...")
            break
        
        if choice in actions:
            actions[choice]()
        else:
            print(f"{RED}Помилка! Оберіть коректний пункт меню.{RESET}")

if __name__ == "__main__":
    main()
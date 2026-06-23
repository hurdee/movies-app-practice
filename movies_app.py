import json
import os
import webbrowser
import requests
import io
import shutil
import csv

from PIL import Image
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
    """Завантажує записи з JSON-файлу."""
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Зберігає записи у JSON-файл з резервною копією."""
    # Якщо файл існує, робимо копію перед перезаписом
    if os.path.exists(FILE_NAME):
        shutil.copy(FILE_NAME, FILE_NAME + ".bak")
    
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ── Основні функції ───────────────────────────────────────────

def add_movie(movies):
    """Додає новий фільм до списку з перевіркою на дублікати."""
    try:
        name = input("Назва фільму: ")
        
        # Перевірка на існування фільму
        if any(m['name'].lower() == name.lower() for m in movies):
            print(f"Помилка: Фільм '{name}' вже є в списку!")
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
            "genre": genre, 
            "year": year, 
            "status": status, 
            "rating": rating,
            "poster_url": poster_url,
            "description": description,
            "trailers": {"ua": trailer_ua, "en": trailer_en}
        })
        save_data(movies)
        print("Фільм успішно додано!")
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
        # ВИВОДИМО ТІЛЬКИ СПИСОК (БЕЗ ТРЕЙЛЕРІВ ТА СЮЖЕТІВ)
        print("\n№ | Назва")
        print("-" * 30)
        for i, m in enumerate(movies):
            print(f"{i+1} | {m['name']}")
        
        num = input("\nВведіть номер для видалення: ")
        if num.isdigit():
            idx = int(num) - 1
            if 0 <= idx < len(movies):
                removed = movies.pop(idx)
                save_data(movies)
                print(f"{RED}Фільм '{removed['name']}' видалено.{RESET}")
            else:
                print("Невірний номер.")
                
    elif choice == '2':
        name = input("Введіть назву для видалення: ")
        # Видаляємо фільми, назва яких збігається
        filtered_movies = [m for m in movies if name.lower() not in m['name'].lower()]
        if len(filtered_movies) < len(movies):
            movies[:] = filtered_movies
            save_data(movies)
            print(f"{RED}Видалено.{RESET}")
        else:
            print("Не знайдено.")

def edit_movie(movies):
    """Редагування фільму з перевіркою, щоб назва була унікальною."""
    name = input("Назва фільму для редагування: ")
    for m in movies:
        if m['name'].lower() == name.lower():
            # Отримуємо нову назву
            new_name = input(f"Нова назва [{m['name']}]: ") or m['name']
            
            # Перевірка, чи нове ім'я вже існує в іншого фільму
            if new_name.lower() != m['name'].lower():
                if any(other['name'].lower() == new_name.lower() for other in movies):
                    print(f"Помилка: Фільм з назвою '{new_name}' вже існує!")
                    return
            
            m['name'] = new_name
            m['genre'] = input(f"Новий жанр [{m['genre']}]: ") or m['genre']
            m['year'] = int(input(f"Новий рік [{m['year']}]: ") or m['year'])
            
            if 'trailers' not in m:
                m['trailers'] = {"ua": "", "en": ""}
                
            m['trailers']['ua'] = input(f"Новий трейлер (UA) [{m['trailers']['ua']}]: ") or m['trailers']['ua']
            m['trailers']['en'] = input(f"Новий трейлер (EN) [{m['trailers']['en']}]: ") or m['trailers']['en']
            m['poster_url'] = input(f"Новий постер (URL) [{m.get('poster_url', '')}]: ") or m.get('poster_url', '')
            m['description'] = input(f"Новий опис [{m.get('description', '')}]: ") or m.get('description', '')
            
            new_status = input(f"Переглянуто (так/ні) [{ 'так' if m['status'] else 'ні' }]: ").lower()
            if new_status:
                m['status'] = (new_status == 'так')
                
            m['rating'] = float(input(f"Нова оцінка [{m['rating']}]: ") or m['rating'])
            
            save_data(movies)
            print("Оновлено!")
            return
    print("Не знайдено.")

def list_movies(movies, filter_key=None, filter_val=None):
    """Виводить список фільмів з описом, кольоровим оформленням та статусом трейлера."""
    if not movies:
        print("Каталог порожній.")
        return
    
    # Додали колонку "Трейлер" у заголовок
    print(f"\n{BOLD}{CYAN}{'№':<3} | {'Назва':<25} | {'Рік':<5} | {'Жанр':<12} | {'Оцінка':<6} | {'Статус':<13} | {'Трейлер'}{RESET}")
    print("-" * 90)
    
    display_list = []
    for m in movies:
        if filter_key and str(m.get(filter_key)).lower() != str(filter_val).lower():
            continue
        display_list.append(m)
        
        # Визначаємо колір оцінки
        score = m.get('rating', 0)
        score_color = GREEN if score >= 8 else (YELLOW if score >= 5 else RED)
        
        # Визначаємо статус
        status_text = "ПЕРЕГЛЯНУТО" if m.get('status') else "НЕ ПЕРЕГЛЯНУТО"
        status_color = GREEN if m.get('status') else RED
        
        # Перевірка наявності трейлера (перевіряємо чи є посилання в 'ua' або 'en')
        trailers = m.get('trailers', {})
        has_trailer = "Є" if (trailers.get('ua') or trailers.get('en')) else "—"
        trailer_color = GREEN if has_trailer == "Є" else RED
        
        # Виведення рядка
        print(f"{YELLOW}{len(display_list):<3}{RESET} | {m['name'][:24]:<25} | {PURPLE}{m['year']:<5}{RESET} | "
              f"{m.get('genre', '???')[:11]:<12} | {score_color}{score:<6.1f}{RESET} | "
              f"{status_color}{status_text:<13}{RESET} | {trailer_color}{has_trailer}{RESET}")
    
    # Логіка вибору фільму
    if display_list:
        choice = input("\nВведіть номер фільму для перегляду сюжета/трейлера/постера (або Enter для повернення): ")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(display_list):
                movie = display_list[idx]
                
                # Вивід опису
                print(f"\n{BOLD}Короткий сюжет:{RESET} {movie.get('description', 'Сюжет відсутній.')}")
                print()
                action = input("Виберіть дію: 1 - Трейлер, 2 - Постер: ")
                if action == "1":
                    lang = input("Оберіть мову (ua/en): ").lower()
                    url = movie.get('trailers', {}).get(lang)
                    if url: 
                        webbrowser.open(url)
                    else: 
                        print(f"{RED}Трейлер не знайдено (можливо, в базі немає відео для цієї мови).{RESET}")
                elif action == "2":
                    show_poster(movie.get('poster_url'))

def search_movie(movies):
    """Пошук фільму за назвою."""
    search_query = input("Введіть назву фільму: ").lower()
    found = [m for m in movies if search_query in m['name'].lower()]
    
    if found:
        for m in found:
            print(f"- {m['name']} (Рік: {m['year']}, Рейтинг: {m['rating']})")
    else:
        print("Не знайдено.")

def show_stats(movies):
    """Показ статистики середньої оцінки."""
    if not movies:
        return
    avg = sum(m['rating'] for m in movies) / len(movies)
    print(f"Всього: {len(movies)}, Середня оцінка: {avg:.2f}")

def filter_movies(movies):
    """Фільтрація за жанром або статусом."""
    choice = input("1-жанр, 2-статус: ")
    if choice == '1':
        list_movies(movies, 'genre', input("Жанр: "))
    elif choice == '2':
        list_movies(movies, 'status', input("Переглянуті (так/ні): ").lower() == 'так')

def sort_movies(movies):
    """Сортування фільмів за рейтингом з вирівнюванням."""
    print(f"\n{'Назва':<25} | {'Рейтинг'}")
    print("-" * 35)
    for m in sorted(movies, key=lambda x: x['rating'], reverse=True):
        print(f"{m['name'][:24]:<25} | {m['rating']:.1f}")

def show_poster(image_path):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
    
    try:
        if image_path.startswith("http"):
            response = requests.get(image_path, timeout=10)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
        else:
            if not os.path.exists(image_path):
                print("Помилка: файл постера не знайдено.")
                return
            img = Image.open(image_path)
        
        # ОСНОВНА ЗМІНА ТУТ:
        # Зменшуємо new_width до 80 (або навіть 60 для кращого результату)
        new_width = 80 
        
        width, height = img.size
        aspect_ratio = height / width
        # 0.55 - це коефіцієнт для компенсації висоти символів шрифту
        new_height = int(aspect_ratio * new_width * 0.55)
        
        img = img.resize((new_width, new_height))
        img = img.convert("RGB")
        
        pixels = img.getdata()
        
        for i, pixel in enumerate(pixels):
            r, g, b = pixel
            # Розрахунок яскравості
            brightness = (r + g + b) // 3
            char = ASCII_CHARS[min(brightness // 25, len(ASCII_CHARS)-1)]
            
            # Вивід кольорового ASCII
            print(f"\033[38;2;{r};{g};{b}m{char}", end="")
            
            # Перенос рядка після завершення ширини
            if (i + 1) % new_width == 0:
                print("\033[0m")
                
        print("\033[0m") # Скидання кольору в кінці
        input("\nНатисніть Enter, щоб повернутися в меню...")
                
    except Exception as e:
        print(f"Помилка при обробці зображення: {e}")
        input("Натисніть Enter, щоб продовжити...")

def export_to_csv():
    """Експортує список фільмів у файл movies.csv."""
    movies = load_data() # Тут має бути відступ!
    if not movies:
        print(f"{RED}Каталог порожній. Немає чого експортувати.{RESET}")
        return
    
    try:
        with open("movies.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["Назва", "Жанр", "Рік", "Оцінка", "Статус", "Опис", "Трейлер UA", "Трейлер EN"])
            
            for m in movies:
                writer.writerow([
                    m['name'],
                    m['genre'],
                    m['year'],
                    m['rating'],
                    "Переглянуто" if m['status'] else "Не переглянуто",
                    m.get('description', ''),
                    m.get('trailers', {}).get('ua', ''),
                    m.get('trailers', {}).get('en', '')
                ])
        print(f"Дані успішно експортовано у файл {PURPLE}movies.csv{RESET}!")
    except Exception as e:
        print(f"{RED}Помилка при експорті: {e}{RESET}")

def check_links(movies):
    """Перевіряє доступність посилань на трейлери."""
    if not movies:
        print("Каталог порожній.")
        return

    print(f"\n{RED}--- Перевірка посилань на трейлери ---{RESET}")
    found_broken = False
    
    for m in movies:
        trailers = m.get('trailers', {})
        for lang, url in trailers.items():
            if url:
                try:
                    # Надсилаємо запит до сайту
                    response = requests.head(url, timeout=5)
                    if response.status_code != 200:
                        print(f"{RED}Бите посилання ({lang.upper()}) у фільмі '{m['name']}': {url}{RESET}")
                        found_broken = True
                except Exception:
                    print(f"{RED}Помилка підключення ({lang.upper()}) у фільмі '{m['name']}': {url}{RESET}")
                    found_broken = True
    
    if not found_broken:
        print(f"{GREEN}Усі посилання працюють справно!{RESET}")

def add_movie_by_api(movies):
    # Використовуємо глобальну змінну API_KEY, яка завантажилась через load_dotenv
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
    
    # Додавання в базу
    new_movie = {
        "name": movie_data.get('title') or movie_data.get('name'),
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
    print(f"\nОб'єкт '{new_movie['name']}' успішно додано!")

    
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
        "9": lambda: show_poster("poster.jpg"),
        "10": export_to_csv,
        "11": lambda: check_links(movies),
        "12": lambda: add_movie_by_api(movies)  # Додано функцію API
    }
    
    while True:
        print(f"\n{RED}--- МЕНЮ КІНОМАНА ---{RESET}")
        
        print(f"{PURPLE}[1]{RESET}  Додати фільм (вручну)")
        print(f"{PURPLE}[2]{RESET}  Видалити фільм")
        print(f"{PURPLE}[3]{RESET}  Редагувати фільм")
        print(f"{PURPLE}[4]{RESET}  Список фільмів")
        print(f"{PURPLE}[5]{RESET}  Пошук фільму")
        print(f"{PURPLE}[6]{RESET}  Показати статистику")
        print(f"{PURPLE}[7]{RESET}  Фільтрація (жанр/статус)")
        print(f"{PURPLE}[8]{RESET}  Сортувати за рейтингом")
        print(f"{PURPLE}[9]{RESET}  Тест постера")
        print(f"{PURPLE}[10]{RESET} Експорт в CSV")
        print(f"{PURPLE}[11]{RESET} Перевірка посилань")
        print(f"{PURPLE}[12]{RESET} Додати фільм через API")
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
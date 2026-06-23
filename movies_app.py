import json
import os

FILE_NAME = "movies.json"

def load_data():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def search_movie(movies):
    search_query = input("Введіть назву або частину назви фільму: ").lower()
    found_movies = [m for m in movies if search_query in m['title'].lower()]
    
    if found_movies:
        print(f"\nЗнайдено фільмів: {len(found_movies)}")
        for m in found_movies:
            print(f"- {m['title']} (Рік: {m['year']}, Рейтинг: {m['rating']})")
    else:
        print("На жаль, нічого не знайдено.")

def add_movie(movies):
    try:
        name = input("Назва фільму: ")
        genre = input("Жанр: ")
        year = int(input("Рік випуску: "))
        status = input("Переглянуто? (так/ні): ").lower() == 'так'
        rating = 0
        if status:
            rating = float(input("Оцінка (1-10): "))
            if not (1 <= rating <= 10): raise ValueError
        
        movies.append({"name": name, "genre": genre, "year": year, "status": status, "rating": rating})
        save_data(movies)
        print("Фільм успішно додано!")
    except ValueError:
        print("Помилка: введіть коректні дані (рік та оцінка мають бути числами).")

def delete_movie(movies):
    title_to_delete = input("Введіть назву фільму, який хочете видалити: ")
    # Шукаємо фільми, назва яких НЕ збігається з тією, що ввів користувач
    new_movies = [m for m in movies if m['name'].lower() != title_to_delete.lower()]

    if len(new_movies) == len(movies):
        print(f"Фільм '{title_to_delete}' не знайдено.")
    else:
        save_data(new_movies)
        movies.clear() # Очищаємо список у пам'яті
        movies.extend(new_movies) # Заповнюємо оновленим списком
        print(f"Фільм '{title_to_delete}' успішно видалено.")

def list_movies(movies, filter_key=None, filter_val=None):
    if not movies:
        print("Каталог порожній.")
        return
    
    print("\n--- Список фільмів ---")
    for m in movies:
        if filter_key and str(m.get(filter_key)).lower() != str(filter_val).lower():
            continue
        status = "Переглянуто" if m['status'] else "Не переглянуто"
        print(f"[{m['year']}] {m['name']} | Жанр: {m['genre']} | {status} | Оцінка: {m['rating']}")

def main():
    movies = load_data()
    while True:
        # Додано рядок для пункту 6
        print("\n1. Додати фільм\n2. Список фільмів\n3. Фільтрація за жанром або статусом\n4. Видалити фільм\n5. Пошук фільму\n6. Вихід")
        choice = input("Обери дію: ")
        
        if choice == '1': add_movie(movies)
        elif choice == '2': list_movies(movies)
        elif choice == '3':
            mode = input("Фільтрувати за (1-жанром, 2-статусом перегляду): ")
            if mode == '1':
                genre = input("Введи жанр: ")
                list_movies(movies, 'genre', genre)
            elif mode == '2':
                status = input("Переглянуті? (так/ні): ").lower() == 'так'
                list_movies(movies, 'status', status)
        elif choice == '4': delete_movie(movies)
        elif choice == '5': search_movie(movies)  # Виклик твоєї нової функції
        elif choice == '6': break                 # Тепер вихід під номером 6
        else: print("Невірний вибір!")

if __name__ == "__main__":
    main()
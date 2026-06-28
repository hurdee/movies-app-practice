import unittest
import os
import csv
from unittest.mock import patch
from io import StringIO
import movies_app


class TestMovieCatalog(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_movies.json"
        movies_app.FILE_NAME = self.test_file

        self.movies = [
            {
                "name": "Матриця",
                "type": "Фільм",
                "genre": "Фантастика",
                "year": 1999,
                "status": True,
                "rating": 9.0,
                "poster_url": "",
                "description": "Neo",
                "trailers": {"ua": "", "en": ""}
            },
            {
                "name": "Breaking Bad",
                "type": "Серіал",
                "genre": "Драма",
                "year": 2008,
                "status": False,
                "rating": 8.5,
                "poster_url": "",
                "description": "",
                "trailers": {"ua": "", "en": ""}
            }
        ]

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

        if os.path.exists("movies.csv"):
            os.remove("movies.csv")

        movies_app.FILE_NAME = "movies.json"

    def test_save_load(self):
        movies_app.save_data(self.movies)
        loaded = movies_app.load_data()

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["name"], "Матриця")

    @patch("builtins.input", side_effect=[
        "1",
        "Інтерстеллар",
        "Фантастика",
        "2014",
        "",
        "",
        "",
        "",
        "так",
        "9"
    ])
    def test_add_movie(self, mock_input):
        movies = []

        movies_app.add_movie(movies)

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["name"], "Інтерстеллар")
        self.assertEqual(movies[0]["rating"], 9)

    @patch("builtins.input", side_effect=[
        "1",
        "Матриця",
        "Фантастика",
        "1999",
        "",
        "",
        "",
        "",
        "так",
        "8"
    ])
    def test_duplicate_movie(self, mock_input):
        movies = self.movies.copy()

        movies_app.add_movie(movies)

        self.assertEqual(len(movies), 2)

    @patch("builtins.input", side_effect=["2", "Матриця"])
    def test_delete_by_name(self, mock_input):
        movies = self.movies.copy()

        movies_app.delete_movie(movies)

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["name"], "Breaking Bad")

    @patch("builtins.input", side_effect=[
        "Матриця",
        "",
        "Matrix",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ])
    def test_edit_name(self, mock_input):
        movies = self.movies.copy()

        movies_app.edit_movie(movies)

        self.assertEqual(movies[0]["name"], "Matrix")

    @patch("builtins.input", side_effect=["Мат"])
    def test_search(self, mock_input):
        captured = StringIO()

        with patch("sys.stdout", captured):
            movies_app.search_movie(self.movies)

        self.assertIn("Матриця", captured.getvalue())

    def test_average_rating(self):
        avg = sum(m["rating"] for m in self.movies) / len(self.movies)

        self.assertEqual(avg, 8.75)

    def test_sorting(self):
        sorted_movies = sorted(
            self.movies,
            key=lambda x: x["rating"],
            reverse=True
        )

        self.assertEqual(sorted_movies[0]["name"], "Матриця")

    @patch("builtins.input", side_effect=["1990", "2000"])
    def test_year_search(self, mock_input):
        captured = StringIO()

        with patch("sys.stdout", captured):
            movies_app.search_by_year_range(self.movies)

        self.assertIn("Матриця", captured.getvalue())

    def test_export_csv(self):
        movies_app.save_data(self.movies)
        movies_app.export_to_csv()

        self.assertTrue(os.path.exists("movies.csv"))

        with open(
            "movies.csv",
            encoding="utf-8-sig"
        ) as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)

        self.assertGreater(len(rows), 1)

    @patch("requests.head")
    def test_check_links(self, mock_head):
        mock_head.return_value.status_code = 200

        movies = [
            {
                "name": "Test",
                "trailers": {
                    "ua": "https://youtube.com/test"
                }
            }
        ]

        movies_app.check_links(movies)

        self.assertTrue(mock_head.called)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestMovieCatalog
    )

    runner = unittest.TextTestRunner(
        verbosity=2
    )

    result = runner.run(suite)

    print("\n================================")

    if result.wasSuccessful():
        print("[УСПІХ] Усі тести пройдено.")
    else:
        print("[ПОМИЛКА] Є помилки у програмі.")

    print("================================")
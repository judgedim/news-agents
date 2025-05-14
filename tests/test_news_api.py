import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import sqlite3

# Додаємо каталог батьківського проекту до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Імпортуємо модулі для тестування
from news_api import app, verify_token, API_TOKEN
from fastapi.testclient import TestClient
from fastapi import HTTPException

class TestNewsAPI(unittest.TestCase):
    """Тести для API новин"""
    
    def setUp(self):
        """Підготовка до тестів"""
        self.client = TestClient(app)
        self.test_token = "test_token"
        
        # Зберігаємо оригінальне значення API_TOKEN
        self.original_token = API_TOKEN
        
        # Створюємо тестову базу даних
        self.test_db_path = "test_articles.db"
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()
        
        # Створюємо тестову таблицю
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            summary TEXT,
            link TEXT,
            published TEXT,
            category TEXT
        )
        ''')
        
        # Додаємо тестові дані
        test_articles = [
            ("Test Title 1", "Test Summary 1", "https://example.com/1", "2025-05-14", "Technology"),
            ("Test Title 2", "Test Summary 2", "https://example.com/2", "2025-05-13", "AI"),
            ("Test Title 3", "Test Summary 3", "https://example.com/3", "2025-05-12", "Data Science")
        ]
        
        self.cursor.executemany(
            "INSERT INTO articles (title, summary, link, published, category) VALUES (?, ?, ?, ?, ?)",
            test_articles
        )
        self.conn.commit()
    
    def tearDown(self):
        """Очищення після тестів"""
        # Закриваємо з'єднання з базою даних
        self.conn.close()
        
        # Видаляємо тестову базу даних
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    @patch("news_api.API_TOKEN", "test_token")
    def test_verify_token_success(self):
        """Тестування успішної перевірки токена"""
        # Створюємо мок об'єкт для HTTPAuthorizationCredentials
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test_token"
        
        # Перевіряємо, що функція не викликає виключення
        result = verify_token(mock_credentials)
        self.assertTrue(result)
    
    @patch("news_api.API_TOKEN", "test_token")
    def test_verify_token_failure(self):
        """Тестування невдалої перевірки токена"""
        # Створюємо мок об'єкт для HTTPAuthorizationCredentials
        mock_credentials = MagicMock()
        mock_credentials.credentials = "wrong_token"
        
        # Перевіряємо, що функція викликає виключення
        with self.assertRaises(HTTPException) as context:
            verify_token(mock_credentials)
        
        # Перевіряємо статус код та повідомлення
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Unauthorized")
    
    @patch("news_api.sqlite3.connect")
    @patch("news_api.API_TOKEN", "test_token")
    def test_get_news(self, mock_connect):
        """Тестування отримання новин"""
        # Налаштовуємо мок для бази даних
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Налаштовуємо результат запиту
        mock_cursor.fetchall.return_value = [
            ("Test Title 1", "Test Summary 1", "https://example.com/1", "2025-05-14", "Technology"),
            ("Test Title 2", "Test Summary 2", "https://example.com/2", "2025-05-13", "AI")
        ]
        
        # Виконуємо запит з правильним токеном
        response = self.client.get(
            "/news?limit=2",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Перевіряємо результат
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["news"]), 2)
        self.assertEqual(data["news"][0]["title"], "Test Title 1")
        self.assertEqual(data["news"][1]["title"], "Test Title 2")
        
        # Перевіряємо, що запит до бази даних був викликаний з правильними параметрами
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch("news_api.API_TOKEN", "test_token")
    def test_get_news_unauthorized(self):
        """Тестування отримання новин без авторизації"""
        # Виконуємо запит без токена
        response = self.client.get("/news")
        
        # Перевіряємо, що запит не пройшов авторизацію
        # В FastAPI відсутність токена може повертати статус 403 або 401
        self.assertIn(response.status_code, [401, 403])
        
        # Виконуємо запит з неправильним токеном
        response = self.client.get(
            "/news",
            headers={"Authorization": "Bearer wrong_token"}
        )
        
        # Перевіряємо, що запит не пройшов авторизацію
        self.assertIn(response.status_code, [401, 403])
    
    @patch("news_api.sqlite3.connect")
    @patch("news_api.API_TOKEN", "test_token")
    def test_get_news_with_limit(self, mock_connect):
        """Тестування отримання новин з обмеженням кількості"""
        # Налаштовуємо мок для бази даних
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Налаштовуємо результат запиту
        mock_cursor.fetchall.return_value = [
            ("Test Title 1", "Test Summary 1", "https://example.com/1", "2025-05-14", "Technology")
        ]
        
        # Виконуємо запит з обмеженням кількості
        response = self.client.get(
            "/news?limit=1",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Перевіряємо результат
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["news"]), 1)
        
        # Перевіряємо, що запит до бази даних був викликаний з правильними параметрами
        mock_cursor.execute.assert_called_once_with(
            "SELECT title, summary, link, published, category FROM articles ORDER BY id DESC LIMIT ?",
            (1,)
        )

if __name__ == "__main__":
    unittest.main()

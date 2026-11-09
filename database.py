#импортируем функцию. нужна чтобы Pyton начал автоматически читать .env. функции импортируем перед библиотеками
from dotenv import load_dotenv
#импортируем бибилотекку. Извлечь значение конкретной переменной 
import os
#импортируем библиотеку. Это официальный адаптер (драйвер) PostgreSQL для Python. 
#Простыми словами, он нужен для того, чтобы код на Python мог общаться с СУБД PostgreSQL
import psycopg

# Загрузить переменные окружения из .env
load_dotenv()



connection = psycopg.connect(
    host=os.getenv("DB_host"),
    port=os.getenv("DB_port"),
    dbname=os.getenv("DB_name"),
    user=os.getenv("DB_user"),
    password=os.getenv("SECRET_KEY")
)
connection.autocommit = True

def get_books():
    with connection.cursor() as cursor:
        cursor.execute("SELECT book_id, title, liked FROM books")
        rows = cursor.fetchall()

        books = []

        for row in rows:
            book = {
                "book_id": row[0],
                "title": row[1],
                "liked": row[2]
            }

            books.append(book)

        return books


def get_book(book_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT book_id, title, liked FROM books WHERE book_id = %s",
            (book_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "book_id": row[0],
            "title": row[1],
            "liked": row[2]
        }

def create_book(title, liked):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO books (title, liked)
            VALUES (%s, %s)
            RETURNING book_id, title, liked
            """,
            (title, liked)
        )

        row = cursor.fetchone()
        connection.commit()

        return {
            "book_id": row[0],
            "title": row[1],
            "liked": row[2]
        }

def delete_book(book_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM books WHERE book_id = %s RETURNING book_id",
            (book_id,)
        )

        row = cursor.fetchone()

        return row is not None


def update_book(book_id, title, liked):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE books
            SET title = %s, liked = %s
            WHERE book_id = %s
            RETURNING book_id, title, liked
            """,
            (title, liked, book_id)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "book_id": row[0],
            "title": row[1],
            "liked": row[2]
        }
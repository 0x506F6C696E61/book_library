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
        cursor.execute("""
            SELECT 
                b.book_id, 
                b.title, 
                b.liked,
                COALESCE(
                    string_agg(DISTINCT CONCAT_WS(' ', a.first_name, a.last_name), ', '), 
                    'Не указан'
                ) AS authors,
                COALESCE(
                    array_remove(array_agg(DISTINCT e.publication_year ORDER BY e.publication_year), NULL), 
                    '{}'
                ) AS years,
                COALESCE(
                    array_remove(array_agg(DISTINCT p.name ORDER BY p.name), NULL), 
                    '{}'
                ) AS publishers,
                string_agg(DISTINCT CONCAT_WS(' ', t.first_name, t.last_name), ', ') AS translators
            FROM books b
            LEFT JOIN book_authors ba USING (book_id)
            LEFT JOIN authors a USING (author_id)
            LEFT JOIN editions e USING (book_id)
            LEFT JOIN publishers p USING (publisher_id)
            LEFT JOIN edition_translators et USING (edition_id)
            LEFT JOIN translators t USING (translator_id)
            GROUP BY b.book_id, b.title, b.liked
            ORDER BY b.book_id
        """)
        rows = cursor.fetchall()

        books = []
        for row in rows:
            books.append({
                "book_id": row[0],
                "title": row[1],
                "liked": row[2],
                "author": row[3],
                "years": row[4],
                "publishers": row[5],
                "translator": row[6]
            })

        return books


def get_book(book_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                b.book_id,
                b.title,
                b.liked,

                -- Авторы
                (
                    SELECT string_agg(
                        DISTINCT CONCAT_WS(' ', a.first_name, a.last_name), ', '
                    )
                    FROM book_authors ba
                    JOIN authors a USING (author_id)
                    WHERE ba.book_id = b.book_id
                ) AS authors,

                -- Страны авторов
                (
                    SELECT string_agg(
                        DISTINCT a.author_country, ', '
                    )
                    FROM book_authors ba
                    JOIN authors a USING (author_id)
                    WHERE ba.book_id = b.book_id
                      AND a.author_country IS NOT NULL
                      AND a.author_country <> ''
                ) AS author_countries,

                -- Годы издания
                (
                    SELECT array_agg(DISTINCT e.publication_year ORDER BY e.publication_year)
                    FROM editions e
                    WHERE e.book_id = b.book_id
                      AND e.publication_year IS NOT NULL
                ) AS years,

                -- Издательства
                (
                    SELECT array_agg(DISTINCT p.name ORDER BY p.name)
                    FROM editions e
                    JOIN publishers p USING (publisher_id)
                    WHERE e.book_id = b.book_id
                ) AS publishers,

                -- Языки издания
                (
                    SELECT array_agg(DISTINCT e.language ORDER BY e.language)
                    FROM editions e
                    WHERE e.book_id = b.book_id
                      AND e.language IS NOT NULL
                ) AS languages,

                -- Переводчики
                (
                    SELECT string_agg(
                        DISTINCT CONCAT_WS(' ', t.first_name, t.last_name), ', '
                    )
                    FROM editions e
                    JOIN edition_translators et USING (edition_id)
                    JOIN translators t USING (translator_id)
                    WHERE e.book_id = b.book_id
                ) AS translators

            FROM books b
            WHERE b.book_id = %s
        """, (book_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "book_id": row[0],
            "title": row[1],
            "liked": row[2],
            "author": row[3],
            "author_country": row[4],
            "years": row[5] or [],
            "publishers": row[6] or [],
            "languages": row[7] or [],
            "translator": row[8]
        }


def get_authors():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                author_id, 
                CONCAT_WS(' ', first_name, last_name) AS full_name, 
                author_country
            FROM authors
            ORDER BY author_id
        """)
        rows = cursor.fetchall()

        authors = []
        for row in rows:
            authors.append({
                "author_id": row[0],
                "name": row[1],
                "author_country": row[2]
            })

        return authors



def create_book(title, liked, author_ids: list[int]):
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO books (title, liked)
                VALUES (%s, %s)
                RETURNING book_id, title, liked
                """,
                (title, liked)
            )
            book_row = cursor.fetchone()
            new_book_id = book_row[0]

            if author_ids:
                for author_id in author_ids:
                    cursor.execute(
                        """
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        """,
                        (new_book_id, author_id)
                    )

            connection.commit()

            return {
                "book_id": book_row[0],
                "title": book_row[1],
                "liked": book_row[2],
                "author_ids": author_ids
            }
        except Exception as e:
            connection.rollback()
            raise e


def delete_book(book_id):
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM book_authors WHERE book_id = %s", (book_id,))
            cursor.execute("DELETE FROM books WHERE book_id = %s RETURNING book_id", (book_id,))
            row = cursor.fetchone()
            connection.commit()
            return row is not None
        except Exception as e:
            connection.rollback()
            raise e


def update_book(book_id, title, liked, author_ids: list[int]):
    with connection.cursor() as cursor:
        try:
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

            cursor.execute("DELETE FROM book_authors WHERE book_id = %s", (book_id,))

            if author_ids:
                for author_id in author_ids:
                    cursor.execute(
                        """
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        """,
                        (book_id, author_id)
                    )

            connection.commit()

            return {
                "book_id": row[0],
                "title": row[1],
                "liked": row[2],
                "author_ids": author_ids
            }
        except Exception as e:
            connection.rollback()
            raise e
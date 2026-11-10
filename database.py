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
                    string_agg(CONCAT_WS(' ', a.first_name, a.last_name), ', '), 
                    'Не указан'
                ) as authors
            FROM books b
            LEFT JOIN book_authors ba USING (book_id)
            LEFT JOIN authors a USING (author_id)
            GROUP BY b.book_id, b.title, b.liked
        """)
        rows = cursor.fetchall()

        books = []
        for row in rows:
            book = {
                "book_id": row[0],
                "title": row[1],
                "liked": row[2],
                "author": row[3]  # Теперь сюда запишется строка вида "Иван Иванов, Петр Петров"
            }
            books.append(book)

        return books


def get_book(book_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                b.book_id, 
                b.title, 
                b.liked,
                COALESCE(string_agg(CONCAT_WS(' ', a.first_name, a.last_name), ', '), 'Не указан') as authors
            FROM books b
            LEFT JOIN book_authors ba USING (book_id)
            LEFT JOIN authors a USING (author_id)
            WHERE b.book_id = %s
            GROUP BY b.book_id, b.title, b.liked
        """, (book_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "book_id": row[0],
            "title": row[1],
            "liked": row[2],
            "author": row[3]
        }

def create_book(title, liked, author_ids: list[int]):
    with connection.cursor() as cursor:
        try:
            # 1. Создаем саму книгу
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

            # 2. Привязываем книгу к авторам в промежуточной таблице
            if author_ids:
                for author_id in author_ids:
                    cursor.execute(
                        """
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        """,
                        (new_book_id, author_id)
                    )

            # Подтверждаем транзакцию, если все шаги прошли успешно
            connection.commit()

            # Возвращаем созданную книгу (для фронтенда мы можем временно отдать пустую строку 
            # или сделать повторный SELECT, но для простоты вернем структуру книги)
            return {
                "book_id": book_row[0],
                "title": book_row[1],
                "liked": book_row[2],
                "author_ids": author_ids
            }
            
        except Exception as e:
            # Если произошла ошибка (например, передали несуществующий author_id), 
            # отменяем все изменения этого шага
            connection.rollback()
            raise e

def delete_book(book_id):
    with connection.cursor() as cursor:
        try:
            # 1. Сначала удаляем все связи этой книги с авторами
            cursor.execute(
                "DELETE FROM book_authors WHERE book_id = %s",
                (book_id,)
            )
            
            # 2. Теперь спокойно удаляем саму книгу
            cursor.execute(
                "DELETE FROM books WHERE book_id = %s RETURNING book_id",
                (book_id,)
            )
            
            row = cursor.fetchone()
            
            # Подтверждаем изменения в БД
            connection.commit()
            
            return row is not None
        
        except Exception as e:
            # Если что-то пошло не так, отменяем операцию
            connection.rollback()
            raise e

def update_book(book_id, title, liked, author_ids: list[int]):
    with connection.cursor() as cursor:
        try:
            # 1. Обновляем основные данные книги
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

            # 2. Удаляем старые связи с авторами
            cursor.execute(
                "DELETE FROM book_authors WHERE book_id = %s",
                (book_id,)
            )

            # 3. Записываем новые связи с авторами
            if author_ids:
                for author_id in author_ids:
                    cursor.execute(
                        """
                        INSERT INTO book_authors (book_id, author_id)
                        VALUES (%s, %s)
                        """,
                        (book_id, author_id)
                    )

            # Подтверждаем транзакцию
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
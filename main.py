from typing import List
from fastapi import FastAPI, HTTPException #FastAPI — это веб-фреймворк для создания API на Python,
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field #pydantic - библиотека, нужна для валидации входящих и сходящих данных по типам, для установки ограничений; basemodel - класс
import database

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class BookCreate(BaseModel):    #наследуемся от BaseModel
    title: str  #в pydantic обязательно нужно указывать типы данных
    liked: str
    # min_items=1 требует, чтобы в массиве был как минимум 1 ID автора
    author_ids: List[int] = Field(..., min_items=1) 

@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/books") 
def get_books():
    return database.get_books()


@app.get("/books/{book_id}")
def get_book(book_id: int):
    book = database.get_book(book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return book


@app.get("/authors")
def get_authors():
    return database.get_authors()



@app.post("/books")
def create_book(book: BookCreate):
    try:
        return database.create_book(book.title, book.liked, book.author_ids)
    except Exception as e:
        # Если база данных выбросила ошибку (например, из-за внешнего ключа ForeignKey)
        raise HTTPException(
            status_code=400, 
            detail=f"Не удалось создать книгу. Проверьте правильность ID авторов. Ошибка: {str(e)}"
        )


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    deleted = database.delete_book(book_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Книга не найдена")


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    try:
        updated_book = database.update_book(
            book_id,
            book.title,
            book.liked,
            book.author_ids  # Передаем массив ID авторов
        )

        if updated_book is None:
            raise HTTPException(
                status_code=404,
                detail="Книга не найдена"
            )

        return updated_book
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Не удалось обновить книгу. Ошибка: {str(e)}"
        )
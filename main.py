from fastapi import FastAPI, HTTPException #FastAPI — это веб-фреймворк для создания API на Python,
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel #pydantic - библиотека, нужна для валидации входящих и сходящих данных по типам, для установки ограничений; basemodel - класс
import database

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class BookCreate(BaseModel):    #наследуемся от BaseModel
    title: str  #в pydantic обязательно нужно указывать типы данных
    liked: str


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


@app.post("/books")
def create_book(book: BookCreate):
    return database.create_book(book.title, book.liked)


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    deleted = database.delete_book(book_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Книга не найдена")


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    updated_book = database.update_book(
        book_id,
        book.title,
        book.liked
    )

    if updated_book is None:
        raise HTTPException(
            status_code=404,
            detail="Книга не найдена"
        )

    return updated_book
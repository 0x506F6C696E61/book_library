const booksContainer = document.getElementById("books");
const message = document.getElementById("message");
const searchInput = document.getElementById("search");
const loadButton = document.getElementById("load-books");

let books = [];

async function loadBooks() {
    message.textContent = "Загружаем книги...";

    try {
        const response = await fetch("/books");

        if (!response.ok) {
            throw new Error("Не удалось загрузить книги");
        }

        books = await response.json();

        renderBooks(books);

    } catch (error) {
        message.textContent = "Ошибка загрузки книг. Проверь работу сервера.";
        console.error(error);
    }
}

function renderBooks(bookList) {
    booksContainer.replaceChildren();

    if (bookList.length === 0) {
        message.textContent = "Книги не найдены.";
        return;
    }

    message.textContent = `Найдено книг: ${bookList.length}`;

    bookList.forEach(book => {
        const card = document.createElement("article");
        card.className = "book-card";

        const title = document.createElement("h3");
        title.textContent = book.title ?? "Без названия";

        const author = document.createElement("p");
        author.textContent = `Автор: ${book.author ?? "Не указан"}`;

        const liked = document.createElement("p");
        liked.textContent = `Оценка: ${book.liked ?? "Не указана"}`;

        card.append(title, author, liked);
        booksContainer.appendChild(card);
    });
}

searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();

    const filteredBooks = books.filter(book => {
        const title = String(book.title ?? "").toLowerCase();
        const author = String(book.author ?? "").toLowerCase();

        return title.includes(query) || author.includes(query);
    });

    renderBooks(filteredBooks);
});

loadButton.addEventListener("click", loadBooks);

loadBooks();
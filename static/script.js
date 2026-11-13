document.addEventListener("DOMContentLoaded", () => {
    const booksContainer = document.getElementById("books");
    const message = document.getElementById("message");
    const titleFilter = document.getElementById("title-filter");

    // Элементы модального окна
    const bookModal = document.getElementById("book-modal");
    const modalClose = document.getElementById("modal-close");
    const bookDetails = document.getElementById("book-details");    

    const rangeMin = document.getElementById("range-min");
    const rangeMax = document.getElementById("range-max");
    const progress = document.getElementById("slider-progress");
    const yearsList = document.getElementById("timeline-years");
    const resetBtn = document.getElementById("reset-btn");

    const authorFilter = document.getElementById("author-filter");
    const publisherFilter = document.getElementById("publisher-filter");

    let allBooks = [];
    let uniqueYears = [];

    // Загружаем подробные сведения о выбранной книге
async function openBookModal(bookId) {
    try {
        const response = await fetch(`/books/${bookId}`);

        if (!response.ok) {
            throw new Error(`Ошибка сервера: ${response.status}`);
        }

        const book = await response.json();

        // Очищаем содержимое предыдущей книги
bookDetails.replaceChildren();

// Добавляем сведения о книге
const details = [
    ["Название", book.title],
    ["Автор", book.author],
    ["Страна автора", book.author_country],
    ["Издательство", book.publishers],
    ["Язык издания", book.languages],
    ["Год издания", book.years],
    ["Переводчик", book.translator],
    ["Моя оценка", book.liked]
];

// Создаём отдельный блок для каждого сведения
details.forEach(([label, value]) => {
    if (value === null || value === undefined || value === "") {
        return;
    }

    const item = document.createElement("div");
    item.className = "book-detail";

    const title = document.createElement("span");
    title.className = "book-detail-label";
    title.textContent = label;

    const content = document.createElement("span");
    content.className = "book-detail-value";
    content.textContent = Array.isArray(value) ? value.join(", ") : value;

    item.append(title, content);
    bookDetails.appendChild(item);
});

// Показываем модальное окно
bookModal.classList.add("active");

    } catch (error) {
        console.error("Не удалось загрузить сведения о книге:", error);
    }
}

    async function loadBooks() {
        message.textContent = "Загружаем книги...";

        try {
            const response = await fetch("/books");
            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            allBooks = await response.json();
            populateDropdowns();
            initTimeline();
        } catch (error) {
            message.textContent = "Ошибка загрузки книг. Проверьте терминал Python.";
            console.error(error);
        }
    }

    // Заполняем выпадающие списки авторов и издательств
    function populateDropdowns() {
        const authorsSet = new Set();
        const publishersSet = new Set();

        allBooks.forEach(book => {
            if (book.author && book.author !== "Не указан") {
                book.author.split(",").forEach(a => {
                    const trimmed = a.trim();
                    if (trimmed) authorsSet.add(trimmed);
                });
            }

            if (Array.isArray(book.publishers)) {
                book.publishers.forEach(pub => {
                    if (pub) publishersSet.add(pub.trim());
                });
            }
        });

        const sortedAuthors = [...authorsSet].sort((a, b) => a.localeCompare(b, "ru"));
        const sortedPublishers = [...publishersSet].sort((a, b) => a.localeCompare(b, "ru"));

        authorFilter.innerHTML = '<option value="">Автор</option>';
        sortedAuthors.forEach(author => {
            const opt = document.createElement("option");
            opt.value = author;
            opt.textContent = author;
            authorFilter.appendChild(opt);
        });

        publisherFilter.innerHTML = '<option value="">Издательство</option>';
        sortedPublishers.forEach(pub => {
            const opt = document.createElement("option");
            opt.value = pub;
            opt.textContent = pub;
            publisherFilter.appendChild(opt);
        });
    }

    function initTimeline() {
        const yearsSet = new Set();
        allBooks.forEach(book => {
            if (Array.isArray(book.years)) {
                book.years.forEach(y => {
                    if (y !== null && y !== undefined) yearsSet.add(Number(y));
                });
            }
        });

        uniqueYears = [...yearsSet].sort((a, b) => a - b);

        if (uniqueYears.length === 0) {
            rangeMin.disabled = true;
            rangeMax.disabled = true;
            applyFilters();
            return;
        }

        const maxIndex = uniqueYears.length - 1;
        rangeMin.disabled = false;
        rangeMax.disabled = false;

        rangeMin.min = 0;
        rangeMin.max = maxIndex;
        rangeMin.value = 0;

        rangeMax.min = 0;
        rangeMax.max = maxIndex;
        rangeMax.value = maxIndex;

        applyFilters();
    }

    function renderScaleLabels(minIdx, maxIdx, maxIndex) {
        yearsList.innerHTML = "";
        if (maxIndex <= 0) return;

        const startYear = uniqueYears[minIdx];
        const endYear = uniqueYears[maxIdx];
        const leftPercent = (minIdx / maxIndex) * 100;
        const rightPercent = (maxIdx / maxIndex) * 100;

        uniqueYears.forEach((year, idx) => {
            const posPercent = (idx / maxIndex) * 100;
            const tooCloseToLeft = Math.abs(posPercent - leftPercent) < 7;
            const tooCloseToRight = Math.abs(posPercent - rightPercent) < 7;

            if (!tooCloseToLeft && !tooCloseToRight && idx % 2 === 0) {
                const tick = document.createElement("li");
                tick.className = "timeline__tick";
                tick.style.left = `${posPercent}%`;
                tick.textContent = year;

                tick.addEventListener("click", () => {
                    rangeMin.value = idx;
                    rangeMax.value = idx;
                    applyFilters();
                });

                yearsList.appendChild(tick);
            }
        });

        if (minIdx === maxIdx) {
            const singleBadge = document.createElement("li");
            singleBadge.className = "timeline__badge";
            singleBadge.style.left = `${leftPercent}%`;
            singleBadge.textContent = startYear;
            yearsList.appendChild(singleBadge);
        } else {
            const leftBadge = document.createElement("li");
            leftBadge.className = "timeline__badge";
            leftBadge.style.left = `${leftPercent}%`;
            leftBadge.textContent = startYear;

            const rightBadge = document.createElement("li");
            rightBadge.className = "timeline__badge";
            rightBadge.style.left = `${rightPercent}%`;
            rightBadge.textContent = endYear;

            yearsList.append(leftBadge, rightBadge);
        }
    }

    function applyFilters() {
        const titleQuery = titleFilter.value.trim().toLowerCase();
        const selectedAuthor = authorFilter.value;
        const selectedPublisher = publisherFilter.value;

        // Подсвечиваем селекты, если в них что-то выбрано
        authorFilter.classList.toggle("has-value", Boolean(selectedAuthor));
        publisherFilter.classList.toggle("has-value", Boolean(selectedPublisher));

        let filtered = allBooks;

        // 1. Фильтр по таймлайну
        if (uniqueYears.length > 0) {
            const maxIndex = uniqueYears.length - 1;
            let minIdx = parseInt(rangeMin.value, 10);
            let maxIdx = parseInt(rangeMax.value, 10);

            if (minIdx > maxIdx) {
                [minIdx, maxIdx] = [maxIdx, minIdx];
            }

            const startYear = uniqueYears[minIdx];
            const endYear = uniqueYears[maxIdx];

            const leftPercent = maxIndex === 0 ? 0 : (minIdx / maxIndex) * 100;
            const rightPercent = maxIndex === 0 ? 0 : 100 - (maxIdx / maxIndex) * 100;
            progress.style.left = `${leftPercent}%`;
            progress.style.right = `${rightPercent}%`;

            renderScaleLabels(minIdx, maxIdx, maxIndex);

            const isFullRange = minIdx === 0 && maxIdx === maxIndex;

            filtered = filtered.filter(book => {
                const bookYears = Array.isArray(book.years) ? book.years : [];
                if (bookYears.length === 0) return isFullRange;
                return bookYears.some(y => y >= startYear && y <= endYear);
            });
        }

        // 2. Фильтр по автору
        if (selectedAuthor) {
            filtered = filtered.filter(book => {
                if (!book.author) return false;
                const bookAuthors = book.author.split(",").map(a => a.trim());
                return bookAuthors.includes(selectedAuthor);
            });
        }

        // 3. Фильтр по издательству
        if (selectedPublisher) {
            filtered = filtered.filter(book => {
                return Array.isArray(book.publishers) && book.publishers.includes(selectedPublisher);
            });
        }

        // 4. Фильтр по названию книги
        if (titleQuery) {
            filtered = filtered.filter(book => {
                const title = String(book.title ?? "").toLowerCase();
                return title.includes(titleQuery);
            });
        }

        renderBooks(filtered);
    }

    function renderBooks(bookList) {
        booksContainer.replaceChildren();

        if (bookList.length === 0) {
            message.textContent = "Книги по выбранным фильтрам не найдены.";
            return;
        }

        message.textContent = `Найдено книг: ${bookList.length}`;

        bookList.forEach(book => {
            const card = document.createElement("article");
            card.className = "book-card";

            //Открываем сведения о книге при нажатии на карточку
            card.addEventListener("click", () => {
                openBookModal(book.book_id);
            });

            const top = document.createElement("div");

            const title = document.createElement("h3");
            title.textContent = book.title ?? "Без названия";

            const author = document.createElement("p");
            author.textContent = book.author ?? "Автор не указан";

            top.append(title, author);

            card.appendChild(top)
            booksContainer.appendChild(card);
        });
    }

    rangeMin.addEventListener("input", applyFilters);
    rangeMax.addEventListener("input", applyFilters);
    authorFilter.addEventListener("change", applyFilters);
    publisherFilter.addEventListener("change", applyFilters);
    titleFilter.addEventListener("input", applyFilters);

    resetBtn.addEventListener("click", () => {
if (uniqueYears.length > 0) {
rangeMin.value = 0;
rangeMax.value = uniqueYears.length - 1;
}
authorFilter.value = "";
publisherFilter.value = "";
titleFilter.value = "";
applyFilters();
});
loadBooks();

// Закрываем окно по нажатию на крестик
modalClose.addEventListener("click", () => {
    bookModal.classList.remove("active");
});

// Закрываем окно по нажатию на затемнённую область
bookModal.addEventListener("click", (event) => {
    if (event.target === bookModal) {
        bookModal.classList.remove("active");
    }
});

// Закрываем окно по нажатию клавиши Escape
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        bookModal.classList.remove("active");
    }
});

});
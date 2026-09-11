import pytest
from reading_logic import (
    normalize_category,
    is_duplicate_title,
    find_book_by_title,
    search_books,
    filter_by_category,
    recommend_next_book,
    get_statistics
)
from config import STATUS_UNREAD, STATUS_COMPLETED, STATUS_READING


def test_category_normalization():
    """Test 4: Category normalization for standard and custom inputs."""
    assert normalize_category("ai") == "AI/ML"
    assert normalize_category("ML") == "AI/ML"
    assert normalize_category("self help") == "self-help"
    assert normalize_category("biz") == "business"
    assert normalize_category("cybersecurity") == "Cybersecurity"  # custom capitalized
    assert normalize_category("") == "general"
    assert normalize_category(None) == "general"


def test_duplicate_detection():
    """Test 3: Case-insensitive duplicate detection."""
    books = [
        {"title": "Atomic Habits", "category": "self-help", "status": STATUS_UNREAD},
        {"title": "Deep Work", "category": "productivity", "status": STATUS_UNREAD}
    ]
    assert is_duplicate_title(books, "Atomic Habits") is True
    assert is_duplicate_title(books, "atomic habits") is True
    assert is_duplicate_title(books, "ATOMIC HABITS") is True
    assert is_duplicate_title(books, "Clean Code") is False


def test_search_books():
    """Test 6: Case-insensitive search across title, category, status."""
    books = [
        {"title": "Atomic Habits", "category": "self-help", "status": STATUS_UNREAD},
        {"title": "The Psychology of Money", "category": "finance", "status": STATUS_UNREAD},
        {"title": "Hands-On Machine Learning", "category": "AI/ML", "status": STATUS_COMPLETED}
    ]

    money_results = search_books(books, "Money")
    assert len(money_results) == 1
    assert money_results[0]["title"] == "The Psychology of Money"

    ai_results = search_books(books, "AI/ML")
    assert len(ai_results) == 1

    unread_results = search_books(books, "unread")
    assert len(unread_results) == 2


def test_category_filtering():
    """Test 7: Category filtering."""
    books = [
        {"title": "Hands-On Machine Learning", "category": "AI/ML", "status": STATUS_UNREAD},
        {"title": "Deep Learning", "category": "AI/ML", "status": STATUS_UNREAD},
        {"title": "Deep Work", "category": "productivity", "status": STATUS_UNREAD}
    ]
    ai_books = filter_by_category(books, "ai")
    assert len(ai_books) == 2

    prod_books = filter_by_category(books, "productivity")
    assert len(prod_books) == 1
    assert prod_books[0]["title"] == "Deep Work"


def test_recommendation_logic():
    """Test 11: Recommendation logic (prioritizes unread, category, FIFO, excludes completed)."""
    books = [
        {"title": "Atomic Habits", "category": "self-help", "status": STATUS_COMPLETED},
        {"title": "Deep Work", "category": "productivity", "status": STATUS_UNREAD},
        {"title": "The Psychology of Money", "category": "finance", "status": STATUS_UNREAD}
    ]

    rec = recommend_next_book(books)
    assert rec["success"] is True
    assert rec["book"]["title"] == "Deep Work"  # Earliest unread book (FIFO)

    # Category specific recommendation
    rec_fin = recommend_next_book(books, category="finance")
    assert rec_fin["success"] is True
    assert rec_fin["book"]["title"] == "The Psychology of Money"


def test_recommendation_empty_or_all_completed():
    """Test 12: Empty reading list recommendation handling."""
    rec_empty = recommend_next_book([])
    assert rec_empty["success"] is False
    assert "empty" in rec_empty["message"].lower()

    completed_books = [
        {"title": "Atomic Habits", "category": "self-help", "status": STATUS_COMPLETED}
    ]
    rec_completed = recommend_next_book(completed_books)
    assert rec_completed["success"] is False
    assert "read all books" in rec_completed["message"].lower()


def test_get_statistics():
    """Test statistics calculation."""
    books = [
        {"title": "Book 1", "category": "AI/ML", "status": STATUS_UNREAD},
        {"title": "Book 2", "category": "AI/ML", "status": STATUS_READING},
        {"title": "Book 3", "category": "finance", "status": STATUS_COMPLETED}
    ]
    stats = get_statistics(books)
    assert stats["total"] == 3
    assert stats["unread"] == 1
    assert stats["reading"] == 1
    assert stats["completed"] == 1
    assert stats["by_category"]["AI/ML"] == 2
    assert stats["by_category"]["finance"] == 1

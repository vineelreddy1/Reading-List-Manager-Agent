import datetime
from typing import List, Dict, Any, Optional
from config import CATEGORY_NORMALIZATION_MAP, STATUS_UNREAD, STATUS_READING, STATUS_COMPLETED


def normalize_category(category: str) -> str:
    """
    Normalize category capitalization and handle custom user categories.
    Example: 'ai' -> 'AI/ML', 'self help' -> 'self-help'.
    """
    if not category or not isinstance(category, str):
        return "general"

    raw = category.strip()
    key = raw.lower()

    if key in CATEGORY_NORMALIZATION_MAP:
        return CATEGORY_NORMALIZATION_MAP[key]

    # For custom categories, format cleanly
    if raw.isupper() or "/" in raw or "-" in raw:
        return raw
    return raw.capitalize()


def is_duplicate_title(books: List[Dict[str, Any]], title: str) -> bool:
    """
    Detect duplicate titles case-insensitively.
    """
    if not title or not isinstance(title, str):
        return False
    target = title.strip().lower()
    return any(b.get("title", "").strip().lower() == target for b in books)


def find_book_by_title(books: List[Dict[str, Any]], title: str) -> Optional[Dict[str, Any]]:
    """
    Find book object matching title case-insensitively.
    """
    if not title or not isinstance(title, str):
        return None
    target = title.strip().lower()
    for book in books:
        if book.get("title", "").strip().lower() == target:
            return book
    return None


def search_books(books: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Case-insensitive search across title, category, and status.
    """
    if not query or not isinstance(query, str):
        return books
    
    q = query.strip().lower()
    results = []
    for b in books:
        t = b.get("title", "").lower()
        c = b.get("category", "").lower()
        s = b.get("status", "").lower()
        if q in t or q in c or q in s:
            results.append(b)
    return results


def filter_by_category(books: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    Filter books by category (handles normalized capitalization and partial match).
    """
    if not category or not isinstance(category, str):
        return books

    target = normalize_category(category).lower()
    raw_target = category.strip().lower()

    results = []
    for b in books:
        b_cat = b.get("category", "").lower()
        if b_cat == target or b_cat == raw_target or raw_target in b_cat or target in b_cat:
            results.append(b)
    return results


def recommend_next_book(books: List[Dict[str, Any]], category: Optional[str] = None) -> Dict[str, Any]:
    """
    Deterministic recommendation logic based on stored list data:
    1. Filter candidates to status == 'unread'
    2. If category specified, filter to requested category
    3. Choose earlier added book (FIFO)
    4. Exclude completed books
    Returns dictionary with recommendation details.
    """
    if not books:
        return {
            "success": False,
            "book": None,
            "message": "Your reading list is empty. Add a book first."
        }

    unread_books = [b for b in books if b.get("status") == STATUS_UNREAD]

    if not unread_books:
        return {
            "success": False,
            "book": None,
            "message": "You have read all books on your reading list! Add some new unread books to get recommendations."
        }

    # Filter by category if requested
    if category and category.strip():
        norm_cat = normalize_category(category)
        matching_unread = filter_by_category(unread_books, category)
        if matching_unread:
            chosen = matching_unread[0]  # FIFO order
            return {
                "success": True,
                "book": chosen,
                "reason": f"Chosen because it is currently unread and belongs to your '{chosen['category']}' category.",
                "message": f"I recommend reading '{chosen['title']}' next ({chosen['category']})."
            }
        else:
            # Fallback to any unread book, explaining that no unread book matched requested category
            chosen = unread_books[0]
            return {
                "success": True,
                "book": chosen,
                "reason": f"No unread books found in category '{norm_cat}'. Recommending earliest unread book overall.",
                "message": f"No unread books in '{norm_cat}'. I recommend starting '{chosen['title']}' ({chosen['category']}) next."
            }

    # No category specified: pick earliest unread book
    chosen = unread_books[0]
    return {
        "success": True,
        "book": chosen,
        "reason": f"Chosen because it is currently unread in your '{chosen['category']}' category.",
        "message": f"I recommend reading '{chosen['title']}' next ({chosen['category']})."
    }


def get_statistics(books: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate real statistics from stored memory.
    """
    total = len(books)
    unread = sum(1 for b in books if b.get("status") == STATUS_UNREAD)
    reading = sum(1 for b in books if b.get("status") == STATUS_READING)
    completed = sum(1 for b in books if b.get("status") == STATUS_COMPLETED)

    by_category: Dict[str, int] = {}
    for b in books:
        cat = b.get("category", "General")
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total": total,
        "unread": unread,
        "reading": reading,
        "completed": completed,
        "by_category": by_category
    }

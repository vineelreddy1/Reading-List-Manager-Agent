import datetime
import uuid
from typing import Dict, Any, Optional, List
from memory import ReadingListMemory
from reading_logic import (
    normalize_category,
    is_duplicate_title,
    find_book_by_title,
    search_books as logic_search_books,
    filter_by_category as logic_filter_by_category,
    recommend_next_book,
    get_statistics as logic_get_statistics
)
from config import STATUS_UNREAD, STATUS_COMPLETED, STATUS_READING


class ReadingListTools:
    """
    Interface exposing structured agent tools backed by ReadingListMemory and pure Python logic.
    """

    def __init__(self, memory: Optional[ReadingListMemory] = None):
        self.memory = memory if memory is not None else ReadingListMemory()

    def add_book(self, title: str, category: str = "general") -> Dict[str, Any]:
        """
        Tool 1: Add a book to persistent reading list state.
        Handles missing input, category normalization, and duplicate detection.
        """
        if not title or not isinstance(title, str) or not title.strip():
            return {
                "success": False,
                "message": "Book title cannot be empty.",
                "title": "",
                "category": category
            }

        clean_title = title.strip()
        norm_category = normalize_category(category)

        # Check for duplicates case-insensitively
        books = self.memory.get_books()
        if is_duplicate_title(books, clean_title):
            return {
                "success": False,
                "title": clean_title,
                "category": norm_category,
                "message": f"'{clean_title}' is already in your reading list."
            }

        book = {
            "id": str(uuid.uuid4())[:8],
            "title": clean_title,
            "category": norm_category,
            "status": STATUS_UNREAD,
            "added_at": datetime.date.today().strftime("%Y-%m-%d")
        }

        self.memory.add_book(book)

        return {
            "success": True,
            "title": clean_title,
            "category": norm_category,
            "message": f"Added '{clean_title}' under {norm_category}."
        }

    def get_list(self) -> Dict[str, Any]:
        """
        Tool 2: Get current reading list.
        """
        books = self.memory.get_books()
        return {
            "success": True,
            "count": len(books),
            "books": books
        }

    def remove_book(self, title: str) -> Dict[str, Any]:
        """
        Remove a book by title from reading list.
        """
        if not title or not isinstance(title, str) or not title.strip():
            return {
                "success": False,
                "message": "Book title is required for removal."
            }

        clean_title = title.strip()
        books = self.memory.get_books()
        existing = find_book_by_title(books, clean_title)

        if not existing:
            return {
                "success": False,
                "message": f"'{clean_title}' isn't currently in your reading list."
            }

        removed = self.memory.remove_book(clean_title)
        if removed:
            return {
                "success": True,
                "title": existing["title"],
                "message": f"Removed '{existing['title']}' from your reading list."
            }
        return {
            "success": False,
            "message": f"Could not remove '{clean_title}'."
        }

    def mark_as_read(self, title: str, status: str = STATUS_COMPLETED) -> Dict[str, Any]:
        """
        Mark a book as completed (or another valid status like 'reading').
        """
        if not title or not isinstance(title, str) or not title.strip():
            return {
                "success": False,
                "message": "Book title is required."
            }

        clean_title = title.strip()
        books = self.memory.get_books()
        existing = find_book_by_title(books, clean_title)

        if not existing:
            return {
                "success": False,
                "message": f"'{clean_title}' isn't currently in your reading list."
            }

        target_status = STATUS_COMPLETED if status not in [STATUS_UNREAD, STATUS_READING, STATUS_COMPLETED] else status
        updated = self.memory.update_book(clean_title, {"status": target_status})

        if updated:
            return {
                "success": True,
                "title": existing["title"],
                "status": target_status,
                "message": f"I marked '{existing['title']}' as {target_status}."
            }
        return {
            "success": False,
            "message": f"Failed to update status for '{clean_title}'."
        }

    def search_books(self, query: str) -> Dict[str, Any]:
        """
        Search books case-insensitively.
        """
        if not query or not isinstance(query, str):
            query = ""
        books = self.memory.get_books()
        results = logic_search_books(books, query)
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "books": results
        }

    def filter_by_category(self, category: str) -> Dict[str, Any]:
        """
        Filter books by category.
        """
        if not category or not isinstance(category, str):
            category = ""
        books = self.memory.get_books()
        norm_cat = normalize_category(category) if category else ""
        results = logic_filter_by_category(books, category)
        return {
            "success": True,
            "category": norm_cat or category,
            "count": len(results),
            "books": results
        }

    def recommend_next(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend what to read next based ONLY on stored list data.
        """
        books = self.memory.get_books()
        return recommend_next_book(books, category)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics summary of current reading list.
        """
        books = self.memory.get_books()
        stats = logic_get_statistics(books)
        return {
            "success": True,
            "statistics": stats
        }

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DATA_FILE, DATA_DIR


class ReadingListMemory:
    """
    Persistent memory manager for Reading List Manager Agent.
    Handles reading, writing, updating, and error recovery for reading list JSON storage.
    """

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = Path(file_path) if file_path else DATA_FILE
        self._ensure_storage_directory()
        self.books: List[Dict[str, Any]] = self.load()

    def _ensure_storage_directory(self) -> None:
        """Ensure parent folder exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> List[Dict[str, Any]]:
        """Load books from JSON file. Returns empty list if file doesn't exist or is corrupted."""
        if not self.file_path.exists():
            return []
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, IOError, OSError) as e:
            # Failure recovery: fallback to empty list without crashing
            print(f"[Memory Warning] Could not parse memory file ({e}). Starting with empty list.")
            return []

    def save(self) -> bool:
        """Persist current book list to JSON storage."""
        try:
            self._ensure_storage_directory()
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.books, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"[Memory Error] Failed to write to memory file: {e}")
            return False

    def get_books(self) -> List[Dict[str, Any]]:
        """Return shallow copy of books."""
        return list(self.books)

    def add_book(self, book: Dict[str, Any]) -> None:
        """Add a new book item and persist."""
        self.books.append(book)
        self.save()

    def update_book(self, title: str, updates: Dict[str, Any]) -> bool:
        """Update fields for a book matching title (case-insensitive)."""
        target = title.strip().lower()
        for book in self.books:
            if book.get("title", "").strip().lower() == target:
                book.update(updates)
                self.save()
                return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book matching title (case-insensitive)."""
        target = title.strip().lower()
        initial_count = len(self.books)
        self.books = [b for b in self.books if b.get("title", "").strip().lower() != target]
        if len(self.books) < initial_count:
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Clear all books from memory and disk."""
        self.books = []
        self.save()

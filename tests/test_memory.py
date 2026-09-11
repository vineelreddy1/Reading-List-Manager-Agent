import os
import json
import tempfile
from pathlib import Path
import pytest
from memory import ReadingListMemory


def test_memory_persistence():
    """Test 10: Memory saves to JSON file and restores across restarts."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        mem1 = ReadingListMemory(file_path=tmp_path)
        mem1.clear()
        mem1.add_book({"title": "Atomic Habits", "category": "self-help", "status": "unread"})
        mem1.add_book({"title": "Deep Work", "category": "productivity", "status": "unread"})

        assert len(mem1.get_books()) == 2

        # Instantiate brand new memory pointing to same file
        mem2 = ReadingListMemory(file_path=tmp_path)
        restored = mem2.get_books()

        assert len(restored) == 2
        assert restored[0]["title"] == "Atomic Habits"
        assert restored[1]["title"] == "Deep Work"
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def test_memory_corrupted_json_recovery():
    """Test 15: Invalid/corrupted JSON recovers gracefully without crashing."""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
        tmp.write("CORRUPTED_JSON_DATA{{{")
        tmp_path = Path(tmp.name)

    try:
        mem = ReadingListMemory(file_path=tmp_path)
        books = mem.get_books()
        assert books == []  # Fallback to empty list without crashing
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)

import os
import tempfile
from pathlib import Path
import pytest
from memory import ReadingListMemory
from tools import ReadingListTools


@pytest.fixture
def temp_tools():
    """Create isolated ReadingListTools instance backed by a temporary file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    memory = ReadingListMemory(file_path=tmp_path)
    memory.clear()
    tools = ReadingListTools(memory=memory)
    yield tools
    if tmp_path.exists():
        os.remove(tmp_path)


def test_add_book(temp_tools):
    """Test 1 & 14: Add book tool with category and category fallback."""
    res = temp_tools.add_book(title="Atomic Habits", category="self-help")
    assert res["success"] is True
    assert res["title"] == "Atomic Habits"
    assert res["category"] == "self-help"

    # Test missing category defaults to general
    res2 = temp_tools.add_book(title="General Knowledge", category="")
    assert res2["success"] is True
    assert res2["category"] == "general"


def test_add_multiple_books(temp_tools):
    """Test 2: Adding multiple books."""
    temp_tools.add_book("Atomic Habits", "self-help")
    temp_tools.add_book("Deep Work", "productivity")
    temp_tools.add_book("Hands-On Machine Learning", "AI/ML")

    lst = temp_tools.get_list()
    assert lst["count"] == 3


def test_duplicate_book(temp_tools):
    """Test 3: Duplicate detection tool returns message without duplicating."""
    temp_tools.add_book("Atomic Habits", "self-help")
    dup_res = temp_tools.add_book("atomic habits", "self-help")

    assert dup_res["success"] is False
    assert "already in your reading list" in dup_res["message"].lower()

    lst = temp_tools.get_list()
    assert lst["count"] == 1


def test_get_list(temp_tools):
    """Test 5: get_list tool."""
    temp_tools.add_book("Clean Code", "programming")
    lst = temp_tools.get_list()
    assert lst["success"] is True
    assert len(lst["books"]) == 1
    assert lst["books"][0]["title"] == "Clean Code"


def test_remove_book(temp_tools):
    """Test 8: remove_book tool (existing and non-existent)."""
    temp_tools.add_book("Deep Work", "productivity")

    # Remove existing
    rem_res = temp_tools.remove_book("Deep Work")
    assert rem_res["success"] is True
    assert "Removed" in rem_res["message"]

    # Remove non-existing
    rem_no = temp_tools.remove_book("Deep Work")
    assert rem_no["success"] is False
    assert "isn't currently in your reading list" in rem_no["message"]


def test_mark_as_read(temp_tools):
    """Test 9: mark_as_read tool."""
    temp_tools.add_book("Atomic Habits", "self-help")
    mark_res = temp_tools.mark_as_read("Atomic Habits")

    assert mark_res["success"] is True
    assert mark_res["status"] == "completed"

    # Verify status in memory
    lst = temp_tools.get_list()
    assert lst["books"][0]["status"] == "completed"


def test_missing_title_or_invalid_input(temp_tools):
    """Test 13 & 15: Missing title and invalid input handling."""
    res_empty = temp_tools.add_book("", "self-help")
    assert res_empty["success"] is False
    assert "empty" in res_empty["message"].lower()

    res_none = temp_tools.add_book(None, "self-help")
    assert res_none["success"] is False

    rem_empty = temp_tools.remove_book("")
    assert rem_empty["success"] is False

import os
import tempfile
from pathlib import Path
import pytest
from memory import ReadingListMemory
from agent import ReadingListAgent


@pytest.fixture
def temp_agent():
    """Create isolated ReadingListAgent instance with temporary storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    memory = ReadingListMemory(file_path=tmp_path)
    memory.clear()
    agent = ReadingListAgent(memory=memory)
    yield agent
    if tmp_path.exists():
        os.remove(tmp_path)


def test_agent_add_and_list_flow(temp_agent):
    """Test Turn 1 & Turn 2: Add books and list them via natural language."""
    # Turn 1: Add book
    res1 = temp_agent.process_query("Add Atomic Habits under self-help.")
    assert "Atomic Habits" in res1["final_answer"]
    assert "[AGENT PLAN]" in res1["trace"]
    assert "[TOOL CALL]" in res1["trace"]
    assert "add_book" in res1["trace"]
    assert res1["memory_count"] == 1

    # Turn 2: View list
    res2 = temp_agent.process_query("Show my reading list.")
    assert "Atomic Habits" in res2["final_answer"]
    assert "get_list" in res2["trace"]


def test_agent_multi_turn_memory_accumulation(temp_agent):
    """Test multi-turn memory accumulation across 4 turns."""
    temp_agent.process_query("Add Atomic Habits under self-help.")
    temp_agent.process_query("Put Deep Work under productivity.")
    temp_agent.process_query("Add The Psychology of Money under finance.")

    res = temp_agent.process_query("What books do I have?")
    assert res["memory_count"] == 3
    assert "Atomic Habits" in res["final_answer"]
    assert "Deep Work" in res["final_answer"]
    assert "The Psychology of Money" in res["final_answer"]


def test_agent_multi_step_filter_and_recommend(temp_agent):
    """Test multi-step execution: filter by AI and recommend."""
    temp_agent.process_query("Add Hands-On Machine Learning under AI/ML.")
    temp_agent.process_query("Add Deep Learning under AI/ML.")
    temp_agent.process_query("Add Deep Work under productivity.")

    res = temp_agent.process_query("Show me my AI books and tell me which one I should read.")
    assert "[AGENT DECISION]" in res["trace"]
    assert "recommend_next" in res["trace"]
    assert "Hands-On Machine Learning" in res["final_answer"] or "Deep Learning" in res["final_answer"]


def test_agent_recommendation_empty_state(temp_agent):
    """Test empty state recommendation query does not invent books."""
    res = temp_agent.process_query("What should I read next?")
    assert "empty" in res["final_answer"].lower()
    assert "Atomic Habits" not in res["final_answer"]

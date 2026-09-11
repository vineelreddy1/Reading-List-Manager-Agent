import json
from pathlib import Path

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Day 8 — Reading List Manager Agent Demo\n",
    "\n",
    "This notebook demonstrates the **Reading List Manager Agent** executing real ReAct agentic loops across **7 distinct scenarios** and proving cross-turn persistent memory.\n",
    "\n",
    "### Agent Architecture:\n",
    "USER → AGENT PLAN → TOOL CALL → TOOL RESULT → MEMORY → AGENT DECISION → FINAL RESPONSE"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys\n",
    "from pathlib import Path\n",
    "import tempfile\n",
    "\n",
    "# Ensure local modules are in path\n",
    "sys.path.insert(0, str(Path.cwd().parent))\n",
    "\n",
    "from memory import ReadingListMemory\n",
    "from agent import ReadingListAgent\n",
    "\n",
    "# Create fresh temporary memory file for clean demo\n",
    "demo_file = Path.cwd() / 'demo_reading_list.json'\n",
    "if demo_file.exists():\n",
    "    demo_file.unlink()\n",
    "\n",
    "memory = ReadingListMemory(file_path=demo_file)\n",
    "agent = ReadingListAgent(memory=memory)\n",
    "print('[OK] Agent initialized with persistent memory file:', demo_file)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 1 — ADD BOOK\n",
    "User: *\"Add Atomic Habits under self-help.\"*"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res1 = agent.process_query('Add Atomic Habits under self-help.')\n",
    "print(res1['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 2 — ADD MORE BOOKS\n",
    "Adding:\n",
    "- *Deep Work* — productivity\n",
    "- *Hands-On Machine Learning* — AI/ML\n",
    "- *The Psychology of Money* — finance\n",
    "- *Harry Potter* — fiction"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "books_to_add = [\n",
    "    'Put Deep Work under productivity.',\n",
    "    'Add Hands-On Machine Learning under AI/ML.',\n",
    "    'Add The Psychology of Money under finance.',\n",
    "    'Add Harry Potter under fiction.'\n",
    "]\n",
    "\n",
    "for query in books_to_add:\n",
    "    r = agent.process_query(query)\n",
    "    print(f\"[ADDED] {r['final_answer']}\")\n",
    "\n",
    "print(f\"\\n[OK] Total items currently in persistent memory: {len(memory.get_books())}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 3 — VIEW READING LIST\n",
    "User: *\"Show my reading list.\"*"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res3 = agent.process_query('Show my reading list.')\n",
    "print(res3['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 4 — FILTER BY CATEGORY\n",
    "User: *\"Show my AI/ML books.\"*"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res4 = agent.process_query('Show my AI/ML books.')\n",
    "print(res4['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 5 — SEARCH\n",
    "User: *\"Do I have a book containing 'Money'?\"*"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res5 = agent.process_query(\"Do I have a book containing 'Money'?\")\n",
    "print(res5['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 6 — MARK BOOK AS COMPLETED\n",
    "User: *\"I finished Atomic Habits.\"*"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res6 = agent.process_query('I finished Atomic Habits.')\n",
    "print(res6['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## SCENARIO 7 — RECOMMENDATION LOGIC\n",
    "User: *\"What should I read next?\"*\n",
    "\n",
    "*Expected logic:* Agent calls `get_list()`, excludes completed books (Atomic Habits), prioritizes earliest unread book (Deep Work), and responds."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "res7 = agent.process_query('What should I read next?')\n",
    "print(res7['trace'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## MULTI-TURN CROSS-TURN MEMORY DEMONSTRATION\n",
    "Demonstrating memory state recovery across independent turns:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Turn 4 check: Count stored books\n",
    "res_count = agent.process_query('How many books are on my list?')\n",
    "print('Turn 4 Query Result:')\n",
    "print(res_count['final_answer'])\n",
    "\n",
    "# Turn 5 check: Retrieve AI books specifically\n",
    "res_ai = agent.process_query('Which ones are AI/ML?')\n",
    "print('\\nTurn 5 Query Result:')\n",
    "print(res_ai['final_answer'])\n",
    "\n",
    "# Restart Agent to prove JSON persistence on disk\n",
    "new_agent_instance = ReadingListAgent(memory=ReadingListMemory(file_path=demo_file))\n",
    "res_restart = new_agent_instance.process_query('Show my reading list.')\n",
    "print('\\nState Recovered After Agent Instance Restart:')\n",
    "print(res_restart['final_answer'])"
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

notebook_path = Path.cwd() / "notebook" / "reading_list_demo.ipynb"
notebook_path.parent.mkdir(parents=True, exist_ok=True)
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=2)

print(f"Created notebook at {notebook_path}")

# Reading List Manager Agent — Day 8

> **Part of the "30 AI Agent Projects in 30 Days" Series**

An autonomous AI Reading List Agent that manages personal reading lists, categorizes books, performs natural-language search & filtering, enforces duplicate prevention, persists state across sessions in JSON storage, and executes deterministic recommendations based strictly on stored memory data.

---

## 🎯 Objective

Build a **REAL AI Agent** for reading list management. The system operates via a transparent **ReAct (Reasoning + Acting)** execution loop:

```
USER
  ↓
AGENT PLAN
  ↓
TOOL CALL
  ↓
OBSERVE (TOOL RESULT)
  ↓
DECIDE (MULTI-STEP DECISION)
  ↓
MEMORY UPDATE
  ↓
FINAL ANSWER
```

---

## ✨ Key Features

- **Tool-Driven Execution**: 2 mandatory tools (`add_book`, `get_list`) + 6 portfolio tools (`remove_book`, `mark_as_read`, `search_books`, `filter_by_category`, `recommend_next`, `get_statistics`).
- **Persistent JSON State**: Remembers reading list state across conversation turns, application restarts, and crashes (`data/reading_list.json`).
- **Case-Insensitive Duplicate Detection**: Prevents duplicate book titles regardless of casing (`Atomic Habits` == `atomic habits`).
- **Category Normalization**: Handles standard categories (`AI/ML`, `self-help`, `productivity`, `finance`, etc.) while seamlessly preserving custom user categories.
- **Deterministic Recommendation Engine**: Recommends what to read next based **ONLY** on stored unread books, requested category, FIFO addition order, and excluding completed books. Never invents books.
- **Transparent Execution Trace**: Formatted output block displaying `[USER]`, `[AGENT PLAN]`, `[TOOL CALL]`, `[TOOL RESULT]`, `[MEMORY]`, `[AGENT DECISION]`, and `[FINAL ANSWER]`.
- **Dual NLU Architecture**: Supports Gemini/OpenAI API when keys are configured, with fallback to an offline regex/rule parser.

---

## 🏗️ Architecture

```
                    USER
                      ↓
                    AGENT
                      ↓
                    PLAN
                      ↓
          ┌───────────┼────────────┐
          ↓           ↓            ↓
      add_book    get_list     search_books
          ↓           ↓            ↓
          └───────────┼────────────┘
                      ↓
                    MEMORY
                      ↓
                READING STATE
                      ↓
             ┌────────┴─────────┐
             ↓                  ↓
        FILTER/SEARCH      STATUS UPDATE
             ↓                  ↓
             └────────┬─────────┘
                      ↓
                 AGENT DECISION
                      ↓
                RECOMMENDATION
                      ↓
                FINAL RESPONSE
```

---

## 🛠️ Tools Reference

| Tool Name | Type | Description | Return Payload |
|---|---|---|---|
| `add_book(title, category)` | **Required** | Adds a book to storage with category normalization & duplicate check. | `{"success": true, "title": "...", "category": "...", "message": "..."}` |
| `get_list()` | **Required** | Retrieves current stored reading list. | `{"success": true, "count": 2, "books": [...]}` |
| `remove_book(title)` | Portfolio | Removes a book by title. | `{"success": true/false, "message": "..."}` |
| `mark_as_read(title)` | Portfolio | Updates status to `completed`. | `{"success": true/false, "status": "completed", "message": "..."}` |
| `search_books(query)` | Portfolio | Case-insensitive search across title, category, status. | `{"success": true, "count": 1, "books": [...]}` |
| `filter_by_category(category)` | Portfolio | Filters list by normalized category. | `{"success": true, "category": "...", "books": [...]}` |
| `recommend_next(category)` | Portfolio | Selects next book to read based on unread status & FIFO order. | `{"success": true/false, "book": {...}, "message": "..."}` |
| `get_statistics()` | Portfolio | Calculates book counts by status and category. | `{"success": true, "statistics": {...}}` |

---

## 🧠 Memory & Persistent Storage

- **In-Memory Cache**: `ReadingListMemory` maintains a memory-resident list during active execution.
- **Disk Persistence**: Every state mutation (`add_book`, `update_book`, `remove_book`, `clear`) triggers an atomic save to `data/reading_list.json`.
- **Data Model**:
  ```json
  {
    "id": "a1b2c3d4",
    "title": "Atomic Habits",
    "category": "self-help",
    "status": "unread",
    "added_at": "2026-09-11"
  }
  ```

---

## 💡 Recommendation Logic

The recommendation engine is written in pure Python:
1. Filters stored books for `status == "unread"`.
2. If user requested a specific category (e.g., `"finance"`), filters unread books to that category.
3. Chooses the earliest added book (FIFO order).
4. Strictly excludes books with `status == "completed"`.
5. If the reading list is empty or no unread books remain, returns a honest message without hallucinating books.

---

## ⚠️ Honest Failure & Resolution

During initial development of `run_notebook.py` on Windows 11, the script failed with:
`UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'` when outputting terminal logs.

**Root Cause**: The Windows default console encoding (`cp1256`/`cp437`) does not support Unicode checkmark characters (`✓`) when printed directly through standard stdout without UTF-8 environment overrides.

**Fix**: Replaced raw Unicode characters with standard ASCII markers (`[OK]`, `[ADDED]`) and set explicit `encoding="utf-8"` when reading and writing JSON files.

---

## 🚀 Installation & Running

### 1. Clone & Setup
```bash
cd reading-list-agent
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for API mode)
```bash
cp .env.example .env
# Add GEMINI_API_KEY or OPENAI_API_KEY if desired
```

### 3. Run Automated Tests
```bash
python -m pytest tests -v
```

### 4. Run Gradio Web UI
```bash
python app.py
```
Open browser at `http://127.0.0.1:7860`.

---

## 📓 Notebook Demo

Run the interactive demonstration covering all 7 required scenarios:
```bash
python run_notebook.py
```
View the populated notebook at [reading_list_demo.ipynb](notebook/reading_list_demo.ipynb).

---

## 💬 Example Interaction

```text
[USER]
Add Atomic Habits under self-help.

[AGENT PLAN]
Add the requested book 'Atomic Habits' under category 'self-help' to persistent reading list.

[TOOL CALL]
add_book(title="Atomic Habits", category="self-help")

[TOOL RESULT]
Added 'Atomic Habits' under self-help.

[MEMORY]
1 book(s) stored in persistent list.

[FINAL ANSWER]
Added 'Atomic Habits' to your self-help reading list.
```

---

## 📌 Limitations

1. **Local JSON Storage**: Suitable for single-user desktop portfolios. Production deployment would benefit from PostgreSQL or SQLite.
2. **Metadata Fetching**: Does not currently query external ISBN databases (like Open Library) for page counts or authors.

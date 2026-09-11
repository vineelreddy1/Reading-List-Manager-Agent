# Viva QA Guide — Reading List Manager Agent (Day 8)

### 1. What is an AI agent?
An AI agent is an autonomous software system that receives user requests, forms an execution plan, selects and invokes tools, observes environment state, makes decisions based on results, and updates persistent memory to fulfill goals.

### 2. Why is this project different from a chatbot?
A simple chatbot relies solely on a direct prompt-to-response loop (`USER → LLM → RESPONSE`) without external state or action capabilities. This agent executes a structured ReAct loop (`USER → PLAN → TOOL → OBSERVE → DECIDE → MEMORY → RESPONSE`), interacting directly with state storage.

### 3. What are the two required tools?
The two mandatory tools are:
1. `add_book(title, category)` — Adds a new book to persistent state.
2. `get_list()` — Retrieves stored reading list items.

### 4. What does add_book() do?
It validates the title, normalizes the category capitalization, performs case-insensitive duplicate checking, assigns a unique ID and addition timestamp (`added_at`), sets `status="unread"`, and saves the item to JSON storage.

### 5. What does get_list() do?
It retrieves all book records stored in persistent memory and returns them as a structured list with titles, categories, and statuses.

### 6. How does memory work?
Memory is managed by `ReadingListMemory`. It keeps an active in-memory list during execution and automatically reads from/writes to `data/reading_list.json` whenever books are added, updated, or removed.

### 7. What information is stored?
Each book record contains:
- `id`: unique identifier string
- `title`: book title string
- `category`: normalized category string
- `status`: string (`unread`, `reading`, or `completed`)
- `added_at`: ISO date string (`YYYY-MM-DD`)

### 8. Why is persistent memory useful?
Without persistent memory, all reading list state would be lost when the Python script or server restarts. Persistent memory ensures data survives across turns, sessions, and system restarts.

### 9. How does search work?
`search_books(query)` performs a case-insensitive substring search across `title`, `category`, and `status` fields, returning matching book objects.

### 10. How does category filtering work?
`filter_by_category(category)` normalizes the target category (e.g. `"ai"` → `"AI/ML"`) and matches it against stored book category fields.

### 11. How are duplicates detected?
Duplicate titles are detected case-insensitively using `title.strip().lower()`. If `"Atomic Habits"` is already saved, trying to add `"atomic habits"` returns a duplicate warning message without adding a second record.

### 12. How does mark_as_read() work?
It searches for a book matching the title (case-insensitive) and updates its `status` field to `"completed"` in memory and disk storage.

### 13. How does the recommendation system work?
It uses deterministic Python logic:
1. Filters stored books for `status == "unread"`.
2. Optionally filters by requested category.
3. Selects the earliest added book (FIFO order).
4. Strictly excludes completed books.

### 14. Why shouldn't the agent invent books?
Hallucinating books breaks user trust and corrupts personal list management. Recommendations must come strictly from the user's actual stored list.

### 15. What happens if the list is empty?
If a user asks *"What should I read next?"* when the list is empty, the agent returns an honest message: *"Your reading list is empty. Add a book first."*

### 16. Why should deterministic filtering be done in Python?
Python code is 100% deterministic, exact, fast, and free of LLM hallucinations. LLMs can miscount or skip items when parsing large arrays, whereas Python handles data operations reliably.

### 17. What role does the LLM play?
The LLM (or NLU parser) converts free-form user natural language into structured tool calls and arguments (`tool_name`, `args`).

### 18. How does the agent decide which tool to use?
The NLU layer evaluates the user prompt against intent rules/JSON schemas, mapping intent keywords (e.g. *"add"*, *"show"*, *"recommend"*, *"finished"*) to corresponding Python functions.

### 19. Explain one complete multi-step execution.
When the user asks *"Show me my AI books and tell me which one I should read"*:
1. **Plan**: Filter list by `"AI/ML"`, then choose recommendation.
2. **Tool Call 1**: `filter_by_category("AI/ML")` → Returns 2 unread books.
3. **Decision**: Select unread book from filtered results.
4. **Tool Call 2**: `recommend_next("AI/ML")` → Returns earliest unread AI book.
5. **Final Response**: *"You have 2 AI/ML books. I recommend starting with 'Hands-On Machine Learning'."*

### 20. What makes this project agentic?
The presence of explicit planning, tool selection, observation feedback, multi-step decision reasoning, state persistence, and natural-language goal execution makes it a true AI agent.

### 21. What would you improve in version 2?
1. Integrate an external API (like Open Library) to automatically pull author names, book covers, and page counts.
2. Upgrade storage to SQLite or Vector DB for semantic book search.
3. Add reading progress tracking (e.g. percentage complete, pages read per day).

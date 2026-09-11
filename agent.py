import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from memory import ReadingListMemory
from tools import ReadingListTools
from reading_logic import normalize_category

# Try importing LLM clients if available
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ReadingListAgent:
    """
    Agentic Reading List Manager implementing the ReAct loop:
    User Query -> Agent Plan -> Tool Call -> Observation -> Decision -> Memory Update -> Final Response.
    """

    def __init__(self, memory: Optional[ReadingListMemory] = None):
        self.memory = memory if memory is not None else ReadingListMemory()
        self.tools = ReadingListTools(memory=self.memory)

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process user query through the Agent loop.
        Returns dictionary containing final_answer, formatted_trace, steps, and updated memory status.
        """
        if not user_query or not user_query.strip():
            return {
                "final_answer": "Please provide a valid request.",
                "trace": "[USER]\n\n[FINAL ANSWER]\nPlease provide a valid request.",
                "steps": []
            }

        clean_query = user_query.strip()
        trace_blocks = [f"[USER]\n{clean_query}"]
        steps = []

        # 1. Determine Plan & Tool Call Intent
        plan, intent = self._plan_and_parse_intent(clean_query)
        trace_blocks.append(f"[AGENT PLAN]\n{plan}")

        # 2. Execute primary tool call
        tool_name = intent.get("tool")
        args = intent.get("args", {})

        tool_call_str = self._format_tool_call(tool_name, args)
        trace_blocks.append(f"[TOOL CALL]\n{tool_call_str}")

        observation = self._execute_tool(tool_name, args)
        obs_str = self._format_observation(tool_name, observation)
        trace_blocks.append(f"[TOOL RESULT]\n{obs_str}")

        # Update steps log
        steps.append({
            "plan": plan,
            "tool": tool_name,
            "args": args,
            "result": observation
        })

        # Check for multi-step workflow (e.g., filter + recommend)
        multi_step = intent.get("next_action")
        if multi_step:
            decision_msg = multi_step.get("decision_reason", "Proceeding to secondary action based on filter results.")
            trace_blocks.append(f"[AGENT DECISION]\n{decision_msg}")

            sec_tool_name = multi_step.get("tool")
            sec_args = multi_step.get("args", {})
            sec_call_str = self._format_tool_call(sec_tool_name, sec_args)
            trace_blocks.append(f"[TOOL CALL]\n{sec_call_str}")

            sec_observation = self._execute_tool(sec_tool_name, sec_args)
            sec_obs_str = self._format_observation(sec_tool_name, sec_observation)
            trace_blocks.append(f"[TOOL RESULT]\n{sec_obs_str}")

            steps.append({
                "plan": decision_msg,
                "tool": sec_tool_name,
                "args": sec_args,
                "result": sec_observation
            })

            # Synthesize answer from both tools
            final_answer = self._synthesize_multi_step_response(clean_query, observation, sec_observation)
        else:
            # Memory state snapshot for trace
            current_book_count = len(self.memory.get_books())
            trace_blocks.append(f"[MEMORY]\n{current_book_count} book(s) stored in persistent list.")
            final_answer = self._synthesize_single_step_response(clean_query, tool_name, args, observation)

        trace_blocks.append(f"[FINAL ANSWER]\n{final_answer}")
        full_trace = "\n\n".join(trace_blocks)

        return {
            "final_answer": final_answer,
            "trace": full_trace,
            "steps": steps,
            "memory_count": len(self.memory.get_books())
        }

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool by name with arguments."""
        if tool_name == "add_book":
            return self.tools.add_book(title=args.get("title", ""), category=args.get("category", "general"))
        elif tool_name == "get_list":
            return self.tools.get_list()
        elif tool_name == "remove_book":
            return self.tools.remove_book(title=args.get("title", ""))
        elif tool_name == "mark_as_read":
            return self.tools.mark_as_read(title=args.get("title", ""))
        elif tool_name == "search_books":
            return self.tools.search_books(query=args.get("query", ""))
        elif tool_name == "filter_by_category":
            return self.tools.filter_by_category(category=args.get("category", ""))
        elif tool_name == "recommend_next":
            return self.tools.recommend_next(category=args.get("category"))
        elif tool_name == "get_statistics":
            return self.tools.get_statistics()
        else:
            return {"success": False, "message": f"Unknown tool '{tool_name}'"}

    def _plan_and_parse_intent(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Convert natural language query to AGENT PLAN and tool parameters.
        Tries LLM first if API key is present, falls back to deterministic NLP regex parser.
        """
        # Try LLM if available and configured
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if GENAI_AVAILABLE and gemini_key:
            try:
                plan, intent = self._llm_parse_gemini(query, gemini_key)
                if intent:
                    return plan, intent
            except Exception as e:
                print(f"[Agent warning] Gemini call failed: {e}. Using deterministic parser.")

        if OPENAI_AVAILABLE and openai_key:
            try:
                plan, intent = self._llm_parse_openai(query, openai_key)
                if intent:
                    return plan, intent
            except Exception as e:
                print(f"[Agent warning] OpenAI call failed: {e}. Using deterministic parser.")

        # Deterministic Rule/Regex Parser
        return self._deterministic_nlp_parse(query)

    def _deterministic_nlp_parse(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        High precision natural-language parser covering all required agent intents.
        """
        q = query.strip()
        ql = q.lower()

        # Multi-step query: "Show me my AI books and tell me which one I should read."
        if ("show" in ql or "filter" in ql) and ("recommend" in ql or "should i read" in ql or "which one" in ql):
            category = "AI/ML" if ("ai" in ql or "ml" in ql) else "general"
            for c in ["productivity", "finance", "self-help", "fiction", "biography", "science", "business", "technology", "programming"]:
                if c in ql:
                    category = c
                    break
            plan = f"Retrieve reading list, filter books related to '{category}', then choose a recommendation from the filtered results."
            intent = {
                "tool": "filter_by_category",
                "args": {"category": category},
                "next_action": {
                    "decision_reason": f"Need to select an unread book recommendation from the filtered {category} category.",
                    "tool": "recommend_next",
                    "args": {"category": category}
                }
            }
            return plan, intent

        # Recommendation: "What should I read next?" / "Recommend a book"
        if any(p in ql for p in ["what should i read", "recommend", "which book should i read", "next book"]):
            category = None
            for c in ["ai/ml", "ai", "ml", "productivity", "finance", "self-help", "self help", "fiction", "biography", "science", "business", "technology", "programming"]:
                if c in ql:
                    category = c
                    break
            plan = "Retrieve stored reading list, inspect books, exclude completed books, and select an unread recommendation."
            intent = {"tool": "recommend_next", "args": {"category": category}}
            return plan, intent

        # Add book: "Add Atomic Habits under self-help" / "Add Atomic Habits" / "Put Deep Work under productivity"
        add_patterns = [
            r"^(?:add|put)\s+(?:the\s+book\s+)?[\"']?(.+?)[\"']?\s+under\s+[\"']?(.+?)[\"']?$",
            r"^(?:add|put)\s+(?:the\s+book\s+)?[\"']?(.+?)[\"']?\s+to\s+my\s+reading\s+list\s+under\s+[\"']?(.+?)[\"']?$",
            r"^(?:add|put)\s+(?:the\s+book\s+)?[\"']?(.+?)[\"']?\s+(?:in|to|on)\s+(?:my\s+reading\s+list|category)\s*[\"']?([^\"']*)[\"']?$",
            r"^(?:add|put)\s+(?:the\s+book\s+)?[\"']?(.+?)[\"']?$"
        ]

        for pat in add_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                groups = m.groups()
                title = groups[0].strip()
                # Clean title if trailing words matched
                if " to my reading list" in title.lower():
                    title = re.sub(r"\s+to\s+my\s+reading\s+list.*", "", title, flags=re.IGNORECASE).strip()

                category = groups[1].strip() if len(groups) > 1 and groups[1] else "general"
                
                # Exclude tool verbs from title
                if title.lower() not in ["reading list", "books", "my list"]:
                    plan = f"Add the requested book '{title}' under category '{category}' to persistent reading list."
                    intent = {"tool": "add_book", "args": {"title": title, "category": category}}
                    return plan, intent

        # View List: "Show my reading list" / "What books do I have?" / "List books"
        if any(p in ql for p in ["show my reading list", "what books do i have", "show list", "view reading list", "list my books", "get list", "what books am i reading", "how many books"]):
            if "how many books" in ql:
                plan = "Query storage statistics to count books currently saved in memory."
                return plan, {"tool": "get_statistics", "args": {}}
            plan = "Retrieve all stored books from persistent reading list memory."
            return plan, {"tool": "get_list", "args": {}}

        # Complete Book: "I finished Atomic Habits" / "Mark Atomic Habits as completed"
        finish_patterns = [
            r"^(?:i\s+finished|i\s+have\s+read|finished|completed)\s+[\"']?(.+?)[\"']?$",
            r"^mark\s+[\"']?(.+?)[\"']?\s+as\s+(?:completed|read|finished)$"
        ]
        for pat in finish_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                plan = f"Update status of '{title}' to completed in persistent memory."
                intent = {"tool": "mark_as_read", "args": {"title": title}}
                return plan, intent

        # Remove Book: "Remove Deep Work" / "Delete Atomic Habits"
        remove_patterns = [
            r"^(?:remove|delete|drop)\s+[\"']?(.+?)[\"']?$"
        ]
        for pat in remove_patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                plan = f"Remove book '{title}' from persistent reading list."
                intent = {"tool": "remove_book", "args": {"title": title}}
                return plan, intent

        # Filter by Category: "Show my AI/ML books" / "Show me my finance books" / "Which books are unread?"
        if "unread" in ql:
            plan = "Filter reading list for books with status 'unread'."
            return plan, {"tool": "search_books", "args": {"query": "unread"}}

        if any(w in ql for w in ["books under", "books in", "show my", "show me my", "filter by"]):
            for c in ["ai/ml", "ai", "ml", "productivity", "finance", "self-help", "self help", "fiction", "biography", "science", "business", "technology", "programming"]:
                if c in ql:
                    plan = f"Filter stored reading list by category '{c}'."
                    return plan, {"tool": "filter_by_category", "args": {"category": c}}

        # Search: "Do I have a book containing 'Money'?" / "Search for AI"
        search_match = re.search(r"(?:containing|search\s+for|find)\s+[\"']?(.+?)[\"']?\??$", q, re.IGNORECASE)
        if search_match:
            query_term = search_match.group(1).strip()
            plan = f"Search reading list case-insensitively for term '{query_term}'."
            return plan, {"tool": "search_books", "args": {"query": query_term}}

        if "money" in ql:
            plan = "Search reading list for books containing 'Money'."
            return plan, {"tool": "search_books", "args": {"query": "Money"}}

        # Default Fallback: View List
        plan = "Retrieve current reading list from memory to fulfill user query."
        return plan, {"tool": "get_list", "args": {}}

    def _llm_parse_gemini(self, query: str, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """Parse query using Google Gemini Client."""
        client = genai.Client(api_key=api_key)
        prompt = f"""You are an AI Reading List Agent planner. Analyze the user request and map it to a tool call.
Available tools:
- add_book(title, category)
- get_list()
- remove_book(title)
- mark_as_read(title)
- search_books(query)
- filter_by_category(category)
- recommend_next(category)
- get_statistics()

User request: "{query}"

Return JSON ONLY with format:
{{
  "plan": "Short explanation of agent plan",
  "tool": "tool_name",
  "args": {{"arg_name": "value"}}
}}"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        data = json.loads(text)
        return data.get("plan", "Execute tool call"), {"tool": data.get("tool"), "args": data.get("args", {})}

    def _llm_parse_openai(self, query: str, api_key: str) -> Tuple[str, Dict[str, Any]]:
        """Parse query using OpenAI Client."""
        client = OpenAI(api_key=api_key)
        prompt = f"""You are an AI Reading List Agent planner. Analyze the user request and map it to a tool call.
Available tools:
- add_book(title, category)
- get_list()
- remove_book(title)
- mark_as_read(title)
- search_books(query)
- filter_by_category(category)
- recommend_next(category)
- get_statistics()

User request: "{query}"

Return JSON ONLY with format:
{{
  "plan": "Short explanation of agent plan",
  "tool": "tool_name",
  "args": {{"arg_name": "value"}}
}}"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("plan", "Execute tool call"), {"tool": data.get("tool"), "args": data.get("args", {})}

    def _format_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Format tool call string for trace display."""
        args_str = ", ".join(f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in args.items() if v is not None)
        return f"{tool_name}({args_str})"

    def _format_observation(self, tool_name: str, observation: Dict[str, Any]) -> str:
        """Format tool execution result for trace display."""
        if tool_name == "get_list":
            books = observation.get("books", [])
            if not books:
                return "0 books returned. Reading list is empty."
            titles = [f"'{b['title']}' ({b['category']}) - {b['status']}" for b in books]
            return f"{len(books)} book(s) returned:\n- " + "\n- ".join(titles)
        elif tool_name in ["filter_by_category", "search_books"]:
            books = observation.get("books", [])
            count = observation.get("count", 0)
            if not books:
                return f"{count} book(s) found."
            titles = [f"'{b['title']}' ({b['category']}) - {b['status']}" for b in books]
            return f"{count} book(s) found:\n- " + "\n- ".join(titles)
        elif tool_name == "recommend_next":
            if observation.get("success"):
                book = observation.get("book", {})
                return f"Recommended '{book.get('title')}' ({book.get('category')}). Reason: {observation.get('reason')}"
            return observation.get("message", "No recommendation available.")
        else:
            return observation.get("message", str(observation))

    def _synthesize_single_step_response(self, query: str, tool_name: str, args: Dict[str, Any], obs: Dict[str, Any]) -> str:
        """Synthesize natural language response for single tool call."""
        if tool_name == "add_book":
            if obs.get("success"):
                return f"Added '{obs.get('title')}' to your {obs.get('category')} reading list."
            return obs.get("message", "Could not add book.")

        elif tool_name == "get_list":
            books = obs.get("books", [])
            if not books:
                return "Your reading list is currently empty."
            lines = [f"{i+1}. {b['title']} — Category: {b['category']} | Status: {b['status']}" for i, b in enumerate(books)]
            return f"Here is your current reading list ({len(books)} books):\n" + "\n".join(lines)

        elif tool_name == "remove_book":
            return obs.get("message", "Processed removal request.")

        elif tool_name == "mark_as_read":
            return obs.get("message", "Updated book status.")

        elif tool_name == "search_books":
            books = obs.get("books", [])
            q = obs.get("query", "")
            if not books:
                return f"No books found matching '{q}'."
            lines = [f"- {b['title']} ({b['category']}) [{b['status']}]" for b in books]
            return f"Found {len(books)} book(s) matching '{q}':\n" + "\n".join(lines)

        elif tool_name == "filter_by_category":
            books = obs.get("books", [])
            cat = obs.get("category", "")
            if not books:
                return f"No books found in category '{cat}'."
            lines = [f"- {b['title']} [{b['status']}]" for b in books]
            return f"You have {len(books)} book(s) under '{cat}':\n" + "\n".join(lines)

        elif tool_name == "recommend_next":
            if obs.get("success"):
                book = obs.get("book", {})
                return f"Based on your stored list, I recommend reading '{book.get('title')}' next because it is currently unread in your {book.get('category')} category."
            return obs.get("message", "Your reading list is empty. Add a book first.")

        elif tool_name == "get_statistics":
            stats = obs.get("statistics", {})
            cat_lines = [f"  • {c}: {count}" for c, count in stats.get("by_category", {}).items()]
            return (
                f"Reading List Summary:\n"
                f"Total: {stats.get('total')}\n"
                f"Unread: {stats.get('unread')}\n"
                f"Reading: {stats.get('reading')}\n"
                f"Completed: {stats.get('completed')}\n\n"
                f"Categories:\n" + "\n".join(cat_lines)
            )

        return obs.get("message", "Task completed.")

    def _synthesize_multi_step_response(self, query: str, filter_obs: Dict[str, Any], rec_obs: Dict[str, Any]) -> str:
        """Synthesize response for multi-step workflow (e.g. Filter + Recommend)."""
        cat_count = filter_obs.get("count", 0)
        cat_name = filter_obs.get("category", "requested")

        if rec_obs.get("success"):
            rec_book = rec_obs.get("book", {})
            return (
                f"You have {cat_count} book(s) in category '{cat_name}'. "
                f"Based on your current unread list, I recommend starting with '{rec_book.get('title')}'."
            )
        else:
            return f"You have {cat_count} book(s) under '{cat_name}'. {rec_obs.get('message')}"

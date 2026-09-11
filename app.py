import os
import gradio as gr
from agent import ReadingListAgent
from memory import ReadingListMemory


# Initialize Agent & Memory
memory = ReadingListMemory()
agent = ReadingListAgent(memory=memory)


def format_books_table():
    """Format reading list for Gradio Dataframe/Table display."""
    books = memory.get_books()
    if not books:
        return [["No books in list", "-", "-", "-"]]
    
    rows = []
    for b in books:
        rows.append([
            b.get("title", ""),
            b.get("category", "general"),
            b.get("status", "unread").capitalize(),
            b.get("added_at", "-")
        ])
    return rows


def process_agent_request(user_input: str, history: list):
    """Handle chat interaction and update UI state."""
    if not user_input or not user_input.strip():
        return history, "", format_books_table(), "No request provided."

    result = agent.process_query(user_input)
    final_ans = result["final_answer"]
    trace = result["trace"]

    history = history or []
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": final_ans})

    table_data = format_books_table()
    return history, "", table_data, trace


def quick_action(action_type: str, history: list):
    """Handle quick action button triggers."""
    prompts = {
        "view": "Show my reading list.",
        "recommend": "What should I read next?",
        "stats": "How many books are on my list and what are the categories?",
        "ai_books": "Show me my AI books and tell me which one I should read."
    }
    query = prompts.get(action_type, "Show my reading list.")
    return process_agent_request(query, history)


def clear_all(history: list):
    """Clear memory and reset view."""
    memory.clear()
    table = format_books_table()
    return [], "", table, "[MEMORY CLEARED]\nReading list reset to 0 items."


# Custom CSS Theme
custom_css = """
body { background-color: #0f172a; font-family: 'Inter', sans-serif; color: #f8fafc; }
.gradio-container { max-width: 1200px !important; margin: 0 auto !important; }
.header-box { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 24px; border-radius: 16px; border: 1px solid #4338ca; text-align: center; margin-bottom: 20px; }
.header-box h1 { font-size: 2.2rem; margin: 0; color: #f8fafc; font-weight: 700; }
.header-box p { color: #a5b4fc; font-size: 1.05rem; margin-top: 6px; }
.trace-box textarea { font-family: 'Fira Code', 'Courier New', monospace !important; font-size: 0.9rem !important; background-color: #020617 !important; color: #38bdf8 !important; border: 1px solid #1e293b !important; }
.btn-primary { background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important; color: white !important; font-weight: 600 !important; border: none !important; }
.btn-secondary { background-color: #1e293b !important; color: #e2e8f0 !important; border: 1px solid #334155 !important; }
"""

with gr.Blocks(title="Reading List Manager Agent") as demo:
    gr.HTML("""
    <div class="header-box">
        <h1>📚 Reading List Manager Agent</h1>
        <p>Day 8 — 30 AI Agent Projects in 30 Days | ReAct Loop • Tool Execution • Persistent JSON Memory</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=6):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=380
            )
            with gr.Row():
                user_msg = gr.Textbox(
                    placeholder="e.g. 'Add Atomic Habits under self-help' or 'What should I read next?'",
                    label="Enter your request...",
                    scale=4,
                    lines=1
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)

            gr.Markdown("### Quick Actions")
            with gr.Row():
                btn_view = gr.Button("📋 View List", elem_classes=["btn-secondary"])
                btn_rec = gr.Button("💡 Recommend Next", elem_classes=["btn-secondary"])
                btn_stats = gr.Button("📊 View Stats", elem_classes=["btn-secondary"])
                btn_ai = gr.Button("🤖 AI Books", elem_classes=["btn-secondary"])
                btn_clear = gr.Button("🗑️ Reset Storage", variant="stop")

        with gr.Column(scale=6):
            gr.Markdown("### 📖 Stored Reading List (Persistent Memory)")
            books_table = gr.Dataframe(
                headers=["Title", "Category", "Status", "Added Date"],
                value=format_books_table(),
                interactive=False,
                wrap=True
            )

            gr.Markdown("### 🔍 Agent Execution Trace")
            trace_output = gr.Textbox(
                label="ReAct Loop (PLAN → TOOL → OBSERVE → DECIDE → MEMORY → RESPONSE)",
                placeholder="Agent trace execution details will appear here...",
                lines=10,
                interactive=False,
                elem_classes=["trace-box"]
            )

    # Event Handlers
    submit_btn.click(
        process_agent_request,
        inputs=[user_msg, chatbot],
        outputs=[chatbot, user_msg, books_table, trace_output]
    )

    user_msg.submit(
        process_agent_request,
        inputs=[user_msg, chatbot],
        outputs=[chatbot, user_msg, books_table, trace_output]
    )

    btn_view.click(lambda h: quick_action("view", h), inputs=[chatbot], outputs=[chatbot, user_msg, books_table, trace_output])
    btn_rec.click(lambda h: quick_action("recommend", h), inputs=[chatbot], outputs=[chatbot, user_msg, books_table, trace_output])
    btn_stats.click(lambda h: quick_action("stats", h), inputs=[chatbot], outputs=[chatbot, user_msg, books_table, trace_output])
    btn_ai.click(lambda h: quick_action("ai_books", h), inputs=[chatbot], outputs=[chatbot, user_msg, books_table, trace_output])
    btn_clear.click(clear_all, inputs=[chatbot], outputs=[chatbot, user_msg, books_table, trace_output])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, css=custom_css)

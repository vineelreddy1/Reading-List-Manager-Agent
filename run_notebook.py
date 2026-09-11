import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

from memory import ReadingListMemory
from agent import ReadingListAgent

notebook_path = root_dir / "notebook" / "reading_list_demo.ipynb"

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Global execution scope
scope = {}

for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        code = "".join(cell["source"])
        print(f"--- Executing Cell {i} ---")
        
        # Capture stdout
        from io import StringIO
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output
        
        try:
            exec(code, scope)
            out_text = redirected_output.getvalue()
        except Exception as e:
            out_text = f"Execution Error: {e}"
        finally:
            sys.stdout = old_stdout
            
        cell["outputs"] = [{
            "name": "stdout",
            "output_type": "stream",
            "text": out_text.splitlines(keepends=True)
        }]
        cell["execution_count"] = i

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"[OK] Notebook executed and saved with outputs at {notebook_path}")

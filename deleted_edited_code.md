# Bug Fix Log: Deleted and Replaced Code

This file contains the history of code that was deleted and replaced to fix the final 3 bugs in the Game NPC Engine v2.0.

## 1. File Descriptor Memory Leak
**File:** `core/memory_db.py`

### ❌ Deleted Code (The Bug)
```python
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
```
*Issue: This created a brand new SQLite connection on every database query. Because the `with _get_connection() as conn:` blocks only commit the transaction and do NOT close the connection, this left thousands of "zombie" open files, eventually crashing the server.*

### ✅ New Code (The Fix)
```python
_conn = None

def _get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn
```
*Fix: We now instantiate a single global connection pool and reuse it, completely stopping the file descriptor leak.*

---

## 2. Path Traversal Vulnerability
**File:** `core/emotion_voice.py`

### ❌ Deleted Code (The Bug)
```python
import os
from typing import Optional

# ... [code skipped] ...

def create_voice_directory(character_name: str):
    """Creates the voice directory structure for a new NPC character."""
    char_dir = os.path.join(VOICES_DIR, character_name.lower().replace(" ", "_"))
    os.makedirs(char_dir, exist_ok=True)
```
*Issue: `character_name` comes directly from the API JSON payload. A malicious user could send `../../../windows/system32`, allowing them to escape the sandbox and create folders anywhere on the server.*

### ✅ New Code (The Fix)
```python
import os
import re
from typing import Optional

# ... [code skipped] ...

def create_voice_directory(character_name: str):
    """Creates the voice directory structure for a new NPC character."""
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", character_name.lower())
    char_dir = os.path.join(VOICES_DIR, safe_name)
    os.makedirs(char_dir, exist_ok=True)
```
*Fix: Added `import re` and stripped all non-alphanumeric characters from the folder name before joining paths.*

---

## 3. Data Pipeline Crash on Null Values
**File:** `prepare_data.py`

### ❌ Deleted Code (The Bug)
```python
def format_item(item: dict) -> dict | None:
    """Converts a raw Airoboros row into Gemma chat format."""
    system_prompt = item.get("system", "").strip()
    user_msg = item.get("instruction", "").strip()
    model_msg = item.get("response", "").strip()
```
*Issue: If the dataset API returns an actual JSON `null` for an empty column rather than a blank string, `.get("system", "")` will return `None`. Calling `.strip()` on `None` instantly throws an AttributeError and crashes the pipeline.*

### ✅ New Code (The Fix)
```python
def format_item(item: dict) -> dict | None:
    """Converts a raw Airoboros row into Gemma chat format."""
    system_prompt = (item.get("system") or "").strip()
    user_msg = (item.get("instruction") or "").strip()
    model_msg = (item.get("response") or "").strip()
```
*Fix: Uses the `or ""` fallback so that `None` is cast to an empty string before `.strip()` is called.*

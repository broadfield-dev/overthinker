#!/usr/bin/env python3
"""
Overthinker — Gradio.Server Backend with SQLite Session Isolation + HF Trace Upload

"""

import os
import re
import json
import uuid
import sqlite3
import requests

from pathlib import Path
from typing import Optional, Dict, List, Any

from gradio import Server
from fastapi import HTTPException
from starlette.responses import HTMLResponse, PlainTextResponse, JSONResponse
from datasets import Dataset, concatenate_datasets, load_dataset
import pandas as pd
from bag import (
    BASE_URL,
    LLMS_TXT,
    SITEMAP_XML,
    ROBOTS_TXT,
    OVERSEER_JSON,
    VIDEO_PAGE_HTML,
    README_MD
)

# ---------------------------------------------------------------------------
# Application Setup
# ---------------------------------------------------------------------------
app = Server()
PORT = 7860
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b"

HF_TOKEN = os.getenv('HF_TOKEN', '')
HF_DATASET_REPO = os.getenv('HF_DATASET_REPO', 'build-small-hackathon/Overthinker-traces')

# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------

def get_db_path(session_id: str) -> Path:
    return DATA_DIR / f"session_{session_id}.db"

def init_session(session_id: str):
    db_path = get_db_path(session_id)
    if db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            description TEXT DEFAULT '',
            emoji TEXT DEFAULT '\U0001f539',
            tips TEXT DEFAULT '[]',
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    root_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO nodes (id, parent_id, type, label, description, emoji) VALUES (?, ?, ?, ?, ?, ?)",
        (root_id, None, "root", "What decision do you want to explore?", "", "\U0001f333")
    )
    conn.commit()
    conn.close()

def get_node_db(session_id: str, node_id: str) -> Optional[Dict]:
    db_path = get_db_path(session_id)
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    try:
        result['tips'] = json.loads(result.get('tips', '[]'))
    except:
        result['tips'] = []
    return result

def get_children_db(session_id: str, parent_id: str) -> List[Dict]:
    db_path = get_db_path(session_id)
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM nodes WHERE parent_id=? ORDER BY order_index",
        (parent_id,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        try:
            d['tips'] = json.loads(d.get('tips', '[]'))
        except:
            d['tips'] = []
        result.append(d)
    return result

def add_node_db(session_id: str, parent_id: str, node_type: str, label: str,
                description: str = "", emoji: str = "\U0001f539",
                tips: list = None, order_index: int = 0) -> Dict:
    node_id = str(uuid.uuid4())
    tips_json = json.dumps(tips or [])
    db_path = get_db_path(session_id)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO nodes (id, parent_id, type, label, description, emoji, tips, order_index) VALUES (?,?,?,?,?,?,?,?)",
        (node_id, parent_id, node_type, label, description, emoji, tips_json, order_index)
    )
    conn.commit()
    conn.close()
    return {
        "id": node_id,
        "parent_id": parent_id,
        "type": node_type,
        "label": label,
        "description": description,
        "emoji": emoji,
        "tips": tips or [],
        "order_index": order_index
    }

def update_root_db(session_id: str, label: str, description: str = ""):
    db_path = get_db_path(session_id)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE nodes SET label=?, description=? WHERE parent_id IS NULL",
        (label, description)
    )
    conn.commit()
    conn.close()

def get_path_db(session_id: str, node_id: str) -> List[Dict]:
    path = []
    current_id = node_id
    while current_id:
        node = get_node_db(session_id, current_id)
        if node is None:
            break
        path.append(node)
        current_id = node.get("parent_id")
    path.reverse()
    return path

def build_path_string(session_id: str, node_id: str) -> str:
    nodes = get_path_db(session_id, node_id)
    parts = []
    for n in nodes:
        t = n["type"]
        label = n["label"]
        if t == "root":
            parts.append(f"[ROOT] {label}")
        elif t == "input":
            parts.append(f"[INPUT] {label}")
        elif t == "outcome":
            parts.append(f"[OUTCOME] {label}")
    return " → ".join(parts)

def get_root_node(session_id: str) -> Optional[Dict]:
    db_path = get_db_path(session_id)
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM nodes WHERE parent_id IS NULL LIMIT 1").fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    try:
        result['tips'] = json.loads(result.get('tips', '[]'))
    except:
        result['tips'] = []
    return result

def get_all_node_ids(session_id: str) -> List[str]:
    """Get IDs of all nodes in the tree (for full export)."""
    db_path = get_db_path(session_id)
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT id FROM nodes").fetchall()
    conn.close()
    return [r[0] for r in rows]

def build_tree_nested(session_id: str) -> Optional[Dict]:
    """Build a nested tree structure from the SQLite DB."""
    root = get_root_node(session_id)
    if not root:
        return None
    def build_tree(node):
        children = get_children_db(session_id, node['id'])
        node_copy = dict(node)
        if isinstance(node_copy.get('tips'), str):
            try:
                node_copy['tips'] = json.loads(node_copy['tips'])
            except:
                node_copy['tips'] = []
        node_copy['children'] = [build_tree(c) for c in children]
        return node_copy
    return build_tree(root)

# ---------------------------------------------------------------------------
# Prompt Builders (with path_context)
# ---------------------------------------------------------------------------

def build_root_prompt(decision: str) -> str:
    return f'''You are an AI that helps people explore decisions by generating decision trees.

Generate a ROOT decision node for the following decision:

"{decision}"

Return ONLY valid JSON with exactly this structure (no markdown, no backticks):
{{
    "label": "A concise label for this decision tree (3-6 words)",
    "description": "A 1-2 sentence description of this decision context",
    "emoji": "An emoji representing this decision",
    "tips": ["One actionable tip for approaching this decision"]
}}'''

def build_options_prompt(decision_label: str, decision_desc: str, count: int, path_context: str, comment: str = "") -> str:
    path_section = f'\nFull path from root to this node: "{path_context}"' if path_context else ''
    comment_section = f'\nUser context: "{comment}"' if comment else ''
    return f'''You are an AI that helps explore decisions by generating decision tree branches.

Parent node: "{decision_label}"
Description: "{decision_desc}"{path_section}{comment_section}

Generate EXACTLY {count} child nodes that represent different OPTIONS or CHOICES the person could take.

IMPORTANT: Frame each child as an OPTION or CHOICE, not as an outcome.

Consider the full decision path above to ensure the options are contextually relevant.

Return ONLY valid JSON with exactly this structure (no markdown, no backticks):
{{
    "children": [
        {{
            "id": "child_1",
            "label": "Short option label (3-6 words)",
            "description": "1-2 sentence description",
            "emoji": "An emoji",
            "tips": ["One practical tip"]
        }},
        ...
    ]
}}

Ensure children have unique IDs like child_1, child_2, etc.'''

def build_outcomes_prompt(decision_label: str, decision_desc: str, count: int, path_context: str, comment: str = "") -> str:
    path_section = f'\nFull path from root to this node: "{path_context}"' if path_context else ''
    comment_section = f'\nUser context: "{comment}"' if comment else ''
    return f'''You are an AI that helps explore decisions by generating decision tree branches.

Parent node: "{decision_label}"
Description: "{decision_desc}"{path_section}{comment_section}

Generate EXACTLY {count} child nodes that represent a DIVERSE RANGE of possible OUTCOMES. Include a MIX of positive, neutral, and negative outcomes.

IMPORTANT: Frame each child as an OUTCOME or CONSEQUENCE, not as a choice someone makes.

Consider the full decision path above to ensure the outcomes are contextually relevant.

Return ONLY valid JSON with exactly this structure (no markdown, no backticks):
{{
    "children": [
        {{
            "id": "child_1",
            "label": "Short outcome label (3-6 words)",
            "description": "1-2 sentence description",
            "emoji": "An emoji",
            "tips": ["One practical tip"]
        }},
        ...
    ]
}}

Ensure children have unique IDs. Make sure the first child is POSITIVE, the second is NEUTRAL, and the third is NEGATIVE.'''

# ---------------------------------------------------------------------------
# AI Call (using OpenRouter via requests)
# ---------------------------------------------------------------------------

def call_api(prompt: str, system_prompt: str = "You are a helpful assistant that generates decision trees.") -> Optional[str]:
    if not OPENROUTER_API_KEY:
        print("[OpenRouter Error] No API key configured")
        return None
    try:
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost:7860'
        }
        data = {
            'model': DEFAULT_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 2048,
            "reasoning": {"enabled": False}

        }
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=data,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            try:
                return result['choices'][0]['message']['content']
            except Exception:
                raise HTTPException(status_code=500, detail="Temporary error: return format, try again.")
        else:
            raise HTTPException(status_code=500, detail="Temporary error: server error, try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Temporary error: server exception, try again.")
        
    return None

def parse_json_response(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end+1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[JSON Parse Error] {e}")
        print(f"[Raw text] {text[:500]}")
        return None

# ---------------------------------------------------------------------------
# Routes (All POST, no GET except for serving index)
# ---------------------------------------------------------------------------

@app.get("/")
async def index():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>Overthinker</h1><p>index.html not found</p>", status_code=404)

@app.post("/root")
async def create_root(request: dict):
    session_id = request.get('session_id', str(uuid.uuid4()))
    init_session(session_id)
    root = get_root_node(session_id)
    if root is None:
        raise HTTPException(status_code=500, detail="Could not initialize session.")
    return {"session_id": session_id, "node": root}

@app.post("/create_tree")
async def create_tree(request: dict):
    session_id = request.get('session_id', str(uuid.uuid4()))
    decision = request.get('decision', '')
    if not decision:
        raise HTTPException(status_code=400, detail="Decision text is required.")
    init_session(session_id)
    prompt = build_root_prompt(decision)
    ai_response = call_api(prompt)
    parsed = parse_json_response(ai_response) if ai_response else None
    if not parsed:
        raise HTTPException(status_code=500, detail="Failed to generate root node. Please check your API key and try again.")
    label = parsed.get('label', f'Overthinking: {decision[:40]}')
    description = parsed.get('description', f'You are overthinking: {decision}')
    emoji = parsed.get('emoji', '\U0001f333')
    tips = parsed.get('tips', ['Start by exploring options.'])
    update_root_db(session_id, label, description)
    db_path = get_db_path(session_id)
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE nodes SET emoji=?, tips=? WHERE parent_id IS NULL", (emoji, json.dumps(tips)))
    conn.commit()
    conn.close()
    root = get_root_node(session_id)
    return {'session_id': session_id, 'node': root}

@app.post("/get_node")
async def get_node_endpoint(request: dict):
    session_id = request.get('session_id')
    node_id = request.get('node_id')
    if not session_id or not node_id:
        raise HTTPException(status_code=400, detail="Missing session_id or node_id")
    init_session(session_id)
    node = get_node_db(session_id, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    children = get_children_db(session_id, node_id)
    path_context = build_path_string(session_id, node_id)
    return {
        'node': node,
        'children': children,
        'path_context': path_context
    }

@app.post("/get_children")
async def get_children(request: dict):
    session_id = request.get('session_id')
    node_id = request.get('node_id')
    count = request.get('count', 3)
    node_type = request.get('node_type', 'outcome')
    comment = request.get('comment', '')
    if not session_id or not node_id:
        raise HTTPException(status_code=400, detail="Missing session_id or node_id")
    init_session(session_id)
    parent = get_node_db(session_id, node_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Node not found")
    path_context = build_path_string(session_id, node_id)
    next_type_map = {'root': 'input', 'input': 'outcome', 'outcome': 'input'}
    next_type = next_type_map.get(node_type, 'outcome')
    parent_label = parent.get('label', 'Unknown')
    parent_desc = parent.get('description', '')
    if next_type == 'input':
        prompt = build_options_prompt(parent_label, parent_desc, count, path_context, comment)
    else:
        prompt = build_outcomes_prompt(parent_label, parent_desc, count, path_context, comment)
    ai_response = call_api(prompt)
    parsed = parse_json_response(ai_response) if ai_response else None
    if not parsed or 'children' not in parsed or not isinstance(parsed['children'], list):
        raise HTTPException(status_code=500, detail="Generation failed. Please check your API key and try again.")
    children_data = parsed['children']
    children = []
    for i, child in enumerate(children_data):
        label = child.get('label', 'Unknown')
        description = child.get('description', '')
        emoji = child.get('emoji', '\U0001f539')
        tips = child.get('tips', [f'Consider this {next_type}.'])
        existing = get_children_db(session_id, node_id)
        existing_labels = [c['label'] for c in existing]
        if label in existing_labels or label in [c['label'] for c in children]:
            label = f"{label} ({i+1})"
        child_node = add_node_db(session_id, node_id, next_type, label, description, emoji, tips, order_index=i)
        child_node['type'] = next_type
        children.append(child_node)
    return {'children': children, 'next_type': next_type}

@app.post("/add_options")
async def add_options(request: dict):
    session_id = request.get('session_id')
    node_id = request.get('node_id')
    count = request.get('count', 3)
    comment = request.get('comment', '')
    if not session_id or not node_id:
        raise HTTPException(status_code=400, detail="Missing session_id or node_id")
    init_session(session_id)
    parent = get_node_db(session_id, node_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Node not found")
    path_context = build_path_string(session_id, node_id)
    next_type_map = {'root': 'input', 'input': 'outcome', 'outcome': 'input'}
    next_type = next_type_map.get(parent.get('type', 'root'), 'outcome')
    parent_label = parent.get('label', 'Unknown')
    parent_desc = parent.get('description', '')
    if next_type == 'input':
        prompt = build_options_prompt(parent_label, parent_desc, count, path_context, comment)
    else:
        prompt = build_outcomes_prompt(parent_label, parent_desc, count, path_context, comment)
    ai_response = call_api(prompt)
    parsed = parse_json_response(ai_response) if ai_response else None
    if not parsed or 'children' not in parsed or not isinstance(parsed['children'], list):
        raise HTTPException(status_code=500, detail="Failed to add options. Please try again.")
    children_data = parsed['children']
    children = []
    for i, child in enumerate(children_data):
        label = child.get('label', 'Unknown')
        description = child.get('description', '')
        emoji = child.get('emoji', '\U0001f539')
        tips = child.get('tips', [f'Additional {next_type}.'])
        existing = get_children_db(session_id, node_id)
        existing_labels = [c['label'] for c in existing]
        if label in existing_labels or label in [c['label'] for c in children]:
            label = f"{label} ({i+1})"
        child_node = add_node_db(session_id, node_id, next_type, label, description, emoji, tips, order_index=i)
        child_node['type'] = next_type
        children.append(child_node)
    return {'children': children, 'next_type': next_type}

@app.post("/upload_trace")
async def upload_trace(request: dict):
    """Serialize the full tree from SQLite and push to HuggingFace dataset."""
    session_id = request.get('session_id')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    if not HF_TOKEN or not HF_DATASET_REPO:
        raise HTTPException(status_code=500, detail="HF_TOKEN and HF_DATASET_REPO must be configured in environment.")
    
    tree = build_tree_nested(session_id)
    if tree is None:
        raise HTTPException(status_code=404, detail="No tree found for this session.")
    
    try:

        
        row = {
            'session_id': session_id,
            'tree_json': json.dumps(tree),
            'created_at': str(tree.get('created_at', ''))
        }
        df = pd.DataFrame([row])
        new_dataset = Dataset.from_pandas(df)
        
        try:
            existing_dataset = load_dataset(HF_DATASET_REPO, split='train', token=HF_TOKEN)
            combined = concatenate_datasets([existing_dataset, new_dataset])
        except Exception:
            combined = new_dataset
        
        combined.push_to_hub(HF_DATASET_REPO, token=HF_TOKEN, private=False)
        
        return {'status': 'success', 'message': 'Trace uploaded successfully!'}
    except Exception as e:
        print(f"[Upload Trace Error] {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload trace: {str(e)}")

@app.post("/export_json")
async def export_json(request: dict):
    session_id = request.get('session_id')
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    root = get_root_node(session_id)
    if not root:
        raise HTTPException(status_code=404, detail="No tree found")
    def build_tree(node):
        children = get_children_db(session_id, node['id'])
        node_copy = dict(node)
        node_copy['children'] = [build_tree(c) for c in children]
        return node_copy
    full_tree = build_tree(root)
    return full_tree

@app.post("/export_path_json")
async def export_path_json(request: dict):
    session_id = request.get('session_id')
    node_id = request.get('node_id')
    if not session_id or not node_id:
        raise HTTPException(status_code=400, detail="Missing session_id or node_id")
    path_nodes = get_path_db(session_id, node_id)
    return {'path': path_nodes}

@app.post("/export_path_md")
async def export_path_md(request: dict):
    session_id = request.get('session_id')
    node_id = request.get('node_id')
    if not session_id or not node_id:
        raise HTTPException(status_code=400, detail="Missing session_id or node_id")
    path = get_path_db(session_id, node_id)
    md = '# \U0001f9e0 Overthinker — Decision Path\n\n'
    for i, node in enumerate(path):
        indent = '  ' * i
        emoji = {'root': '\U0001f333', 'input': '\U0001f9e0', 'outcome': '\U0001f4ca'}.get(node.get('type', ''), '\U0001f4cc')
        md += f'{indent}{emoji} **{node.get("label", "")}**\n'
        if node.get('description'):
            md += f'{indent}  > {node.get("description", "")}\n'
        if node.get('tips') and len(node['tips']) > 0:
            md += f'{indent}  > \U0001f4a1 {node["tips"][0]}\n'
        md += '\n'
    return PlainTextResponse(content=md, status_code=200)
@app.get("/llms.txt", response_class=PlainTextResponse)
async def get_llms_txt():
    return PlainTextResponse(LLMS_TXT)

@app.get("/readme.md", response_class=PlainTextResponse)
async def get_readme_md():
    return PlainTextResponse(README_MD)
    
@app.get("/sitemap.xml", response_class=HTMLResponse)
async def get_sitemap():
    return HTMLResponse(content=SITEMAP_XML, media_type="application/xml")

@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots():
    return PlainTextResponse(ROBOTS_TXT)

@app.get("/overthinker.json", response_class=JSONResponse)
async def get_overthinker_json():
    return JSONResponse(content=OVERSEER_JSON, media_type="application/json")

@app.get("/video", response_class=HTMLResponse)
async def get_video():
    return HTMLResponse(content=VIDEO_PAGE_HTML)
# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"\U0001f9e0 Overthinker — SQLite Session Mode + HF Trace Upload on port {PORT}")
    print(f"\U0001f916 Model: {DEFAULT_MODEL}")
    print(f"\U0001f310 Open http://localhost:{PORT} in your browser")
    if not OPENROUTER_API_KEY:
        print("\u26a0\ufe0f  No OPENROUTER_API_KEY found. Add to .env or environment. Generation will fail.")
    if not HF_TOKEN or not HF_DATASET_REPO:
        print("\u26a0\ufe0f  No HF_TOKEN or HF_DATASET_REPO set. Upload will fail.")
    app.launch(
        server_port=PORT,
        show_error=True,
        share=False
    )

# bag.py — Static strings for SEO, metadata, and video page
# All strings are exported as module-level variables for app.py to serve

BASE_URL = "https://build-small-hackathon-overthinker.hf.space"
VIDEO_URL = "https://huggingface.co/spaces/build-small-hackathon/OverThinker/resolve/main/video_1.mp4"
VIDEO_CARD = "https://cdn-uploads.huggingface.co/production/uploads/677e884129c1f2af708eb07b/et2f8YT0mUp1DipL8LL-U.jpeg"
# --- LLMs.txt ---
LLMS_TXT = """# Overthinker: AI-Powered Decision Tree Explorer (WIP)
**Overthinker** is an interactive decision tree explorer that helps you untangle complex choices by generating context-aware options and outcomes using a small open-weight AI model. Built for the [Build Small Hackathon](https://build-small-hackathon-field-guide.hf.space/) — a Hugging Face × Gradio jam for tiny AI models under 32B parameters.
[![Hugging Face Space](https://img.shields.io/badge/🤗%20Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/build-small-hackathon/overthinker) 
[![Demo Video](https://img.shields.io/badge/📺%20Demo-Video-blue)](https://youtube.com/) 
[![Social Post](https://img.shields.io/badge/🐦%20Social-Post-1DA1F2)](https://x.com/broadfield_dev/status/2066130027029406090)
![Screenshot](https://cdn-uploads.huggingface.co/production/uploads/677e884129c1f2af708eb07b/et2f8YT0mUp1DipL8LL-U.jpeg)
---
## 🧠 The Idea
Ever spent hours overthinking a decision? Overthinker turns that into a feature. You start with a root question — "Should I quit my job?" — and the AI generates branching options (Input nodes) and outcomes (Outcome nodes), building a full decision tree. Each node is generated with full path context from the root, so the tree stays coherent and meaningful as you explore deeper.
**Track:** Backyard AI (practical, problem-solving app) + Whimsical (Thousand Token Wood) — the playful tree exploration fits both.
---
## ✅ Hackathon Requirements Met
| Requirement | Status | Details |
|------------|--------|---------|
| **Under 32B parameters** (REQ-01) | ✅ | Uses `nvidia/nemotron-3-nano-30b-a3b` (30B) via OpenRouter API |
| **Gradio app deployed** (REQ-02) | ✅ | Gradio.Server-based app, deployable as Hugging Face Space |
| **Demo video** (REQ-03) | ⏳ | Loading.... |
| **Social post** (REQ-04) | ✅ | Linked above |
| **GPU limit** (REQ-05) | ✅ | Zero GPU usage — inference runs remotely via OpenRouter API |
| **Tagged README** (REQ-06) | ✅ | YAML front matter includes track + badge tags |
---
## 🏆 Targeted Prizes & Badges
| Prize / Badge | Value | Why Overthinker Qualifies |
|--------------|-------|--------------------------|
| **Nemotron Hardware Prize** (NVIDIA) | Two RTX 5080s | Built with `nvidia/nemotron-3-nano-30b-a3b` — a Nemotron model. Full path context injection ensures coherent generation. |
| **Off Brand** ($1,500) | Custom UI bonus | Custom D3.js tree visualization with zoom/pan/drag, path sidebar, export to SVG/JSON/PNG, keyboard shortcuts, theme toggle — far beyond default Gradio components. |
| **Best Demo** ($1,000) | Full package | Interactive app + demo video + social post — all three will be polished. |
| **Bonus Quest Champion** ($2,000) | Most criteria met | Targets Nemotron + Off Brand + Best Demo + Community Choice + Tiny Titan (model ≤ 4B? No, but 30B is still small). |
| **Community Choice** ($2,000) | Shareable app | Beautiful D3 tree, export features, shareable trace upload to HF dataset — encourages social sharing. |
---
## ✨ Key Features
- **Interactive Decision Tree**: Start with a root question, explore branching options and outcomes
- **Full Path Context**: Every generation prompt includes the entire lineage from root to current node — no disconnected logic
- **Session-Based Storage**: SQLite per-session databases — zero memory overlap between users, safe for public Spaces
- **Rich Visualization**: D3.js tree with zoom, pan, drag, collapsible nodes, and breadcrumb navigation
- **Export Options**: Save your tree as SVG, JSON, Markdown, or PNG
- **Trace Upload**: Upload your decision tree to a shared Hugging Face dataset for community exploration
---
## 🛠️ Tech Stack
| Component | Technology |
|-----------|-----------|
| **Frontend** | Gradio (custom D3.js + HTML/CSS/JS) |
| **Backend** | Python 3.10+, Gradio.Server (FastAPI-based) |
| **AI Model** | `nvidia/nemotron-3-nano-30b-a3b` via OpenRouter API |
| **Database** | SQLite (per-session, disk-persistent) |
| **Dataset** | Hugging Face `datasets` (trace upload) |
| **Deployment** | Hugging Face Spaces (no GPU needed) |
---
## 🚀 Getting Started
### Local Development
1. **Clone the repository**
```bash
git clone https://github.com/broadfield-dev/overthinker.git
cd Overthinker_Hackathon
```
2. **Install dependencies**
```bash
pip install gradio
```
3. **Set environment variables**
Create a `.env` file:
```
OPENROUTER_API_KEY=your_openrouter_api_key
HF_TOKEN=your_huggingface_write_token  # for trace upload
HF_DATASET_REPO=your-username/overthinker-traces  # optional, for trace sharing
```
4. **Run the app**
```bash
python app.py
```
Then open `http://localhost:7860` in your browser.
### Deploy on Hugging Face Spaces
1. Fork or upload this repository as a new Space on Hugging Face
2. Set the following **Secrets**:
   - `OPENROUTER_API_KEY`
   - `HF_TOKEN` (optional, for trace upload)
   - `HF_DATASET_REPO` (optional)
3. Ensure `requirements.txt` contains: `gradio`, `fastapi`, `uvicorn`, `httpx`, `jinja2`, `datasets`
4. The Space will start automatically — no GPU needed
> Note: SQLite databases are stored in the `data/` directory, which persists across restarts on Hugging Face Spaces.
---
## 📚 How It Works
1. **Start**: Enter a decision question (e.g., "Should I start a business?")
2. **Generate Options**: Click "Explore Options" — the AI generates 3 possible paths
3. **Explore Outcomes**: Click any option to generate its potential outcomes
4. **Dive Deeper**: Continue exploring deeper into the tree — each level maintains full context from the root
5. **Export**: Save your tree as SVG, JSON, Markdown, or PNG
6. **Upload Trace**: Share your decision tree with the community via HF dataset upload
### Path Context Injection
Overthinker passes the complete path from root to current node into every AI prompt:
```
[ROOT] Should I quit my job? → [INPUT] Start freelancing → [OUTCOME] Income becomes unstable
```
This ensures coherent, context-aware generation at every depth.
---
## 🧪 Testing & Quality
- All endpoints tested with valid and invalid session IDs
- Edge cases: empty trees, multiple concurrent users, API failures
- Memory testing: validated <50MB RAM under heavy load (compared to 5GB in v26)
- Frontend tested in Chrome, Firefox, and Safari
---
## 📦 File Structure
```
Overthinker_Hackathon/
├── app.py                 # Backend with SQLite, POST endpoints, path context
├── templates/
│   └── index.html         # Full D3 tree visualization (~1800 lines)
├── data/                  # Created automatically for per-session SQLite DBs
├── README.md              # This file
└── requirements.txt       # (to be added — include gradio, fastapi, uvicorn, httpx, jinja2, datasets)
```
---
## 🔗 Links
- **Field Guide**: [https://build-small-hackathon-field-guide.hf.space/](https://build-small-hackathon-field-guide.hf.space/)
- **Hugging Face Space**: [To be added after submission](https://huggingface.co/spaces/build-small-hackathon/overthinker)
- **Demo Video**: [To be added]()
- **Social Post**: [To be added]()
- **Hugging Face Dataset (Traces)**: [To be added]()
---
## 🙌 Acknowledgments
Built with ❤️ for the [Build Small Hackathon](https://build-small-hackathon-field-guide.hf.space/) by broadfield-dev.
Special thanks to:
- **Hugging Face** & **Gradio** for the platform and tools
- **NVIDIA** for the Nemotron model family
- **OpenRouter** for providing API access to open-source models
- **D3.js** for the powerful visualization library
---
*Last updated: June 14, 2026*"""

# --- Sitemap XML ---
SITEMAP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>2026-06-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{BASE_URL}/llms.txt</loc>
    <changefreq>always</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{BASE_URL}/overthinker.json</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{BASE_URL}/video</loc>
    <changefreq>weekly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>
"""

# --- Robots.txt ---
ROBOTS_TXT = f"""User-agent: *
Allow: /
Sitemap: {BASE_URL}/sitemap.xml
"""

# --- Overthinker JSON-LD ---
OVERSEER_JSON = f"""{{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Overthinker",
  "description": "AI-powered decision tree explorer that generates options and outcomes with full context from root.",
  "url": "{BASE_URL}/",
  "applicationCategory": "Productivity",
  "operatingSystem": "Web",
  "author": {{
    "@type": "Person",
    "name": "broadfield-dev"
  }},
  "offers": {{
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }}
}}
"""

# --- Video Page HTML (placeholder for your video URL) ---
# Replace PLACEHOLDER_VIDEO_URL with your actual video link
VIDEO_PAGE_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Overthinker Demo Video</title>
  <!-- Basic Page Meta -->
    <meta property="og:title" content="OverThinker Demo" />
    <meta property="og:description" content="AI Powered Decision Tree" />
    <meta property="og:image" content="{VIDEO_CARD}" />
    <meta property="og:url" content="{BASE_URL}/video" />
    
    <!-- Video-Specific Open Graph Tags -->
    <meta property="og:video" content="{VIDEO_URL}" />
    <meta property="og:video:secure_url" content="{VIDEO_URL}" />
    <meta property="og:video:type" content="video/mp4" />
    <meta property="og:video:width" content="1280" />
    <meta property="og:video:height" content="720" />
    <meta name="twitter:card" content="player" />
    <meta name="twitter:title" content="OverThinker Demo" />
    <meta name="twitter:description" content="AI Powered Decision Tree" />
    <meta name="twitter:image" content="{VIDEO_CARD}" />
    <meta name="twitter:player" content="{VIDEO_URL}" />
    <meta name="twitter:player:width" content="1280" />
    <meta name="twitter:player:height" content="720" />
       """ + """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "VideoObject",
      "name": "OverThinker Demo",
      "description": "Build Small Hackathon | AI Powered Decision Tree",
      "thumbnailUrl": "https://cdn-uploads.huggingface.co/production/uploads/677e884129c1f2af708eb07b/et2f8YT0mUp1DipL8LL-U.jpeg",
      "uploadDate": "2026-06-15T08:00:00+08:00",
      "duration": "PT3M20S",
      "contentUrl": "https://huggingface.co/spaces/build-small-hackathon/OverThinker/resolve/main/video_1.mp4",
      "embedUrl": "https://build-small-hackathon-overthinker.hf.space/video"
    }
    </script>
 
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: #fff;
      padding: 2rem;
    }
    h1 {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      background: linear-gradient(45deg, #f093fb, #f5576c);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .video-container {
      width: 100%;
      max-width: 800px;
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    video {
      width: 100%;
      display: block;
    }
    .back-link {
      margin-top: 2rem;
      color: #a0a0ff;
      text-decoration: none;
      font-size: 1.2rem;
      transition: 0.3s;
    }
    .back-link:hover {
      color: #f5576c;
      text-decoration: underline;
    }
  </style>
</head>""" + f"""
<body>
  <h1>Overthinker Demo</h1>
  <div class="video-container">
    <video controls poster="{VIDEO_CARD}">
      <source src="{VIDEO_URL}" type="video/mp4">
      Your browser does not support the video tag.
    </video>
  </div>
  <a href="/" class="back-link">← Back to Overthinker</a>
</body>
</html>
"""

README_MD=LLMS_TXT

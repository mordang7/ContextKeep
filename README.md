<div align="center">

![ContextKeep Banner](assets/banner.png)

# ContextKeep 🧠
### Infinite Long-Term Memory for AI Agents

[![Version: 1.2](https://img.shields.io/badge/Version-1.2-brightgreen?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![Status: Stable](https://img.shields.io/badge/Status-Stable-blue?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![Platform: Linux | Windows | macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-green.svg?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/paypalme/GeekJohn)

**ContextKeep** is a powerful, standalone memory server that gives your AI agents (Claude, Cursor, Gemini, OpenCode, and more) a persistent, searchable brain. Stop repeating yourself — let your AI remember everything, permanently.

[Features](#-features) • [What's New in V1.2](#-whats-new-in-v12) • [Installation](#-installation) • [MCP Tools](#-mcp-tools) • [Web Dashboard](#-web-dashboard) • [Configuration](#-configuration)

</div>

---

## 🌟 Features

*   **♾️ Infinite Context:** Store unlimited project details, preferences, decisions, and snippets — no expiry, no size cap.
*   **💰 Save Money & Tokens:** Pull only the memories that matter, slashing context window usage and API costs.
*   **🔌 Universal Compatibility:** Works with *any* MCP-compliant client via Stdio (local) or SSE (remote/homelab).
*   **🧭 Memory Index Protocol:** A reliable two-step retrieval system — `list_all_memories()` → `retrieve_memory()` — so agents always find the right key, every time.
*   **🖥️ Modern Web Dashboard:** Manage your memories visually with Grid, List, and Calendar views in a sleek dark interface.
*   **🔒 Privacy First:** 100% local storage. Your data never touches an external server.
*   **🔎 Smart Search:** Keyword and semantic search across all memory content.
*   **🐧 Linux Service:** Runs silently in the background as a systemd service.

---

![ContextKeep Showcase](Showcase.png)

---

## 🆕 What's New in V1.2

### 🧭 `list_all_memories()` — The Memory Index Tool
The headline feature of V1.2. Agents can now call `list_all_memories()` to receive a complete directory of every stored memory — key, title, tags, and last-updated timestamp — in a single call. This eliminates unreliable fuzzy key guessing and makes memory retrieval 100% deterministic.

```
📚 Memory Directory — 140 total memories:
==================================================

🔑 Key:     GJ_Personal_Setup_Master
   Title:   Personal System Specifications (Master Record)
   Tags:    setup, specs, desktop, homelab
   Updated: 2026-02-19T12:37

🔑 Key:     GeekJ_Video_Shield_vs_Streamer_2026
   Title:   GeekJ Video: Shield TV Pro vs Google TV Streamer 4K
   Tags:    GeekJ, YouTube, video, streaming
   Updated: 2026-02-10T22:06
...
```

**The recommended retrieval protocol for agents:**
> **Step 1:** Call `list_all_memories()` → scan the directory for the exact key.
> **Step 2:** Call `retrieve_memory(exact_key)` → fetch the full content.
>
> Only use `search_memories()` for content-based searches, not key lookup.

---

### 🎨 Obsidian Lab UI Redesign
The web dashboard has been completely reskinned with a premium dark "Obsidian Lab" aesthetic:
- Deep navy background with electric cyan (`#00e5ff`) accents
- JetBrains Mono for memory keys — instantly distinguishable at a glance
- Violet tag chips on Grid cards
- Live memory count badge in the top-right header

### 📅 Enhanced Calendar View
- Full month navigation — scroll forward and backward through your memory timeline
- Cleaned-up layout — the "Recent Memories" sidebar has been removed for a focused, distraction-free calendar experience

### 🃏 Richer Grid Cards
Grid view cards now show:
- **Tag chips** — all tags displayed as coloured pills directly on the card
- **Character count badge** — instant size indicator per memory (e.g. `2.1k chars`)

---

## 🚀 Installation

### Prerequisites
*   Python 3.10 or higher (if running locally)
*   Docker & Docker Compose (optional, for containerised deployment)
*   Git (optional)

### Docker Deployment (Recommended)

The easiest way to run ContextKeep is using Docker Compose. This runs both the MCP Server (SSE) and the WebUI in isolated containers with a shared volume for persistent memory storage.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mordang7/ContextKeep.git
    cd ContextKeep
    ```

2.  **Start the services:**
    ```bash
    docker compose up -d
    ```

This will expose:
*   **WebUI:** `http://localhost:5000`
*   **MCP Server (SSE):** `http://localhost:5100/sse`

Your data is safely stored in a Docker volume (`contextkeep-data`) so it persists between restarts.

### Local Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mordang7/ContextKeep.git
    cd ContextKeep
    ```

2.  **Run the Installer:**
    *   **Linux/macOS:**
        ```bash
        python3 install.py
        ```
    *   **Windows:**
        ```powershell
        python install.py
        ```

3.  **Follow the Wizard:** The installer creates a virtual environment, installs dependencies, and generates a ready-to-use `mcp_config.json`.

---

## 🛠️ MCP Tools

ContextKeep exposes **5 MCP tools** to any connected agent:

| Tool | Signature | Purpose |
|------|-----------|---------|
| `list_all_memories` | *(no args)* | **[USE FIRST]** Returns a full directory of all memory keys, titles, tags, and timestamps |
| `retrieve_memory` | `(key: str)` | Fetch the full content of a specific memory by exact key |
| `store_memory` | `(key: str, content: str, tags: str)` | Create or update a memory |
| `search_memories` | `(query: str)` | Content-based keyword/semantic search across all memories |
| `list_recent_memories` | *(no args)* | Return the 10 most recently updated memories |

### Recommended Agent Directive

Add this to your `GEMINI.md`, `AGENTS.md`, or `CLAUDE.md`:

```markdown
## Memory Index Protocol (MANDATORY)
1. FIRST — call `list_all_memories()` to get the complete key directory
2. THEN — call `retrieve_memory(exact_key)` using the exact key from step 1
Only use `search_memories()` for content-based searches, NOT for key lookup.
```

---

## 🔌 Configuration

Copy the contents of `mcp_config.example.json` into your AI client's config file and update the paths.

### Option 1: Local (Claude Desktop / Gemini CLI / Cursor)
```json
{
  "mcpServers": {
    "context-keep": {
      "command": "/absolute/path/to/ContextKeep/venv/bin/python",
      "args": ["/absolute/path/to/ContextKeep/server.py"]
    }
  }
}
```

### Option 2: Remote via SSH (Homelab / Raspberry Pi)
Run ContextKeep on a home server and access it from any machine on your network:
```json
{
  "mcpServers": {
    "context-keep": {
      "command": "ssh",
      "args": [
        "-i", "/path/to/private_key",
        "user@192.168.1.X",
        "'/path/to/ContextKeep/venv/bin/python'",
        "'/path/to/ContextKeep/server.py'"
      ]
    }
  }
}
```

### Option 3: SSE Mode (HTTP)
Ideal for OpenCode, web apps, or any client that prefers HTTP transport:
```json
{
  "mcpServers": {
    "context-keep": {
      "transport": "sse",
      "url": "http://localhost:5100/sse"
    }
  }
}
```

---

## 🌐 Web Dashboard

ContextKeep ships with a full-featured web UI to manage your memories without touching the CLI.

*   **URL:** `http://localhost:5000`
*   **Grid View:** Memory cards with tag chips, char counts, and inline actions
*   **List View:** Dense, scannable table with all memories sorted by last updated
*   **Calendar View:** Browse your memory history by month
*   **Search:** Real-time filtering across titles, keys, and content
*   **Full CRUD:** Create, view, edit, and delete memories from the browser

**To start manually:**
```bash
./venv/bin/python webui.py
```

---

## 🐧 Linux Service Setup (Recommended for Homelabs)

Run both the MCP server and Web UI as persistent background services:

```bash
chmod +x install_services.sh
./install_services.sh
```

This installs:

| Service | Port | Purpose |
|---------|------|---------|
| `contextkeep-server` | `5100` | MCP server (SSE transport) |
| `contextkeep-webui` | `5000` | Web dashboard |

**Manage services:**
```bash
sudo systemctl status contextkeep-server
sudo systemctl restart contextkeep-webui
```

---

## 📋 Changelog

### V1.2 — Obsidian Lab
- ✅ New `list_all_memories()` MCP tool — complete memory directory in one call
- ✅ Obsidian Lab UI redesign — dark premium aesthetic with cyan/neon accents
- ✅ Memory count live badge in the header
- ✅ Calendar month navigation (forward/back)
- ✅ Grid cards now show tag chips and character count badges
- ✅ Removed "Recent Memories" sidebar for a cleaner calendar layout
- ✅ Memory Index Protocol V1.2 — standardised two-step agent retrieval pattern

### V1.1
- Web dashboard with Grid, List, and Calendar views
- SSE transport support alongside Stdio
- Linux systemd service installer
- Memory titles and timestamps

### V1.0
- Core MCP server with `store_memory`, `retrieve_memory`, `search_memories`
- SQLite-backed persistent storage
- SSH remote transport support

---

## 🤝 Contributing

Contributions are welcome. Open a PR, file an issue, or suggest a feature — all input is appreciated.

## ☕ Support the Project

If ContextKeep saves you time, tokens, or sanity — consider buying me a coffee.

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/paypalme/GeekJohn)

---

<div align="center">
  <sub>Built with ❤️ by GeekJohn</sub>
</div>

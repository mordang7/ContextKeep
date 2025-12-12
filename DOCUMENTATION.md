# ContextKeep V1.0 Beta - Complete Documentation

## 🧠 Overview
**ContextKeep** (formerly SmartMCP Agent) is a powerful, standalone memory server for AI agents. It provides a persistent, searchable "long-term memory" that allows your AI tools (like Gemini CLI, OpenCode, Cursor, VS Code, and Antigravity) to remember context, project details, and user preferences across sessions.

### Key Features
*   **Infinite Memory:** Store unlimited notes, snippets, and context.
*   **Universal Compatibility:** Works with any MCP-compliant client (Stdio & SSE support).
*   **Web Interface:** Manage your memories visually via a modern dashboard.
*   **Privacy Focused:** All data is stored locally on your machine (or private server).
*   **Smart Search:** Semantic and keyword search to find exactly what you need.

---

## 🚀 Installation

### Prerequisites
*   Python 3.10 or higher
*   Git (optional, for cloning)

### 1. Setup (Server-Side)
1.  **Download/Clone** the `ContextKeep` folder to your desired location (e.g., `/home/shared/J_Useful_Apps/ContextKeep`).
2.  **Run the Installer**:
    *   **Linux/Mac**:
        ```bash
        cd ContextKeep
        python3 install.py
        ```
    *   **Windows**:
        ```powershell
        cd ContextKeep
        python install.py
        ```
3.  **Install System Services (Linux Only)**:
    To run ContextKeep automatically in the background:
    ```bash
    chmod +x install_services.sh
    ./install_services.sh
    ```
    This will install and start:
    *   `contextkeep-server`: The MCP API server (Port 5100).
    *   `contextkeep-webui`: The Web Dashboard (Port 5000).

---

## 🔌 Client Configuration

### A. Gemini CLI
Edit your `settings.json`:
```json
{
  "mcpServers": {
    "context-keep": {
      "transport": "sse",
      "url": "http://<SERVER_IP>:5100/sse"
    }
  }
}
```

### B. OpenCode (Local)
Edit your `opencode.json`. **Note:** OpenCode requires local stdio if running on the same machine.
```json
{
  "mcp": {
    "context-keep": {
      "type": "local",
      "command": [
        "/path/to/ContextKeep/venv/bin/python",
        "/path/to/ContextKeep/server.py"
      ],
      "enabled": true
    }
  }
}
```

### C. Antigravity / Cursor / VS Code (Remote via SSH)
Edit your `mcp_config.json` or IDE settings:
```json
{
  "mcpServers": {
    "context-keep": {
      "command": "ssh",
      "args": [
        "-i", "/path/to/private_key",
        "user@<SERVER_IP>",
        "'/path/to/ContextKeep/venv/bin/python'",
        "'/path/to/ContextKeep/server.py'"
      ]
    }
  }
}
```
*Note: Ensure paths with spaces are wrapped in single quotes inside the JSON string.*

---

## 📖 Usage Guide

### Available Tools
Your AI will have access to these tools:
1.  `store_memory(key, content, tags)`: Save a new memory.
    *   *Example:* "Store a memory called 'project_specs' with the content '...'"
2.  `retrieve_memory(key)`: Get the content of a specific memory.
    *   *Example:* "Retrieve the 'project_specs' memory."
3.  `search_memories(query)`: Find memories by keyword or topic.
    *   *Example:* "Search for memories about 'database schema'."
4.  `list_recent_memories()`: See what you've worked on recently.

### Web Dashboard
Access the dashboard at `http://<SERVER_IP>:5000`.
*   **View:** Browse memories in Grid, List, or Calendar view.
*   **Edit:** Manually update memory content.
*   **Create:** Add new memories directly from the browser.
*   **Search:** Filter memories instantly.

---

## 📜 Project History & Changelog

## 📜 Project History & Changelog

### **ContextKeep V1.1 Public Beta (2025-11-30)**
*   **Public Release:** Released on GitHub: [mordang7/ContextKeep](https://github.com/mordang7/ContextKeep).
*   **Sanitization:** Codebase fully sanitized for public use.
*   **Features:** Added "Save Money & Tokens" feature; updated branding with Cyberpunk aesthetic.
*   **Documentation:** Professional README with donation link and badges.

### **ContextKeep V1.0 Beta (2025-11-30)**
*   **Rebranding:** Officially renamed from "SmartMCP Agent" (and briefly "Memora") to "ContextKeep".
*   **Standalone Release:** Decoupled from "AI_CLI_Projects" into a dedicated "J_Useful_Apps" product.
*   **Simplified Setup:** New `install_services.sh` with auto-detection for User/Path.
*   **WebUI Fixes:** Fixed branding and CSS loading issues in the Beta release.

### **SmartMCP Agent V1.4 (Legacy)**
*   **Implicit Search:** Added logic to proactively search memories based on user intent.
*   **Documentation:** Comprehensive documentation overhaul.

### **SmartMCP Agent V1.3 (2025-11-23)**
*   **WebUI Launch:** Introduced the Flask-based Web Interface.
*   **Calendar View:** Added visual timeline of memory creation.
*   **Edit Tracking:** Detailed edit history logged in memory content body.
*   **UI Enhancements:** List/Grid views, responsive design.

### **SmartMCP Agent V1.2 (2025-11-23)**
*   **Dark Theme:** Modern dark theme for WebUI.
*   **Modals:** View/Edit/Delete operations via modals.
*   **Auto-Timestamp:** Automatic timestamping on edits.

### **SmartMCP Agent V1.1 (2025-11-23)**
*   **Timezone Awareness:** Timestamps now support timezones.
*   **Enhanced Search:** Improved search by title, key, and content.

### **SmartMCP Agent V1.0 RC (2025-11-23)**
*   **Initial Release:** OS-agnostic MCP server.
*   **Memory Manager:** JSON-based storage with `core.memory_manager`.
*   **Basic CRUD:** `store_memory` and `retrieve_memory` tools.

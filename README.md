<div align="center">

![ContextKeep Banner](assets/banner.png)

# ContextKeep 🧠
### Infinite Long-Term Memory for AI Agents

[![Status: Beta](https://img.shields.io/badge/Status-Beta-blue?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![Platform: Linux | Windows | macOS](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=for-the-badge)](https://github.com/mordang7/ContextKeep)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![MCP Compliant](https://img.shields.io/badge/MCP-Compliant-green.svg?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.com/paypalme/GeekJohn)

**ContextKeep** is a powerful, standalone memory server that gives your AI tools (Claude, Cursor, VS Code, Gemini, OpenCode) a persistent, searchable brain. Stop repeating yourself—let your AI remember.

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Web Dashboard](#-web-dashboard) • [Configuration](#-configuration)

</div>

---

## 🌟 Features

*   **♾️ Infinite Context:** Store unlimited project details, preferences, and snippets.
*   **💰 Save Money & Tokens:** Reduce context window usage by only retrieving relevant memories, lowering API costs.
*   **🔌 Universal Compatibility:** Works with *any* MCP-compliant client via Stdio (Local) or SSE (Remote).
*   **🖥️ Modern Web Dashboard:** Manage your memories visually with Grid, List, and Calendar views.
*   **🔒 Privacy First:** 100% local storage. Your data never leaves your machine.
*   **🔎 Smart Search:** Find exactly what you need with semantic and keyword search.
*   **🐧 Linux Service:** Runs silently in the background as a system service.

---

![ContextKeep Showcase](assets/Showcase.png)

---

## 🚀 Installation

### Prerequisites
*   Python 3.10 or higher
*   Git (optional)

### Quick Start
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mordang7/ContextKeep.git
    cd ContextKeep
    ```

2.  **Run the Installer:**
    *   **Linux/Mac:**
        ```bash
        python3 install.py
        ```
    *   **Windows:**
        ```powershell
        python install.py
        ```

3.  **Follow the Wizard:** The installer will create a virtual environment, install dependencies, and generate a custom configuration file for you.

---

## 🔌 Configuration

After installation, you will find a `mcp_config.json` file in the root directory. Copy its contents into your AI client's configuration.

### Example Configurations

#### 1. Claude Desktop / Gemini CLI (Local)
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

#### 2. Remote Access (SSH)
Perfect for running ContextKeep on a home server (e.g., Raspberry Pi) and accessing it from your laptop.
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

#### 3. SSE Mode (Http)
If you prefer HTTP transport (great for OpenCode or web apps):
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

ContextKeep includes a beautiful web interface to manage your memories.

*   **URL:** `http://localhost:5000`
*   **Features:**
    *   **Dashboard:** Overview of recent memories.
    *   **Calendar:** Visual timeline of your work.
    *   **Search:** Instant filtering.
    *   **CRUD:** Create, Read, Update, Delete memories manually.

**To start it manually:**
```bash
./venv/bin/python webui.py
```

---

## 🐧 Linux Service Setup (Optional)

Run ContextKeep as a background service (systemd) on Linux/WSL:

```bash
chmod +x install_services.sh
./install_services.sh
```

This will install:
*   `contextkeep-server` (Port 5100)
*   `contextkeep-webui` (Port 5000)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ☕ Support the Project

If ContextKeep helps you build cool things, consider buying me a coffee!

<a href="https://www.paypal.com/paypalme/GeekJohn">
  <img src="https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal" alt="Donate with PayPal" />
</a>

---

<div align="center">
  <sub>Built with ❤️ by GeekJohn</sub>
</div>

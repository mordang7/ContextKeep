# ContextKeep 🧠
**Infinite Long-Term Memory for your AI**

ContextKeep is a digital notebook for your AI. It allows your AI (like Claude, Cursor, or VS Code) to remember your project details, preferences, and past conversations forever.

## Why use ContextKeep?
- **Stop Repeating Yourself**: Don't paste the same project context over and over.
- **Save Money**: Reduce token usage by only retrieving what's needed.
- **Privacy First**: Your data stays on your machine.

---

## 🚀 Quick Start Guide

### 1. Installation
1.  **Download** this folder to your computer.
2.  **Run the Installer**:
    - **Windows**: Double-click `install.py` (if Python is installed) or run `python install.py` in a terminal.
    - **Linux/Mac**: Run `python3 install.py` in a terminal.
3.  **Follow the prompts**: The installer will set everything up for you.

### 2. Connect to your AI
The installer will generate a file called `mcp_config.json`.
1.  Open `mcp_config.json`.
2.  Copy the contents.
3.  Paste it into your AI's configuration file (e.g., `claude_desktop_config.json` or your IDE's MCP settings).
4.  **Restart your AI**.

### 3. Start Using It!
Just talk to your AI naturally. It now has new tools to remember things.

**Examples:**
- "Remember that my server IP is 192.168.1.50"
- "What was I working on yesterday?"
- "Search my memories for 'database schema'"

---

## 🌐 Web Interface
ContextKeep comes with a beautiful dashboard to view and manage your memories.
- **URL**: `http://localhost:5000`
- **Features**: Calendar view, search, edit, and delete memories manually.

To start the WebUI manually, run:
```bash
./venv/bin/python webui.py
```
*(Or use the `python` executable in the `venv/Scripts` folder on Windows)*

---

## 🐧 Linux/WSL Service Setup (Optional)
If you are on Linux, you can make ContextKeep run automatically in the background.

1.  Run the service installer:
    ```bash
    chmod +x install_services.sh
    ./install_services.sh
    ```
2.  That's it! ContextKeep will now start when your computer turns on.

---

## 🛠️ Advanced
- **Configuration**: See `mcp_config.example.json` for manual setup.
- **Logs**: Check the `logs/` folder if something goes wrong.

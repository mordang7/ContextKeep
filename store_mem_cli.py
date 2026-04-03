import sys
import os
from pathlib import Path

from core.memory_manager import memory_manager

key = "Valheim_Plus_Forge_Project_State"
title = "Valheim Plus Forge Project State"
tags = ["project", "electron", "valheim", "config-editor", "v0.7"]
content = """Active project: Valheim Plus Forge. 
Location: d:\\AI Shared\\AI_CLI_Projects\\J_Useful_Apps\\Valheim_Plus_Forge. 
Current Version: V0.7 (Electron Matrix). 
Tech Stack: Electron, Vanilla JS. 
Key Features: Native Config Editing, Silent Auto-Backup (to backups/ folder), Restore Backup System. 
Release Folder: Windows_Release_V0.7. 
Legacy: Windows_Release_V0.6."""

try:
    result = memory_manager.store_memory(key, content, tags, title)
    print(f"SUCCESS: Stored memory '{result['title']}'")
except Exception as e:
    print(f"ERROR: {e}")

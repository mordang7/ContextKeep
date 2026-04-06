import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def print_header():
    print("="*60)
    print("      ContextKeep V1.3 Harbor — Installation Wizard")
    print("="*60)
    print()

def check_python():
    print("[*] Checking Python version...")
    if sys.version_info < (3, 10):
        print("[-] Error: Python 3.10 or higher is required.")
        sys.exit(1)
    print(f"[+] Python {sys.version_info.major}.{sys.version_info.minor} detected.")

def check_uv():
    """Check if uv is available on PATH."""
    return shutil.which("uv") is not None

def create_venv():
    print("\n[*] Setting up virtual environment...")
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("    - Virtual environment already exists.")
    else:
        print("    - Creating new virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    
    # Return path to python executable in venv
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"

def install_with_uv():
    """Install dependencies using uv (fast Python package manager)."""
    print("\n[*] Installing dependencies with uv...")
    try:
        subprocess.check_call(["uv", "sync"])
        print("[+] Dependencies installed via uv.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] uv sync failed: {e}")
        return False

def install_with_pip(python_path):
    """Install dependencies using pip (traditional method)."""
    print("\n[*] Installing dependencies with pip...")
    try:
        subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", "requirements.txt"])
        print("[+] Dependencies installed via pip.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing dependencies: {e}")
        sys.exit(1)

def generate_config(python_path):
    print("\n[*] Generating configuration...")
    
    server_script = Path("server.py").resolve()
    
    config = {
        "mcpServers": {
            "context-keep": {
                "command": str(python_path.resolve()),
                "args": [str(server_script)]
            }
        }
    }
    
    config_path = Path("mcp_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"[+] Created {config_path.name}")
    return config

def main():
    print_header()
    check_python()
    
    has_uv = check_uv()
    
    print("\nThis installer will set up ContextKeep and install dependencies.")
    if has_uv:
        print("  ✓ uv detected — will use uv for fast installation.")
    else:
        print("  • uv not found — will use pip + venv (classic method).")
        print("  💡 Tip: Install uv for faster setup: https://docs.astral.sh/uv/")
    
    print("\n🐳 Docker alternative: docker compose up --build")
    
    if input("\nProceed with local install? [Y/n]: ").lower().strip() == 'n':
        print("Installation aborted.")
        sys.exit(0)
    
    if has_uv:
        if install_with_uv():
            # uv creates its own venv, get the python path from it
            if os.name == "nt":
                python_path = Path(".venv") / "Scripts" / "python.exe"
            else:
                python_path = Path(".venv") / "bin" / "python"
        else:
            print("[!] Falling back to pip...")
            python_path = create_venv()
            install_with_pip(python_path)
    else:
        python_path = create_venv()
        install_with_pip(python_path)
    
    generate_config(python_path)
    
    print("\n" + "="*60)
    print("      Installation Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Open your Claude Desktop App or IDE configuration file.")
    print(f"2. Copy the contents of '{Path('mcp_config.json').resolve()}' into your config file.")
    print("3. Restart your IDE/Claude App.")
    print("\nYour memories will be stored in the 'data/memories' folder.")
    print("\nEnjoy ContextKeep V1.3 Harbor! 🚀")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

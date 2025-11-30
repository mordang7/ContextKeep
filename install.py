import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def print_header():
    print("="*60)
    print("      ContextKeep V1.0 - Installation Wizard")
    print("="*60)
    print()

def check_python():
    print("[*] Checking Python version...")
    if sys.version_info < (3, 10):
        print("[-] Error: Python 3.10 or higher is required.")
        sys.exit(1)
    print(f"[+] Python {sys.version_info.major}.{sys.version_info.minor} detected.")

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

def install_dependencies(python_path):
    print("\n[*] Installing dependencies...")
    try:
        subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", "requirements.txt"])
        print("[+] Dependencies installed.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing dependencies: {e}")
        sys.exit(1)

def generate_config(python_path):
    print("\n[*] Generating configuration...")
    
    server_script = Path("server.py").resolve()
    
    # Create the config dictionary
    # We use the absolute path to the venv python and the server script
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
    
    print("\nThis installer will set up a local virtual environment and")
    print("install necessary dependencies for ContextKeep.")
    print("It will also generate the configuration needed for your IDE.")
    
    if input("\nProceed? [Y/n]: ").lower().strip() == 'n':
        print("Installation aborted.")
        sys.exit(0)
        
    python_path = create_venv()
    install_dependencies(python_path)
    
    generate_config(python_path)
    
    print("\n" + "="*60)
    print("      Installation Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Open your Claude Desktop App or IDE configuration file.")
    print(f"2. Copy the contents of '{Path('mcp_config.json').resolve()}' into your config file.")
    print("3. Restart your IDE/Claude App.")
    print("\nYour memories will be stored in the 'data/memories' folder.")
    print("\nEnjoy your new memory!")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

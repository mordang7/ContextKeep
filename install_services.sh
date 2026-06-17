#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "      ContextKeep V2.1 Service Installer"
echo "=========================================="
echo ""

if [ -n "${SUDO_USER:-}" ]; then
    CURRENT_USER="$SUDO_USER"
else
    CURRENT_USER="$(whoami)"
fi

CURRENT_DIR="$(pwd)"

if [ -x "$CURRENT_DIR/.venv/bin/python" ]; then
    PYTHON="$CURRENT_DIR/.venv/bin/python"
elif [ -x "$CURRENT_DIR/venv/bin/python" ]; then
    PYTHON="$CURRENT_DIR/venv/bin/python"
else
    echo "Could not find .venv/bin/python or venv/bin/python."
    echo "Run python install.py first, then rerun this installer."
    exit 1
fi

echo "[*] User: $CURRENT_USER"
echo "[*] Directory: $CURRENT_DIR"
echo "[*] Python: $PYTHON"
echo ""

mkdir -p "$CURRENT_DIR/logs" "$CURRENT_DIR/data"
chown -R "$CURRENT_USER" "$CURRENT_DIR/logs" "$CURRENT_DIR/data"

install_service() {
    local template="$1"
    local service_name="$2"

    echo "[*] Installing $service_name..."

    if [ ! -f "$template" ]; then
        echo "Template not found: $template"
        exit 1
    fi

    sed -e "s|{{USER}}|$CURRENT_USER|g" \
        -e "s|{{WORKDIR}}|$CURRENT_DIR|g" \
        -e "s|{{PYTHON}}|$PYTHON|g" \
        "$template" > "$service_name.tmp"

    sudo mv "$service_name.tmp" "/etc/systemd/system/$service_name"
    sudo systemctl enable "$service_name"
    sudo systemctl restart "$service_name"
    echo "[+] $service_name installed and started."
}

install_service "contextkeep-server.service" "contextkeep-server.service"
install_service "contextkeep-webui.service" "contextkeep-webui.service"

sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "      Installation Complete"
echo "=========================================="
echo "WebUI: http://<host>:5000"
echo "MCP HTTP: http://<host>:5100/mcp"
echo ""
echo "Replace <host> with this machine's hostname or IP address."

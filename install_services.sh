#!/bin/bash
# Install ContextKeep V1.0 Services (Server + WebUI)

echo "=========================================="
echo "      ContextKeep V1.0 - Service Installer     "
echo "=========================================="
echo ""

# Get current user and directory
# If running as sudo, get the original user
if [ -n "$SUDO_USER" ]; then
    CURRENT_USER="$SUDO_USER"
else
    CURRENT_USER=$(whoami)
fi

CURRENT_DIR=$(pwd)

echo "[*] Detected User: $CURRENT_USER"
echo "[*] Detected Directory: $CURRENT_DIR"
echo ""

# Create logs directory
mkdir -p "$CURRENT_DIR/logs"
chown -R "$CURRENT_USER" "$CURRENT_DIR/logs"

# Function to install a service
install_service() {
    TEMPLATE=$1
    SERVICE_NAME=$2
    
    echo "[*] Installing $SERVICE_NAME..."
    
    if [ ! -f "$TEMPLATE" ]; then
        echo "[-] Error: Template $TEMPLATE not found!"
        return
    fi
    
    # Replace placeholders and write to temp file
    # We use | as delimiter for sed to handle slashes in paths
    sed -e "s|{{USER}}|$CURRENT_USER|g" \
        -e "s|{{WORKDIR}}|$CURRENT_DIR|g" \
        "$TEMPLATE" > "$SERVICE_NAME.tmp"
        
    # Move to systemd directory
    sudo mv "$SERVICE_NAME.tmp" "/etc/systemd/system/$SERVICE_NAME"
    
    # Enable and start
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME"
    
    echo "[+] $SERVICE_NAME installed and started."
}

# Install both services
install_service "contextkeep-server.service" "contextkeep-server.service"
install_service "contextkeep-webui.service" "contextkeep-webui.service"

# Reload daemon once
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "      Installation Complete!              "
echo "=========================================="
echo "WebUI: http://$(hostname -I | awk '{print $1}'):5000"
echo "MCP Server (SSE): http://$(hostname -I | awk '{print $1}'):5100/sse"
echo ""

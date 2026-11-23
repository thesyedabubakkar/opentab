#!/bin/bash
set -e

echo "=============================================================="
echo " Starting OpenTab Autonomous Agent on Render.com 24/7 Cloud  "
echo "=============================================================="

# If WhatsApp is enabled, start the Node.js Baileys bridge in background
if [ "$ENABLE_WHATSAPP" = "True" ] || [ "$ENABLE_WHATSAPP" = "true" ]; then
    echo "[*] Launching Node.js WhatsApp Bridge service..."
    node channels/whatsapp_service.js &
fi

# Launch Python Agent in foreground
echo "[*] Launching OpenTab Agent Engine on port ${PORT:-10000}..."
exec python main.py --mode all

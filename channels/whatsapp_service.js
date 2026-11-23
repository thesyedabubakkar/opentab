/**
 * OpenTab WhatsApp Gateway
 * 100% Free & Open-Source WhatsApp Multi-Device Bridge (Powered by Baileys)
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const http = require('http');
const path = require('path');
const fs = require('fs');

const AUTH_DIR = path.join(__dirname, '..', 'data', 'baileys_auth');
const PYTHON_WEBHOOK_URL = process.env.WHATSAPP_WEBHOOK_URL || 'http://localhost:8000/webhook/whatsapp';
const PORT = parseInt(process.env.WHATSAPP_PORT || '3001', 10);

let sock = null;

async function startWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  sock = makeWASocket({
    auth: state,
    printQRInTerminal: false,
    logger: require('pino')({ level: 'silent' })
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('\n======================================================');
      console.log('   SCAN THIS QR CODE WITH YOUR WHATSAPP MOBILE APP   ');
      console.log('   (WhatsApp -> Linked Devices -> Link a Device)      ');
      console.log('======================================================\n');
      qrcode.generate(qr, { small: true });
    }

    if (connection === 'close') {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      console.log(`[*] WhatsApp connection closed (code: ${statusCode}). Reconnecting: ${shouldReconnect}`);
      if (shouldReconnect) {
        setTimeout(startWhatsApp, 3000);
      }
    } else if (connection === 'open') {
      console.log('[+] WhatsApp Connected Successfully! OpenTab is live on WhatsApp.');
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;

    for (const msg of messages) {
      if (!msg.message || msg.key.fromMe) continue;

      const sender = msg.key.remoteJid;
      const text = msg.message.conversation ||
                   msg.message.extendedTextMessage?.text ||
                   msg.message.imageMessage?.caption ||
                   '';

      if (!text.trim()) continue;

      console.log(`[WhatsApp Inbound] From ${sender}: ${text}`);

      // Forward to Python OpenTab Agent
      try {
        const payload = JSON.stringify({
          sender: sender,
          text: text,
          message_id: msg.key.id
        });

        const url = new URL(PYTHON_WEBHOOK_URL);
        const req = http.request({
          hostname: url.hostname,
          port: url.port,
          path: url.pathname,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(payload)
          }
        });

        req.on('error', (e) => console.error(`[!] Failed to forward to Python agent: ${e.message}`));
        req.write(payload);
        req.end();
      } catch (err) {
        console.error('[!] Forwarding error:', err);
      }
    }
  });
}

// Outbound HTTP Server: Allows Python Agent to reply to WhatsApp
const server = http.createServer(async (req, res) => {
  if (req.method === 'POST' && req.url === '/send') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        const { to, text, image_path, video_path, audio_path } = data;

        if (!sock) {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ error: 'WhatsApp socket not ready' }));
        }

        if (video_path && fs.existsSync(video_path)) {
          await sock.sendMessage(to, {
            video: fs.readFileSync(video_path),
            caption: text || '',
            mimetype: 'video/mp4'
          });
        } else if (audio_path && fs.existsSync(audio_path)) {
          await sock.sendMessage(to, {
            audio: fs.readFileSync(audio_path),
            mimetype: 'audio/mp4',
            ptt: true // Push to Talk (Voice Note)
          });
        } else if (image_path && fs.existsSync(image_path)) {
          await sock.sendMessage(to, {
            image: fs.readFileSync(image_path),
            caption: text || ''
          });
        } else if (text) {
          await sock.sendMessage(to, { text: text });
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'sent' }));
      } catch (err) {
        console.error('[!] Send error:', err);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(PORT, () => {
  console.log(`[*] WhatsApp Bridge outbound server running on port ${PORT}`);
  startWhatsApp().catch(err => console.error('[!] WhatsApp init error:', err));
});

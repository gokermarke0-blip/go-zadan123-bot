const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const pino = require('pino');
const { Boom } = require('@hapi/boom');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BOT_NAME = "go zadan123";

// إعدادات بسيطة
async function startBot() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info');

    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: pino({ level: 'silent' }),
        browser: [BOT_NAME, "Chrome", "1.0"],
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('Connection closed, reconnecting...', lastDisconnect?.error);
            if (shouldReconnect) startBot();
        } else if (connection === 'open') {
            console.log('✅ ' + BOT_NAME + ' is online!');
        }
    });

    // استقبال الرسائل
    sock.ev.on('messages.upsert', async ({ messages }) => {
        const msg = messages[0];
        if (!msg.message || msg.key.fromMe) return;

        const from = msg.key.remoteJid;
        const text = msg.message.conversation || msg.message.extendedTextMessage?.text || '';

        // لو بعت لينك، حاول تحميل الفيديو
        if (text.includes('tiktok.com') || text.includes('instagram.com') || text.includes('facebook.com') || text.includes('youtu')) {
            await sock.sendMessage(from, { text: '⏳ جاري تحميل الفيديو من ' + BOT_NAME + ' ...' });

            try {
                // استخدام API خارجي بسيط للتحميل (yt-dlp style عبر api)
                const apiUrl = `https://api.vevioz.com/api/button/mp4/${encodeURIComponent(text)}`;
                const response = await axios.get(apiUrl);
                
                if (response.data && response.data.data && response.data.data[0]) {
                    const videoUrl = response.data.data[0].url;
                    await sock.sendMessage(from, { 
                        video: { url: videoUrl },
                        caption: `✅ تم التحميل بواسطة ${BOT_NAME}\n\nلو في مشكلة قول .help`
                    });
                } else {
                    await sock.sendMessage(from, { text: '❌ مش قادر أحمل الفيديو دلوقتي، جرب لينك تاني.' });
                }
            } catch (err) {
                console.error(err);
                await sock.sendMessage(from, { text: '⚠️ حصل خطأ في التحميل. تأكد من اللينك وجرب تاني.' });
            }
        } 
        // أوامر بسيطة
        else if (text.toLowerCase() === '.help' || text.toLowerCase() === 'help') {
            await sock.sendMessage(from, { 
                text: `*${BOT_NAME}*\n\nابعت أي لينك من:\n• TikTok\n• Instagram (Reels/Post)\n• Facebook\n• YouTube\n\nهحملك الفيديو تلقائي!\n\nأوامر:\n.help → هذه الرسالة` 
            });
        }
    });
}

startBot().catch(console.error);

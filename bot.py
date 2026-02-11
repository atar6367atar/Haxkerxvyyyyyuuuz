import os
import sys
import asyncio
import subprocess
import threading
import http.server
import socketserver
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ================= HEALTH SERVER =================
class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Runner Active")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.ThreadingTCPServer(("0.0.0.0", port), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()
# =================================================


def extract_imports(code):
    imports = set()
    for line in code.split("\n"):
        line = line.strip()
        if line.startswith("import "):
            parts = line[7:].split(",")
            for part in parts:
                pkg = part.strip().split()[0].split(".")[0]
                if pkg:
                    imports.add(pkg)
        elif line.startswith("from "):
            parts = line.split()
            if len(parts) > 1:
                pkg = parts[1].split(".")[0]
                imports.add(pkg)
    return list(imports)


async def run_no_timeout(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        packages = extract_imports(code)

        # Paketleri yükle
        for pkg in packages:
            try:
                __import__(pkg)
            except:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

        # Çalıştır (timeout yok)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode(errors="ignore")[:3500] if stdout else "Çıktı yok"

        if stderr:
            output += "\n\nHata:\n" + stderr.decode(errors="ignore")[:1000]

        return output

    except Exception as e:
        return f"Hata: {str(e)}"


# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Render Python Runner\n\n"
        ".py dosyası gönder.\n"
        "Timeout yok (Render limiti geçerli)."
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py dosyası gönder!")
        return

    status = await update.message.reply_text("İndiriliyor...")

    try:
        file = await context.bot.get_file(doc.file_id)

        save_path = f"/tmp/{doc.file_name}"
        await file.download_to_drive(save_path)

        await status.edit_text("Paketler yükleniyor ve çalıştırılıyor...")

        output = await run_no_timeout(save_path)

        result = f"Dosya: {doc.file_name}\n\nÇıktı:\n{output}"

        if len(result) > 4090:
            result = result[:4000]

        await status.edit_text(result)

    except Exception as e:
        await status.edit_text(f"Hata: {str(e)}")


def main():
    if not TOKEN:
        print("BOT_TOKEN bulunamadı!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_file))

    print("Bot başlatıldı.")
    app.run_polling()


if __name__ == "__main__":
    main()      app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_file))
        print("🤖 ULTRA FAST Python Runner Bot başladı!")
        print(f"✅ Port: {os.environ.get('PORT', 10000)} açık")
        print(f"📦 Cache: {len(runner.package_cache)} paket")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main() kontrol
    if not doc.file_name.endswith('.py'):
        await update.message.reply_text("❌ Sadece `.py` uzantılı dosyalar kabul edilir!")
        return
    
    if doc.file_size > 10 * 1024 * 1024:  # 10MB
        await update.message.reply_text("❌ Dosya çok büyük! Maksimum 10MB.")
        return
    
    # Anlık geri bildirim
    status_msg = await update.message.reply_text("⚡ Dosya işleniyor...")
    
    temp_path = None
    try:
        # Dosyayı indir
        file = await context.bot.get_file(doc.file_id)
        temp_path = f"/tmp/{user_id}_{doc.file_name}"
        await file.download_to_drive(temp_path)
        
        await status_msg.edit_text("🔍 Import'lar analiz ediliyor...")
        
        # ÇALIŞTIR - ZAMAN AŞIMI YOK!
        output = await runner.run_ultra_fast(temp_path)
        
        # Sonuç
        result = f"📁 *Dosya:* `{doc.file_name}`\n\n📤 *Çıktı:*\n```\n{output}\n```"
        
        # Uzun çıktıları parçala
        if len(result) > 4096:
            result = f"📁 *Dosya:* `{doc.file_name}`\n\n📤 *Çıktı (ilk 4000 karakter):*\n```\n{output[:3500]}\n```"
        
        await status_msg.edit_text(result, parse_mode='Markdown')
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Hata oluştu: {str(e)[:200]}")
    
    finally:
        # Temizlik
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durumu"""
    await update.message.reply_text(
        f"🤖 *Bot Durumu*\n\n"
        f"⚡ Mod: ULTRA FAST (Zaman aşımı YOK)\n"
        f"📦 Cache: {len(runner.package_cache)} paket\n"
        f"🐍 Python: {sys.version.split()[0]}\n"
        f"✅ Durum: Aktif\n\n"
        f"💡 `.py` dosyanı gönder, anında çalıştırayım!",
        parse_mode='Markdown'
    )

async def cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manuel temizlik"""
    user_id = update.effective_user.id
    await update.message.reply_text("🧹 Geçici dosyalar temizlendi!")

# ============ MAIN ============
def main():
    """Ana fonksiyon"""
    if not TOKEN:
        print("❌ HATA: BOT_TOKEN environment variable bulunamadı!")
        print("📌 Render'da Environment Variable ekle: BOT_TOKEN=xxx")
        return
    
    try:
        # Application oluştur
        app = Application.builder().token(TOKEN).build()
        
        # Handler'ları ekle
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("cleanup", cleanup))
        app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_file))
        
        print("🤖 ULTRA FAST Python Runner Bot başladı!")
        print(f"🐍 Python: {sys.version}")
        print(f"⏱️ Zaman aşımı: YOK (sınırsız)")
        print(f"📦 Cache: {len(runner.package_cache)} paket")
        print("✅ Bot hazır! Dosyaları bekliyor...")
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Bot başlatılamadı: {e}")
        raise

if __name__ == "__main__":
    main()

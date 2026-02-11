import os
import sys
import asyncio
import subprocess
import threading
import http.server
import socketserver
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ================= HEALTH SERVER =================

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot Active")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.ThreadingTCPServer(("0.0.0.0", port), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

# ================= IMPORT TESPIT =================

def extract_imports(code):
    imports = set()
    for line in code.split("\n"):
        line = line.strip()

        if line.startswith("import "):
            parts = line.replace("import ", "").split(",")
            for part in parts:
                pkg = part.strip().split(" ")[0].split(".")[0]
                if pkg:
                    imports.add(pkg)

        elif line.startswith("from "):
            parts = line.split()
            if len(parts) > 1:
                pkg = parts[1].split(".")[0]
                if pkg:
                    imports.add(pkg)

    return list(imports)

# ================= RUNNER =================

async def run_code(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        packages = extract_imports(code)

        # Paketleri yükle (timeout yok)
        for pkg in packages:
            try:
                __import__(pkg)
            except:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

        # Çalıştır (timeout YOK)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode(errors="ignore") if stdout else "Çıktı yok"

        if stderr:
            output += "\n\nHata:\n" + stderr.decode(errors="ignore")

        return output[:4000]

    except Exception as e:
        return f"Hata: {str(e)}"

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Python Runner Bot\n\n"
        ".py dosyası gönder.\n"
        "Timeout yok (Render limiti geçerlidir)."
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py dosyası gönder!")
        return

    await update.message.reply_text("Dosya indiriliyor...")

    try:
        file = await context.bot.get_file(document.file_id)

        save_path = f"/tmp/{document.file_name}"
        await file.download_to_drive(save_path)

        await update.message.reply_text("Paketler yükleniyor ve çalıştırılıyor...")

        output = await run_code(save_path)

        await update.message.reply_text(f"Çıktı:\n{output}")

    except Exception as e:
        await update.message.reply_text(f"Hata: {str(e)}")

# ================= MAIN =================

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
    main()

import os
import sys
import asyncio
import subprocess
import threading
import http.server
import socketserver
import re
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

STD_LIBS = {
    "sys","os","re","json","time","datetime","math","random","collections",
    "itertools","functools","pathlib","typing","uuid","hashlib","base64",
    "copy","enum","socket","threading","asyncio","subprocess","http",
    "socketserver"
}

def extract_imports(code):
    imports = set()

    pattern1 = re.findall(r'^\s*import\s+([a-zA-Z0-9_., ]+)', code, re.MULTILINE)
    pattern2 = re.findall(r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import', code, re.MULTILINE)

    for match in pattern1:
        parts = match.split(",")
        for p in parts:
            pkg = p.strip().split(" as ")[0].split(".")[0]
            if pkg and pkg not in STD_LIBS:
                imports.add(pkg)

    for match in pattern2:
        pkg = match.split(".")[0]
        if pkg and pkg not in STD_LIBS:
            imports.add(pkg)

    return list(imports)

# ================= PIP INSTALLER =================

def install_package(pkg):
    try:
        __import__(pkg)
        return False
    except:
        pass

    possible_names = [
        pkg,
        pkg.replace("_", "-"),
        pkg.replace("-", "_")
    ]

    for name in possible_names:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except:
            continue

    return False

# ================= RUNNER =================

async def run_code(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        packages = extract_imports(code)

        installed = []

        for pkg in packages:
            result = install_package(pkg)
            if result:
                installed.append(pkg)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        output = ""

        if installed:
            output += "Yüklenen Paketler:\n" + ", ".join(installed) + "\n\n"

        if stdout:
            output += stdout.decode(errors="ignore")

        if stderr:
            output += "\n\nHata:\n" + stderr.decode(errors="ignore")

        return output[:4000] if output else "Çıktı yok"

    except Exception as e:
        return f"Hata: {str(e)}"

# ================= TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ultra Python Runner\n\n"
        "Tüm importları otomatik kurar.\n"
        "Timeout yok (Render limiti geçerli)."
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith(".py"):
        await update.message.reply_text("Sadece .py dosyası gönder!")
        return

    await update.message.reply_text("İndiriliyor ve analiz ediliyor...")

    try:
        file = await context.bot.get_file(document.file_id)
        save_path = f"/tmp/{document.file_name}"
        await file.download_to_drive(save_path)

        await update.message.reply_text("Paketler kuruluyor ve çalıştırılıyor...")

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

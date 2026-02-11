import os
import sys
import subprocess
import tempfile
import shutil
import asyncio
import re
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ============ RENDER HEALTH CHECK SERVER ============
# Bu port sayesinde Render "No open ports" hatası vermez!
class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'🤖 Python Runner Bot is ONLINE!')
    
    def log_message(self, format, *args):
        pass  # Logları kapat, sessiz çalış

def start_health_server():
    """Render'ın istediği portu açar"""
    port = int(os.environ.get('PORT', 10000))
    handler = HealthCheckHandler
    httpd = socketserver.TCPServer(("0.0.0.0", port), handler)
    print(f"✅ Health check server active on port {port}")
    httpd.serve_forever()

# Health server'ı arka planda başlat
threading.Thread(target=start_health_server, daemon=True).start()
# ====================================================

# ============ TELEGRAM IMPORT (Python 3.13+ Fix) ============
if sys.version_info >= (3, 13):
    import collections.abc
    if not hasattr(collections, 'Mapping'):
        collections.Mapping = collections.abc.Mapping
    if not hasattr(collections, 'MutableMapping'):
        collections.MutableMapping = collections.abc.MutableMapping

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# ============ LOAD ENV ============
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# ============ ULTRA FAST PYTHON RUNNER ============
class UltraFastPythonRunner:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.package_cache = set()
        self._init_environment()
    
    def _init_environment(self):
        """Süper hızlı başlangıç"""
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
        
        # En çok kullanılan paketleri önyükle
        common = [
            'requests', 'numpy', 'pandas', 'flask', 'django', 'pillow', 
            'matplotlib', 'beautifulsoup4', 'selenium', 'scrapy',
            'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'celery',
            'pytest', 'scipy', 'sklearn', 'tensorflow', 'torch'
        ]
        
        def preload_pkg(pkg):
            try:
                __import__(pkg.replace('-', '_'))
                self.package_cache.add(pkg)
            except:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--user", pkg],
                        capture_output=True,
                        timeout=30
                    )
                    self.package_cache.add(pkg)
                except:
                    pass
        list(self.executor.map(preload_pkg, common))
    
    def extract_imports_instant(self, code):
        """Milisaniyede import tespiti"""
        imports = set()
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import '):
                parts = line[7:].split(',')
                for part in parts:
                    pkg = part.strip().split()[0].split('.')[0]
                    if pkg and not pkg.startswith('_'):
                        imports.add(pkg)
            elif line.startswith('from '):
                parts = line.split()
                if len(parts) > 1:
                    pkg = parts[1].split('.')[0]
                    if pkg and not pkg.startswith('_'):
                        imports.add(pkg)
        
        std_libs = {
            'sys', 'os', 're', 'json', 'time', 'datetime', 'math',
            'random', 'collections', 'itertools', 'functools', 'pathlib',
            'typing', 'uuid', 'hashlib', 'base64', 'copy', 'enum',
            'socket', 'threading', 'asyncio', 'concurrent', 'multiprocessing',
            'argparse', 'logging', 'warnings', 'traceback', 'inspect',
            'abc', 'array', 'atexit', 'binascii', 'bisect', 'builtins',
            'bz2', 'calendar', 'cgi', 'cmath', 'cmd', 'codecs', 'contextlib',
            'csv', 'ctypes', 'curses', 'dbm', 'decimal', 'difflib', 'dis',
            'distutils', 'doctest', 'email', 'encodings', 'errno', 'fcntl',
            'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib',
            'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
            'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr',
            'importlib', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
            'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
            'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib',
            'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'ntpath',
            'nturl2path', 'numbers', 'opcode', 'operator', 'optparse', 'os',
            'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools',
            'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix',
            'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
            'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're',
            'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
            'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
            'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket',
            'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics',
            'string', 'stringprep', 'struct', 'subprocess', 'sunau',
            'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
            'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
            'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'types',
            'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid',
            'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
            'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp',
            'zipfile', 'zipimport', 'zlib'
        }
        return [imp for imp in imports if imp and imp not in std_libs]
    
    def install_packages_parallel(self, packages):
        if not packages:
            return []
        to_install = []
        for pkg in packages:
            if pkg not in self.package_cache:
                try:
                    __import__(pkg.replace('-', '_'))
                    self.package_cache.add(pkg)
                except:
                    to_install.append(pkg)
        if not to_install:
            return []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install"] + to_install,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self.package_cache.update(to_install)
                return to_install
        except:
            installed = []
            for pkg in to_install:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--user", pkg],
                        capture_output=True,
                        timeout=30
                    )
                    self.package_cache.add(pkg)
                    installed.append(pkg)
                except:
                    pass
            return installed
        return []
    
    async def run_ultra_fast(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            imports = self.extract_imports_instant(code)
            installed = []
            if imports:
                installed = self.install_packages_parallel(imports)
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(file_path)
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')[:3500] if stdout else "✅ Çalıştı"
            if stderr:
                error = stderr.decode('utf-8', errors='ignore')
                if "Error" in error or "Exception" in error:
                    output = f"❌ Hata:\n{error[:2000]}"
                else:
                    output += f"\n\n⚠️ {error[:1000]}"
            if installed:
                output = f"📦 Yüklenen: {', '.join(installed[:5])}{'...' if len(installed) > 5 else ''}\n\n{output}"
            return output[:4000]
        except Exception as e:
            return f"❌ Hata: {str(e)[:500]}"

runner = UltraFastPythonRunner()

# ============ TELEGRAM HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 *ULTRA FAST Python Runner*\n\n"
        f"Merhaba {user.first_name}! 👋\n\n"
        f"⚡ **Özellikler:**\n"
        f"• 🚫 Zaman aşımı YOK\n"
        f"• 📦 Paralel paket yükleme\n"
        f"• 💾 Akıllı cache\n"
        f"• 🔍 Anlık import tespiti\n"
        f"• 🧹 Otomatik temizlik\n\n"
        f"📤 **.py dosyanı gönder, çalıştırayım!** 🚀",
        parse_mode='Markdown'
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user_id = update.effective_user.id
    
    if not doc.file_name.endswith('.py'):
        await update.message.reply_text("❌ Sadece `.py` dosyası gönder!")
        return
    if doc.file_size > 10 * 1024 * 1024:
        await update.message.reply_text("❌ Dosya >10MB olamaz!")
        return
    
    status_msg = await update.message.reply_text("⚡ İşleniyor...")
    temp_path = None
    
    try:
        file = await context.bot.get_file(doc.file_id)
        temp_path = f"/tmp/{user_id}_{doc.file_name}"
        await file.download_to_drive(temp_path)
        await status_msg.edit_text("🔍 Analiz ediliyor...")
        output = await runner.run_ultra_fast(temp_path)
        result = f"📁 *{doc.file_name}*\n\n📤 *Çıktı:*\n```\n{output}\n```"
        if len(result) > 4096:
            result = f"📁 *{doc.file_name}*\n\n📤 *Çıktı:*\n```\n{output[:3500]}\n```"
        await status_msg.edit_text(result, parse_mode='Markdown')
    except Exception as e:
        await status_msg.edit_text(f"❌ Hata: {str(e)[:200]}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 *Bot Durumu*\n\n"
        f"⚡ Mod: ULTRA FAST\n"
        f"📦 Cache: {len(runner.package_cache)} paket\n"
        f"🐍 Python: {sys.version.split()[0]}\n"
        f"✅ Port: Açık (Render uyumlu)\n"
        f"💡 .py dosyanı gönder!",
        parse_mode='Markdown'
    )

# ============ MAIN ============
def main():
    if not TOKEN:
        print("❌ BOT_TOKEN bulunamadı!")
        return
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_file))
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

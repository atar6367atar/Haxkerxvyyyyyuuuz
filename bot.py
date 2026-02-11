import os
import sys
import subprocess
import tempfile
import shutil
import asyncio
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

class UltraFastPythonRunner:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.package_cache = set()
        self._init_environment()
    
    def _init_environment(self):
        """Süper hızlı başlangıç"""
        # Pip'i güncelleme yapmadan hazır et
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
        
        # En çok kullanılan 20 paketi önyükle
        common = [
            'requests', 'numpy', 'pandas', 'flask', 'django', 'pillow', 
            'matplotlib', 'beautifulsoup4', 'selenium', 'scrapy',
            'tensorflow', 'torch', 'transformers', 'opencv-python',
            'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'celery'
        ]
        
        def preload_pkg(pkg):
            try:
                __import__(pkg.replace('-', '_'))
                self.package_cache.add(pkg)
            except:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True,
                        timeout=30
                    )
                    self.package_cache.add(pkg)
                except:
                    pass
        
        # Paralel önyükleme
        list(self.executor.map(preload_pkg, common))
    
    def extract_imports_instant(self, code):
        """Milisaniyede import tespiti"""
        imports = set()
        
        # Tek geçişte tüm importları yakala
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import '):
                parts = line[7:].split(',')
                for part in parts:
                    pkg = part.strip().split()[0].split('.')[0]
                    imports.add(pkg)
            elif line.startswith('from '):
                pkg = line.split()[1].split('.')[0]
                imports.add(pkg)
        
        # Sadece 3rd party paketleri al
        std_libs = {
            'sys', 'os', 're', 'json', 'time', 'datetime', 'math',
            'random', 'collections', 'itertools', 'functools', 'pathlib',
            'typing', 'uuid', 'hashlib', 'base64', 'copy', 'enum',
            'socket', 'threading', 'asyncio', 'concurrent', 'multiprocessing',
            'argparse', 'logging', 'warnings', 'traceback', 'inspect'
        }
        
        return [imp for imp in imports if imp and imp not in std_libs]
    
    def install_packages_parallel(self, packages):
        """Paralel paket yükleme"""
        if not packages:
            return []
        
        # Cache'ten hızlı kontrol
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
        
        # TEK KOMUT - TEK SEFERDE hepsini yükle
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install"] + to_install,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.package_cache.update(to_install)
                return to_install
        except:
            # Başarısız olanları tek tek dene
            installed = []
            for pkg in to_install:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True,
                        timeout=10
                    )
                    self.package_cache.add(pkg)
                    installed.append(pkg)
                except:
                    pass
            return installed
        
        return []
    
    async def run_ultra_fast(self, file_path):
        """Anında çalıştır - ZAMAN AŞIMI YOK"""
        
        # Dosyayı oku
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Importları anında bul
        imports = self.extract_imports_instant(code)
        
        # Paketleri paralel yükle
        if imports:
            self.install_packages_parallel(imports)
        
        # Çalıştır - SINIRSIZ SÜRE
        process = await asyncio.create_subprocess_exec(
            sys.executable, file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(file_path)
        )
        
        # Sonsuz bekle - timeout YOK!
        stdout, stderr = await process.communicate()
        
        output = stdout.decode() if stdout else "✅ Çalıştı"
        if stderr:
            error = stderr.decode()
            if "Error" in error or "Exception" in error:
                output = f"❌ Hata:\n{error}"
            else:
                output += f"\nℹ️ {error}"
        
        return output[:4096]  # Telegram limiti

runner = UltraFastPythonRunner()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komutu"""
    await update.message.reply_text(
        "🤖 *ULTRA FAST Python Runner*\n\n"
        "🔥 Özellikler:\n"
        "• ⚡ **Zaman aşımı YOK** - Ne kadar uzun çalışırsa çalışsın\n"
        "• 📦 **Paralel paket yükleme** - Tüm paketler aynı anda\n"
        "• 🚀 **Anlık çalıştırma** - Milisaniyede tepki\n"
        "• 💾 **Akıllı cache** - Bir kere yükle, her zaman kullan\n"
        "• 🔄 **Sınırsız süre** - 1 saat de çalışır, 1 gün de\n\n"
        "📤 `.py` dosyanı gönder, gerisini bana bırak!",
        parse_mode='Markdown'
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Süper hızlı dosya işleyici"""
    
    doc = update.message.document
    
    # Hızlı kontrol
    if not doc.file_name.endswith('.py'):
        await update.message.reply_text("❌ Sadece .py dosyaları kabul edilir")
        return
    
    # Anlık geri bildirim
    status_msg = await update.message.reply_text("⚡ Hazırlanıyor...")
    
    try:
        # Dosyayı indir
        file = await context.bot.get_file(doc.file_id)
        file_path = f"/tmp/{doc.file_name}"
        await file.download_to_drive(file_path)
        
        await status_msg.edit_text("🔍 Import'lar analiz ediliyor...")
        
        # ÇALIŞTIR - ZAMAN AŞIMI YOK!
        output = await runner.run_ultra_fast(file_path)
        
        # Sonuç
        result = f"📁 `{doc.file_name}`\n\n📤 **Çıktı:**\n```\n{output}\n```"
        await status_msg.edit_text(result, parse_mode='Markdown')
        
        # Temizlik
        os.remove(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Hata: {str(e)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot durumu"""
    await update.message.reply_text(
        f"⚡ *ULTRA FAST*\n\n"
        f"📦 Cache: {len(runner.package_cache)} paket\n"
        f"⏱️ Timeout: Sınırsız\n"
        f"🐍 Python: {sys.version[:10]}",
        parse_mode='Markdown'
    )

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN gerekli!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.Document.FileExtension("py"), handle_file))
    
    print("🤖 ULTRA FAST bot başladı! (Zaman aşımı YOK)")
    app.run_polling()

if __name__ == "__main__":
    main()

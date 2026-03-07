# ==================== RONDK - Süleymanili Kız Bot ====================
import os
import json
import random
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY')
GROUP_ID = int(os.environ.get('GROUP_ID', 0))

IRAQ_TZ = timezone(timedelta(hours=3))
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RondkBot:
    def __init__(self):
        self.isim = "Rondk"
        self.yas = 23
        self.sehir = "Süleymani"
        self.isim_varyasyonlari = ["rondk", "rndo", "rnde", "rund", "روندك"]
        self.kullanicilar_file = 'kullanicilar.json'
        self.konusmalar_file = 'konusmalar.json'
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.konusmalar = self.dosya_yukle(self.konusmalar_file, {})
        logger.info(f"🤫 {self.isim} başlatılıyor... (Yaş: {self.yas}, Şehir: {self.sehir})")
    
    def dosya_yukle(self, dosya_adi, varsayilan):
        try:
            with open(dosya_adi, 'r') as f:
                return json.load(f)
        except:
            with open(dosya_adi, 'w') as f:
                json.dump(varsayilan, f)
            return varsayilan
    
    def dosya_kaydet(self, dosya_adi, veri):
        with open(dosya_adi, 'w') as f:
            json.dump(veri, f, indent=2)
    
    def su_an(self):
        return datetime.now(IRAQ_TZ)
    
    def isim_var_mi(self, metin):
        metin_lower = metin.lower()
        return any(isim.lower() in metin_lower for isim in self.isim_varyasyonlari)
    
    async def cevap_ver(self, update, context):
        mesaj = update.message
        kullanici = mesaj.from_user
        metin = mesaj.text or ""
        
        prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Saat: {self.su_an().strftime('%H:%M')}
Kullanıcı: {kullanici.first_name}
Mesajı: "{metin}"
Kısa ve doğal cevap ver:
"""
        try:
            response = model.generate_content(prompt)
            cevap = response.text[:300]
            await mesaj.reply_text(cevap)
        except Exception as e:
            logger.error(f"Gemini hatası: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id == context.bot.id:
            return
        
        metin = update.message.text or ""
        
        if metin.startswith('/'):
            return
        
        ozel_sohbet = update.effective_chat.type == 'private'
        etiket_var = f"@{context.bot.username}" in metin
        isim_var = self.isim_var_mi(metin)
        
        if ozel_sohbet or etiket_var or isim_var:
            await asyncio.sleep(random.randint(1, 3))
            await self.cevap_ver(update, context)
    
    def run(self):
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        logger.info(f"🚀 {self.isim} çalışıyor...")
        app.run_polling()

if __name__ == "__main__":
    bot = RondkBot()
    bot.run()

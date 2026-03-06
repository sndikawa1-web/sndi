# ==================== RONDK - Süleymanili Kız Bot (ÖZEL HIZLI) ====================
import os
import json
import random
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ==================== AYARLAR ====================
TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY')
GROUP_ID = int(os.environ.get('GROUP_ID', 0))

# Irak Saati
IRAQ_TZ = timezone(timedelta(hours=3))

# Gemini'yi ayarla
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

# Loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== RONDK ====================
class RondkBot:
    def __init__(self):
        self.isim = "Rondk"
        self.yas = 23
        self.sehir = "Süleymani"
        
        # İsim varyasyonları
        self.isim_varyasyonlari = [
            "rondk", "rndo", "rnde", "rund", "روندك",
            "Rondk", "Rndo", "Rnde", "Rund", "روندك"
        ]
        
        # Dosya yolları
        self.kullanicilar_file = 'kullanicilar.json'
        self.konusmalar_file = 'konusmalar.json'
        
        # Verileri yükle
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.konusmalar = self.dosya_yukle(self.konusmalar_file, {})
        
        logger.info(f"🤫 {self.isim} başlatılıyor... (Yaş: {self.yas}, Şehir: {self.sehir})")
    
    def dosya_yukle(self, dosya_adi, varsayilan):
        try:
            with open(dosya_adi, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                json.dump(varsayilan, f, ensure_ascii=False, indent=2)
            return varsayilan
    
    def dosya_kaydet(self, dosya_adi, veri):
        with open(dosya_adi, 'w', encoding='utf-8') as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    
    def su_an(self):
        return datetime.now(IRAQ_TZ)
    
    def dil_tani(self, metin):
        kurtce_kelimeler = ['erê', 'na', 'slaw', 'çoni', 'başim', 'spas', 'min']
        for kelime in kurtce_kelimeler:
            if kelime in metin.lower():
                return "kurtce"
        return "turkce"
    
    def isim_var_mi(self, metin):
        """Metinde Rondk'un isim varyasyonları var mı?"""
        metin_lower = metin.lower()
        for isim in self.isim_varyasyonlari:
            if isim.lower() in metin_lower:
                return True
        return False
    
    async def gemini_cevap_al(self, prompt):
        """Gemini'den cevap al, hata olursa None döndür"""
        try:
            response = model.generate_content(prompt)
            return response.text[:300]  # Çok uzun olmasın
        except Exception as e:
            logger.error(f"Gemini hatası: {e}")
            return None
    
    async def cevap_ver(self, update, context):
        mesaj = update.message
        kullanici = mesaj.from_user
        kullanici_id = str(kullanici.id)
        metin = mesaj.text or ""
        
        # Kullanıcıyı kaydet
        if kullanici_id not in self.kullanicilar:
            self.kullanicilar[kullanici_id] = {
                'isim': kullanici.first_name,
                'username': kullanici.username,
                'ilk_gorusme': self.su_an().isoformat(),
                'konusma_sayisi': 0
            }
        
        self.kullanicilar[kullanici_id]['konusma_sayisi'] += 1
        self.kullanicilar[kullanici_id]['son_gorusme'] = self.su_an().isoformat()
        self.dosya_kaydet(self.kullanicilar_file, self.kullanicilar)
        
        dil = self.dil_tani(metin)
        
        # Yapay zeka prompt'u
        prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Kişiliğin: Sessiz, gözlemci, dedikoducu (ama seçici), mantıklı.
Sadece sana seslenildiğinde veya mesajın yanıtlandığında konuşuyorsun.
Şu an özel sohbet desin, samimi ve doğal konuş.

Saat: {self.su_an().strftime('%H:%M')}
Şehir: Süleymani
Kullanıcı: {kullanici.first_name}
Mesajı: "{metin}"
Dili: {dil}

Kısa ve doğal cevap ver (bot olduğunu belli etme):
"""
        
        # Gemini'den cevap al
        cevap = await self.gemini_cevap_al(prompt)
        
        # Eğer cevap geldiyse gönder
        if cevap:
            await mesaj.reply_text(cevap)
            
            # Konuşmayı kaydet
            self.konusmalar[f"{kullanici_id}_{self.su_an().timestamp()}"] = {
                'kullanici': kullanici_id,
                'mesaj': metin,
                'cevap': cevap,
                'zaman': self.su_an().isoformat()
            }
            self.dosya_kaydet(self.konusmalar_file, self.konusmalar)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Sadece grup ve özel mesajlar
        if update.effective_chat.type not in ['group', 'supergroup', 'private']:
            return
        
        # Kendi mesajlarına cevap verme
        if update.effective_user.id == context.bot.id:
            return
        
        mesaj = update.message
        if not mesaj or not mesaj.text:
            return
        
        metin = mesaj.text
        
        # Komutları cevaplama
        if metin.startswith('/'):
            return
        
        # Bot etiketlenmiş mi?
        bot_etiket = f"@{context.bot.username}"
        etiket_var = bot_etiket in metin
        
        # İsim varyasyonları var mı?
        isim_var = self.isim_var_mi(metin)
        
        # Mesaj yanıtlanmış mı?
        yanit_var = False
        if mesaj.reply_to_message and mesaj.reply_to_message.from_user.id == context.bot.id:
            yanit_var = True
        
        # Özel sohbet kontrolü
        ozel_sohbet = update.effective_chat.type == 'private'
        
        # Sabah namazı kontrolü (05:00-15:00)
        saat = self.su_an().hour
        uyuyor_mu = 5 <= saat < 15
        
        # Uyuyorsa ve özel değilse cevap verme
        if uyuyor_mu and not ozel_sohbet:
            return
        
        # Konuşma kontrolü
        konusacak_mi = False
        bekleme_suresi = 0
        
        if ozel_sohbet:
            # Özelde her zaman konuş, 1-3 saniye bekle
            konusacak_mi = True
            bekleme_suresi = random.randint(1, 3)
        elif etiket_var or isim_var or yanit_var:
            # Grupta etiket varsa konuş, 3-8 saniye bekle
            konusacak_mi = True
            bekleme_suresi = random.randint(3, 8)
        elif random.random() < 0.05:  # %5 ihtimalle kendiliğinden
            konusacak_mi = True
            bekleme_suresi = random.randint(5, 15)
        
        if konusacak_mi:
            # Bekleme süresi kadar bekle
            await asyncio.sleep(bekleme_suresi)
            # Cevap ver
            await self.cevap_ver(update, context)
    
    def run(self):
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"🚀 {self.isim} çalışıyor... (Şehir: {self.sehir})")
        app.run_polling()

# ==================== BAŞLAT ====================
if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ BOT_TOKEN bulunamadı!")
        exit(1)
    if not GEMINI_KEY:
        logger.error("❌ GEMINI_KEY bulunamadı!")
        exit(1)
    
    bot = RondkBot()
    bot.run()

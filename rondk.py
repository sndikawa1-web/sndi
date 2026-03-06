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
        self.sehir = "Süleymani"  # Değiştirildi
        
        # İsim varyasyonları (bunlara da cevap ver)
        self.isim_varyasyonlari = [
            "rondk", "rndo", "rnde", "rund", "روندك",
            "Rondk", "Rndo", "Rnde", "Rund", "روندك"
        ]
        
        # Dosya yolları
        self.kullanicilar_file = 'kullanicilar.json'
        self.kuyruk_file = 'kuyruk.json'
        self.konusmalar_file = 'konusmalar.json'
        
        # Verileri yükle
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.kuyruk = self.dosya_yukle(self.kuyruk_file, [])
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
    
    def saat_kontrol(self):
        saat = self.su_an().hour
        dakika = self.su_an().minute
        toplam_dakika = saat * 60 + dakika
        
        # Sabah namazından sonra (05:00 - 15:00)
        if 300 <= toplam_dakika < 900:
            return "uyuyor", 10*60*60  # 10 saat
        
        # Öğleden sonra (15:00 - 18:00)
        elif 900 <= toplam_dakika < 1080:
            return "uyanik", random.randint(300, 1800)
        
        # Akşam (18:00 - 00:00)
        elif 1080 <= toplam_dakika < 1440:
            return "aktif", random.randint(300, 600)
        
        # Gece (00:00 - 05:00)
        else:
            return "dedikodu", random.randint(60, 300)
    
    def dil_tani(self, metin):
        kurtce_kelimeler = ['erê', 'na', 'slaw', 'çoni', 'başim', 'spas', 'min', 'rondk']
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
    
    async def cevap_ver(self, update, context, bekleme_suresi):
        await asyncio.sleep(bekleme_suresi)
        
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
        durum, _ = self.saat_kontrol()
        
        # Yapay zeka prompt'u
        prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Kişiliğin: Sessiz, gözlemci, dedikoducu (ama seçici), mantıklı.
Sadece sana seslenildiğinde veya mesajın yanıtlandığında konuşuyorsun.
Gece yarısı (00:00-05:00) daha konuşkan ve dedikoducusun.
Sabah namazından sonra (05:00-15:00) uyuyorsun.

Şu an: {durum}
Saat: {self.su_an().strftime('%H:%M')}
Şehir: Süleymani
Kullanıcı: {kullanici.first_name}
Mesajı: "{metin}"
Dili: {dil}

Kısa ve doğal cevap ver (bot olduğunu belli etme). Süleymani aksanıyla konuş:
"""
        
        try:
            response = model.generate_content(prompt)
            cevap = response.text[:300]
        except Exception as e:
            logger.error(f"Gemini hatası: {e}")
            hazir_cevaplar = [
                "Slaw, çonî?",
                "Başim, tu çonî?",
                "Evet, haklısın.",
                "Yok ya öyle deme.",
                "Bence de.",
                "Valla bilmiyorum.",
                "Heval, çi dibêjî?"
            ]
            cevap = random.choice(hazir_cevaplar)
        
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
        
        # Bot etiketlenmiş mi? (normal etiket)
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
        
        durum, bekleme = self.saat_kontrol()
        
        # Uyuyorsa kuyruğa ekle
        if durum == "uyuyor" and (etiket_var or isim_var or yanit_var or ozel_sohbet):
            self.kuyruk.append({
                'update_id': update.update_id,
                'zaman': self.su_an().isoformat(),
                'bekleme': bekleme
            })
            self.dosya_kaydet(self.kuyruk_file, self.kuyruk)
            return
        
        # Konuşma kontrolü
        konusacak_mi = False
        
        if etiket_var or isim_var or yanit_var or ozel_sohbet:
            konusacak_mi = True  # Direkt seslenilince %100
        elif durum == "dedikodu" and random.random() < 0.5:
            konusacak_mi = True  # Gece %50 konuşur
        elif random.random() < 0.1:
            konusacak_mi = True  # Normalde %10
        
        if konusacak_mi:
            await self.cevap_ver(update, context, bekleme)
    
    async def kuyruk_kontrol(self, context):
        yeni_kuyruk = []
        for kayit in self.kuyruk:
            giris_zamani = datetime.fromisoformat(kayit['zaman'])
            gecen_sure = (self.su_an() - giris_zamani).total_seconds()
            
            if gecen_sure >= kayit['bekleme']:
                logger.info("Kuyruktan mesaj işlendi (basit versiyon)")
            else:
                yeni_kuyruk.append(kayit)
        
        self.kuyruk = yeni_kuyruk
        self.dosya_kaydet(self.kuyruk_file, self.kuyruk)
    
    def run(self):
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        job_queue = app.job_queue
        if job_queue:
            job_queue.run_repeating(self.kuyruk_kontrol, interval=300, first=10)
        else:
            logger.warning("JobQueue kurulamadı, kuyruk sistemi çalışmayacak")
        
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

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

# Loglama
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ==================== GEMİNİ TEST ====================
print("🔧 Gemini test başlıyor...")
print(f"GEMINI_KEY var mı: {'EVET' if GEMINI_KEY else 'HAYIR'}")
if GEMINI_KEY:
    print(f"GEMINI_KEY uzunluğu: {len(GEMINI_KEY)}")
    print(f"GEMINI_KEY ilk 10 karakter: {GEMINI_KEY[:10]}...")

try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Merhaba, 2+2 kaç?")
    print(f"✅ Gemini BAŞARILI! Cevap: {response.text}")
except Exception as e:
    print(f"❌ Gemini HATASI: {e}")
# =================================================
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
        
        # Gemini'yi ayarla (DÜZELTİLDİ)
        logger.info("🤖 Gemini başlatılıyor...")
        self.model = None
        try:
            if GEMINI_KEY:
                genai.configure(api_key=GEMINI_KEY)
                self.model = genai.GenerativeModel('models/gemini-1.5-pro')
                logger.info("✅ Gemini başarıyla ayarlandı")
                
                # Test mesajı
                test = self.model.generate_content("Merhaba, test mesajı. Kısa cevap ver.")
                logger.info(f"✅ Gemini test başarılı: {test.text[:50]}")
            else:
                logger.error("❌ GEMINI_KEY bulunamadı!")
        except Exception as e:
            logger.error(f"❌ Gemini başlatılamadı: {e}")
        
        logger.info(f"🤫 {self.isim} başlatılıyor... (Yaş: {self.yas}, Şehir: {self.sehir})")
    
    def dosya_yukle(self, dosya_adi, varsayilan):
        """JSON dosyasını yükle, yoksa oluştur"""
        try:
            with open(dosya_adi, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                json.dump(varsayilan, f, ensure_ascii=False, indent=2)
            return varsayilan
        except Exception as e:
            logger.error(f"Dosya yükleme hatası {dosya_adi}: {e}")
            return varsayilan
    
    def dosya_kaydet(self, dosya_adi, veri):
        """JSON dosyasına kaydet"""
        try:
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Dosya kaydetme hatası {dosya_adi}: {e}")
    
    def su_an(self):
        """Şu anki Irak saatini ver"""
        return datetime.now(IRAQ_TZ)
    
    def dil_tani(self, metin):
        """Metnin dilini tespit et"""
        kurtce_kelimeler = ['erê', 'na', 'slaw', 'çoni', 'başim', 'spas', 'min']
        metin_lower = metin.lower()
        for kelime in kurtce_kelimeler:
            if kelime in metin_lower:
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
        """Gemini'den cevap al (DÜZELTİLDİ)"""
        if not self.model:
            logger.error("❌ Gemini modeli hazır değil!")
            return None
        
        try:
            logger.info("🤔 Gemini düşünüyor...")
            response = self.model.generate_content(prompt)
            if response and response.text:
                logger.info(f"✅ Gemini cevap verdi: {response.text[:50]}...")
                return response.text[:500]
            return None
        except Exception as e:
            logger.error(f"❌ Gemini hatası: {e}")
            return None
    
    async def cevap_ver(self, update, context):
        """Mesaja cevap ver"""
        mesaj = update.message
        kullanici = mesaj.from_user
        kullanici_id = str(kullanici.id)
        metin = mesaj.text or ""
        
        logger.info(f"💬 Cevap veriliyor: {kullanici.first_name} - {metin[:50]}")
        
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
Kişiliğin: Sessiz, gözlemci, mantıklı.
Sadece sana seslenildiğinde konuşuyorsun.
Şu an sohbet ediyorsun, samimi ve doğal konuş.

Saat: {self.su_an().strftime('%H:%M')}
Şehir: Süleymani
Kullanıcı: {kullanici.first_name}
Mesajı: "{metin}"
Dili: {dil}

Kısa ve doğal bir cevap ver (sakın bot olduğunu belli etme):
"""
        
        # Gemini'den cevap al
        cevap = await self.gemini_cevap_al(prompt)
        
        if cevap:
            await mesaj.reply_text(cevap)
            logger.info(f"✅ Cevap gönderildi")
            
            # Konuşmayı kaydet
            self.konusmalar[f"{kullanici_id}_{self.su_an().timestamp()}"] = {
                'kullanici': kullanici_id,
                'mesaj': metin,
                'cevap': cevap,
                'zaman': self.su_an().isoformat()
            }
            self.dosya_kaydet(self.konusmalar_file, self.konusmalar)
        else:
            logger.error("❌ Cevap alınamadı")
            # Gemini çalışmazsa basit cevap ver
            basit_cevaplar = [
                "Slaw, çonî?",
                "Başim, tu çonî?",
                "Evet haklısın",
                "Yok ya öyle deme",
                "Bence de"
            ]
            await mesaj.reply_text(random.choice(basit_cevaplar))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gelen mesajları işle"""
        
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
            logger.info(f"😴 {self.isim} uyuyor, cevap vermedi")
            return
        
        # Konuşma kontrolü
        konusacak_mi = False
        bekleme_suresi = 0
        
        if ozel_sohbet:
            konusacak_mi = True
            bekleme_suresi = random.randint(1, 3)
            logger.info(f"💬 Özel sohbet, {bekleme_suresi}s sonra cevap verecek")
        elif etiket_var or isim_var or yanit_var:
            konusacak_mi = True
            bekleme_suresi = random.randint(3, 8)
            logger.info(f"🏷️ Etiket var, {bekleme_suresi}s sonra cevap verecek")
        elif random.random() < 0.05:
            konusacak_mi = True
            bekleme_suresi = random.randint(5, 15)
            logger.info(f"🎲 Rastgele, {bekleme_suresi}s sonra cevap verecek")
        
        if konusacak_mi:
            await asyncio.sleep(bekleme_suresi)
            await self.cevap_ver(update, context)
    
    def run(self):
        """Botu başlat"""
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"🚀 {self.isim} çalışıyor... (Şehir: {self.sehir})")
        print(f"🤖 {self.isim} botu başlatıldı!")
        print(f"📊 Grup ID: {GROUP_ID}")
        print(f"✅ Gemini: {'ÇALIŞIYOR' if self.model else 'ÇALIŞMIYOR'}")
        
        app.run_polling()


# ==================== BAŞLAT ====================
if __name__ == "__main__":
    print("🔧 Bot başlatılıyor...")
    
    if not TOKEN:
        print("❌ HATA: BOT_TOKEN bulunamadı!")
        print("📝 Railway'de Variables sekmesine BOT_TOKEN ekleyin")
        exit(1)
    
    if not GEMINI_KEY:
        print("⚠️ UYARI: GEMINI_KEY bulunamadı!")
        print("📝 Railway'de Variables sekmesine GEMINI_KEY ekleyin")
        print("⚠️ Gemini olmadan sınırlı çalışacak")
    
    bot = RondkBot()
    bot.run()

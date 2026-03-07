# ==================== RONDK - Profesyonel AI Kız Bot ====================
import os
import json
import random
import asyncio
import logging
import sys
import fcntl
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from groq import Groq

# ==================== TEK İNSTANCE KİLİDİ ====================
def tek_instance_kontrol():
    lock_file = '/tmp/rondk.lock'
    try:
        fp = open(lock_file, 'w')
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp.write(str(os.getpid()))
        fp.flush()
        return True
    except IOError:
        print("❌ Bot zaten çalışıyor! Çıkılıyor...")
        return False

if not tek_instance_kontrol():
    exit(1)
# ============================================================

# ==================== AYARLAR ====================
TOKEN = os.environ.get('BOT_TOKEN')
GROQ_KEY = os.environ.get('GROQ_KEY')
GROUP_ID = int(os.environ.get('GROUP_ID', 0))

# Irak Saati
IRAQ_TZ = timezone(timedelta(hours=3))

# Loglama
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        self.profiller_file = 'profiller.json'
        self.istatistik_file = 'istatistik.json'
        
        # Verileri yükle
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.konusmalar = self.dosya_yukle(self.konusmalar_file, {})
        self.profiller = self.dosya_yukle(self.profiller_file, {})
        self.istatistik = self.dosya_yukle(self.istatistik_file, {
            'toplam_konusma': 0,
            'populer_kelimeler': {},
            'aktif_saatler': defaultdict(int)
        })
        
        # Groq AI'yi ayarla
        logger.info("🤖 Groq başlatılıyor...")
        self.ai_available = False
        try:
            if GROQ_KEY:
                self.groq_client = Groq(api_key=GROQ_KEY)
                logger.info("✅ Groq başarıyla ayarlandı")
                
                # Test mesajı
                test = self.ai_konus("Merhaba, kısa bir test cevabı ver.")
                if test:
                    logger.info(f"✅ Groq test başarılı: {test[:50]}...")
                    self.ai_available = True
                else:
                    logger.error("❌ Groq test başarısız!")
            else:
                logger.error("❌ GROQ_KEY bulunamadı!")
        except Exception as e:
            logger.error(f"❌ Groq başlatılamadı: {e}")
        
        # Süleymani'ye özel veriler
        self.suleymani_ozel = {
            "yemek": ["kleftiko", "dolma", "kebap", "biryan", "sambusa"],
            "mekan": ["çavılanda", "bazar", "gölyan", "şehitler", "süleymani park"],
            "olay": [
                "dün akşam çavılanda yangın çıkmış",
                "bazar'da indirim var",
                "gölyan'da düğün vardı",
                "yeni kafe açılmış"
            ]
        }
        
        # Özel günler
        self.ozel_gunler = {
            "01-01": "yılbaşı",
            "21-03": "nevroz",
            "01-05": "işçi bayramı",
            "15-08": "kurtuluş günü"
        }
        
        # Kişiye özel selamlar
        self.kisiye_ozel_selam = {}
        
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
    
    def zaman_selami(self):
        """Saate göre selam ver"""
        saat = self.su_an().hour
        if saat < 10:
            return "günaydın canım 🌅"
        elif saat < 14:
            return "merhabaa 😊"
        elif saat < 18:
            return "tünaydınn ✨"
        elif saat < 22:
            return "iyi akşamlar 🌙"
        else:
            return "gece gece ne yapıyorsun? 🦉"
    
    def dil_tani(self, metin):
        """Metnin dilini tespit et"""
        kurtce_kelimeler = ['erê', 'na', 'slaw', 'çoni', 'başim', 'spas', 'min', 'wa', 'ka', 'de']
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
    
    def ruh_hali_analizi(self, metin):
        """Metinden ruh halini analiz et"""
        mutlu = ['😂', '😊', '😁', 'iyi', 'güzel', 'harika', 'süper']
        uzgun = ['😢', '😭', '😔', 'kötü', 'berbat', 'üzgün', 'canım sıkkın']
        mutlu_soz = ['aferin', 'tebrikler', 'sevindim']
        
        metin_lower = metin.lower()
        for kelime in mutlu + mutlu_soz:
            if kelime in metin_lower:
                return "mutlu"
        for kelime in uzgun:
            if kelime in metin_lower:
                return "uzgun"
        return "normal"
    
    def ozel_gun_kontrol(self):
        """Bugün özel gün mü?"""
        bugun = self.su_an().strftime("%d-%m")
        return self.ozel_gunler.get(bugun)
    
    def kelime_ogren(self, metin):
        """Kullanıcının sık kullandığı kelimeleri öğren"""
        for kelime in metin.lower().split():
            if len(kelime) > 3:
                self.istatistik['populer_kelimeler'][kelime] = self.istatistik['populer_kelimeler'].get(kelime, 0) + 1
    
    def kullanici_profili_guncelle(self, kullanici_id, isim, metin, ruh_hali):
        """Kullanıcı profilini güncelle"""
        if kullanici_id not in self.profiller:
            self.profiller[kullanici_id] = {
                'isim': isim,
                'ilk_gorusme': self.su_an().isoformat(),
                'konusma_sayisi': 0,
                'ruh_hali': ruh_hali,
                'son_konu': metin[:50],
                'bilinenler': [],
                'ozel_notlar': {}
            }
        
        profil = self.profiller[kullanici_id]
        profil['konusma_sayisi'] += 1
        profil['son_gorusme'] = self.su_an().isoformat()
        profil['ruh_hali'] = ruh_hali
        profil['son_konu'] = metin[:50]
        
        self.dosya_kaydet(self.profiller_file, self.profiller)
    
    def ai_konus(self, prompt, kullanici_adi=None, ruh_hali=None, ozel_gun=None):
        """Groq AI ile konuş (Profesyonel versiyon)"""
        if not hasattr(self, 'groq_client'):
            return None
        
        # Kişiye özel selam
        kisi_selam = ""
        if kullanici_adi and kullanici_adi in self.kisiye_ozel_selam:
            kisi_selam = self.kisiye_ozel_selam[kullanici_adi]
        
        # Özel gün mesajı
        ozel_gun_msg = f"Bu arada bugün {ozel_gun}! " if ozel_gun else ""
        
        # Ruh haline göre ek
        ruh_mesaj = {
            "mutlu": "Karşımdaki mutlu görünüyor, ona uygun neşeli cevap ver.",
            "uzgun": "Karşımdaki üzgün görünüyor, ona destek ol, teselli et.",
            "normal": "Normal sohbet ediyoruz."
        }.get(ruh_hali, "")
        
        # Rastgele Süleymani olayı
        suleymani_olay = ""
        if random.random() < 0.15:  # %15 ihtimalle
            olay = random.choice(self.suleymani_ozel['olay'])
            suleymani_olay = f" Bu arada {olay}."
        
        system_prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Kimliğin: Ne bileyim işte, sessiz biraz ama konuşunca konuşurum.
Şey... genelde pek karışmam ama biri seslenirse cevap veririm.

ÖZEL DURUM: {ozel_gun_msg} {ruh_mesaj} {suleymani_olay}
KİŞİYE ÖZEL: {kisi_selam}

NASIL KONUŞMAMALI:
- Çok resmi konuşma ("merhaba", "nasılsınız" falan deme)
- Uzun cümleler kurma
- Çok mantıklı olma
- Bot gibi cevap verme

NASIL KONUŞMALI:
- "valla", "ya", "işte", "şey" gibi kelimeler kullan
- Bazen imla hatası yap (çünkü telefondan yazıyoruz)
- Kısa cevaplar ver
- "🤔", "😅", "😂", "😊", "🥰" gibi emojiler kullan
- Bazen anlamasan bile "hele", "hıı", "öyle mi" de
- Ara sıra Kürtçe kelime kullan ("wa", "erê", "slaw", "spas")

ÖRNEK DOĞAL KONUŞMALAR:
- "valla bilmiom ki 🤔"
- "hele bi düşüniiim..."
- "öyle mi? ben hiç farketmedm 😅"
- "ya bence de"
- "hıı anladm"
- "ne diyorsun yaa"
- "slaw canım naber? 😊"
- "wa gerçekten mi?"

SAKIN AMA SAKIN robot gibi konuşma! Normal bir kız gibi konuş.

Şimdi şu mesaja cevap ver: {prompt}
"""
        
        try:
            # Denenecek modeller
            modeller = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            
            for model in modeller:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9,  # Biraz daha yaratıcı
                        max_tokens=150
                    )
                    return response.choices[0].message.content
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"❌ Groq hatası: {e}")
            return None
    
    async def cevap_ver(self, update, context):
        """Mesaja cevap ver (Profesyonel versiyon)"""
        mesaj = update.message
        kullanici = mesaj.from_user
        kullanici_id = str(kullanici.id)
        metin = mesaj.text or ""
        
        logger.info(f"💬 Cevap veriliyor: {kullanici.first_name} - {metin[:50]}")
        
        # İstatistik güncelle
        self.istatistik['toplam_konusma'] += 1
        self.istatistik['aktif_saatler'][self.su_an().hour] += 1
        self.kelime_ogren(metin)
        self.dosya_kaydet(self.istatistik_file, self.istatistik)
        
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
        
        # Ruh hali analizi
        ruh_hali = self.ruh_hali_analizi(metin)
        
        # Kullanıcı profilini güncelle
        self.kullanici_profili_guncelle(kullanici_id, kullanici.first_name, metin, ruh_hali)
        
        # Özel gün kontrolü
        ozel_gun = self.ozel_gun_kontrol()
        
        # Dil tespiti
        dil = self.dil_tani(metin)
        
        # Zaman selamı (bazen ekle)
        zaman_selami = ""
        if random.random() < 0.2:  # %20 ihtimalle
            zaman_selami = self.zaman_selami() + " "
        
        # AI için prompt hazırla
        prompt = f"""
Kullanıcı: {kullanici.first_name}
Mesajı: "{metin}"
Dili: {dil}
Ruh hali: {ruh_hali}

Bu mesaja kısa, samimi ve doğal bir cevap ver.
Eğer mesaj Kürtçe ise Kürtçe cevap ver, Türkçe ise Türkçe cevap ver.
Çok kısa ve öz ol, sanki arkadaşınla konuşuyormuşsun gibi.
"""
        
        cevap = self.ai_konus(prompt, kullanici.first_name, ruh_hali, ozel_gun)
        
        if cevap:
            # Bazen cevabı biraz değiştir
            if random.random() < 0.1:
                cevap += " " + random.choice(["😊", "🥰", "🤔", "😅", "😂"])
            
            # Bazen soruya soruyla cevap ver
            if random.random() < 0.03 and '?' in metin:
                cevap += " sen ne düşünüyosun peki?"
            
            await mesaj.reply_text(zaman_selami + cevap)
            logger.info(f"✅ Cevap gönderildi: {cevap[:50]}...")
            
            # Konuşmayı kaydet
            self.konusmalar[f"{kullanici_id}_{self.su_an().timestamp()}"] = {
                'kullanici': kullanici_id,
                'mesaj': metin,
                'cevap': cevap,
                'ruh_hali': ruh_hali,
                'zaman': self.su_an().isoformat()
            }
            self.dosya_kaydet(self.konusmalar_file, self.konusmalar)
        else:
            logger.error("❌ Cevap alınamadı, hazır cevap veriliyor")
            basit_cevaplar = [
                "valla bilmiom ki 🤔",
                "hele bi düşüniiim...",
                "öyle mi? ben hiç farketmedm 😅",
                "ya bence de",
                "hıı anladm",
                "ne diyorsun yaa",
                "slaw canım naber? 😊",
                "wa gerçekten mi?"
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
        
        # Konuşma kontrolü - Daha doğal bekleme süreleri
        konusacak_mi = False
        bekleme_suresi = 0
        
        if ozel_sohbet:
            konusacak_mi = True
            bekleme_suresi = random.randint(2, 6)  # 2-6 saniye
            logger.info(f"💬 Özel sohbet, {bekleme_suresi}s sonra cevap verecek")
        elif etiket_var or isim_var or yanit_var:
            konusacak_mi = True
            bekleme_suresi = random.randint(4, 12)  # 4-12 saniye
            logger.info(f"🏷️ Etiket var, {bekleme_suresi}s sonra cevap verecek")
        elif random.random() < 0.05:  # %5 ihtimalle kendiliğinden
            konusacak_mi = True
            bekleme_suresi = random.randint(8, 20)  # 8-20 saniye
            logger.info(f"🎲 Rastgele, {bekleme_suresi}s sonra cevap verecek")
        
        if konusacak_mi:
            await asyncio.sleep(bekleme_suresi)
            await self.cevap_ver(update, context)
    
    def run(self):
        """Botu başlat"""
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"🚀 {self.isim} çalışıyor... (Şehir: {self.sehir})")
        print("="*50)
        print(f"🤖 {self.isim} botu başlatıldı!")
        print(f"📊 Grup ID: {GROUP_ID}")
        print(f"✅ Groq: {'ÇALIŞIYOR' if self.ai_available else 'ÇALIŞMIYOR'}")
        print(f"🧠 Hafıza: {len(self.profiller)} kişi tanıyor")
        print(f"💬 Toplam konuşma: {self.istatistik['toplam_konusma']}")
        print("="*50)
        
        app.run_polling()


# ==================== BAŞLAT ====================
if __name__ == "__main__":
    print("🔧 Rondk Profesyonel versiyon başlatılıyor...")
    
    if not TOKEN:
        print("❌ HATA: BOT_TOKEN bulunamadı!")
        exit(1)
    
    if not GROQ_KEY:
        print("⚠️ UYARI: GROQ_KEY bulunamadı!")
    
    bot = RondkBot()
    bot.run()

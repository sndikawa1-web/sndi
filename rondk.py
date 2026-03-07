# ==================== RONDK 2.0 - Profesyonel AI Kız Bot ====================
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
ADMIN_ID = 5541236874  # Senin ID'n

# Irak Saati
IRAQ_TZ = timezone(timedelta(hours=3))

# Loglama
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== RONDK 2.0 ====================
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
        self.dogumgunleri_file = 'dogumgunleri.json'
        self.kisilik_file = 'kisilik.json'
        
        # Verileri yükle
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.konusmalar = self.dosya_yukle(self.konusmalar_file, {})
        self.profiller = self.dosya_yukle(self.profiller_file, {})
        self.dogumgunleri = self.dosya_yukle(self.dogumgunleri_file, {})
        
        # İstatistikler
        self.istatistik = self.dosya_yukle(self.istatistik_file, {
            'toplam_konusma': 0,
            'populer_kelimeler': {},
            'aktif_saatler': {},
            'gunluk_mesaj': 0,
            'son_sifirlama': datetime.now(IRAQ_TZ).strftime("%Y-%m-%d")
        })
        
        # Kişilik özellikleri
        self.kisilik = self.dosya_yukle(self.kisilik_file, {
            'mizah_anlayisi': 0.5,
            'konuskanlik': 0.3,
            'dedikodu_sever': 0.7,
            'sabir': 0.8,
            'hasret': 0.0,
            'mod': 'normal'
        })
        
        # Modlar
        self.modlar = {
            'normal': 'Sıradan Rondk',
            'esprili': 'Komik Rondk 🤣',
            'felsefe': 'Düşünen Rondk 🤔',
            'anne': 'Şefkatli Rondk 🥰',
            'asi': 'Dinamit Rondk 🔥'
        }
        
        # Oyunlar
        self.oyunlar = {
            'yazı_tura': lambda: random.choice(['yazı', 'tura']),
            'zar': lambda: str(random.randint(1, 6)),
            'taş_kağıt_makas': lambda: random.choice(['taş ✊', 'kağıt ✋', 'makas ✌️'])
        }
        
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
                "gölyan'da düğün vardı"
            ]
        }
        
        # Özel günler
        self.ozel_gunler = {
            "01-01": "yılbaşı",
            "21-03": "nevroz",
            "01-05": "işçi bayramı"
        }
        
        # Fotoğraflar
        self.fotograflar = {
            "kahvalti": "☕️ bugün kahvaltıda menemen yaptım",
            "manzara": "🌄 süleymani'den manzara",
            "yemek": "😋 akşam yemeğim",
            "kedi": "🐱 caddedeki kedi"
        }
        
        # Müzikler
        self.sarkilar = {
            "şivan perwer": "🎵 Şivan Perwer - Hevalê",
            "ciwan haco": "🎵 Ciwan Haco - Dayka Min",
            "xecê": "🎵 Xecê - Keçê"
        }
        
        # Konumlar
        self.konumlar = {
            "çavılanda": "📍 Çavılanda Caddesi",
            "bazar": "📍 Büyük Bazar",
            "gölyan": "📍 Gölyan Parkı"
        }
        
        # Rüya tabirleri
        self.ruya_tabirleri = {
            "yılan": "düşman var dikkat et 🐍",
            "para": "hayırlı işler geliyor 💰",
            "ölü": "uzun ömür 👻",
            "uçmak": "terfi alacaksın ✈️"
        }
        
        # Fal bakma
        self.fallar = [
            "☕️ kahve falında yol görünüyor",
            "🔮 yakında güzel haber alacaksın",
            "⭐️ yıldızlar sana gülüyor"
        ]
        
        # Aşk dedikoduları
        self.ask_dedikodulari = [
            "🤔 @ahmet ile @mehmet arasında bir şey var mı?",
            "😏 @zeynep bugün çok mutluydu",
            "👀 kim kime bakıyor acaba?"
        ]
        
        # Günlük sayaç
        self.bugun_mesaj = 0
        self.bugun_konusan = set()
        
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
            logger.error(f"Dosya yükleme hatası: {e}")
            return varsayilan
    
    def dosya_kaydet(self, dosya_adi, veri):
        """JSON dosyasına kaydet"""
        try:
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Dosya kaydetme hatası: {e}")
    
    def su_an(self):
        """Şu anki Irak saatini ver"""
        return datetime.now(IRAQ_TZ)
    
    def gunluk_sifirla(self):
        """Günlük sayaçları sıfırla"""
        bugun = self.su_an().strftime("%Y-%m-%d")
        if self.istatistik['son_sifirlama'] != bugun:
            self.bugun_mesaj = 0
            self.bugun_konusan = set()
            self.istatistik['son_sifirlama'] = bugun
            self.dosya_kaydet(self.istatistik_file, self.istatistik)
    
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
    
    def ruh_hali_analizi(self, metin):
        """Metinden ruh halini analiz et"""
        mutlu = ['😂', '😊', 'iyi', 'güzel', 'harika']
        uzgun = ['😢', '😔', 'kötü', 'berbat', 'üzgün']
        
        metin_lower = metin.lower()
        for kelime in mutlu:
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
    
    def kisilik_guncelle(self):
        """Kişilik özelliklerini güncelle"""
        self.kisilik['konuskanlik'] = min(1.0, self.kisilik['konuskanlik'] + 0.001)
        
        # Hasret hissi (güvenli hesaplama)
        if self.profiller:
            try:
                son_konusma = max([p.get('son_gorusme', '2000-01-01') for p in self.profiller.values()])
                son_konusma_tarih = datetime.fromisoformat(son_konusma)
                gunler = (self.su_an() - son_konusma_tarih).days
                self.kisilik['hasret'] = min(1.0, max(0, gunler / 30))
            except:
                self.kisilik['hasret'] = 0.0
        
        self.dosya_kaydet(self.kisilik_file, self.kisilik)
    
    def ai_konus(self, prompt):
        """Groq AI ile konuş"""
        if not hasattr(self, 'groq_client'):
            return None
        
        system_prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Sessiz, gözlemci, mantıklı birisin.
Sadece sana seslenildiğinde konuşuyorsun.
Samimi ve doğal konuş, kısa cevaplar ver.
Ara sıra Kürtçe kelime kullan ("slaw", "spas", "çoni").
SAKIN bot olduğunu belli etme!

Modun: {self.modlar[self.kisilik['mod']]}

Şimdi şu mesaja kısa ve doğal bir cevap ver: {prompt}
"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Groq hatası: {e}")
            return None
    
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
        
        metin = mesaj.text.strip()
        kullanici = update.effective_user
        kullanici_id = str(kullanici.id)
        
        # Günlük sayaçları sıfırla
        self.gunluk_sifirla()
        
        # İstatistik güncelle
        self.istatistik['toplam_konusma'] = self.istatistik.get('toplam_konusma', 0) + 1
        self.bugun_mesaj += 1
        self.bugun_konusan.add(kullanici_id)
        
        saat = str(self.su_an().hour)
        if saat not in self.istatistik['aktif_saatler']:
            self.istatistik['aktif_saatler'][saat] = 0
        self.istatistik['aktif_saatler'][saat] += 1
        
        self.dosya_kaydet(self.istatistik_file, self.istatistik)
        
        # Kullanıcıyı kaydet
        if kullanici_id not in self.kullanicilar:
            self.kullanicilar[kullanici_id] = {
                'isim': kullanici.first_name,
                'username': kullanici.username,
                'ilk_gorusme': self.su_an().isoformat(),
                'konusma_sayisi': 0
            }
        
        self.kullanicilar[kullanici_id]['konusma_sayisi'] = self.kullanicilar[kullanici_id].get('konusma_sayisi', 0) + 1
        self.kullanicilar[kullanici_id]['son_gorusme'] = self.su_an().isoformat()
        self.dosya_kaydet(self.kullanicilar_file, self.kullanicilar)
        
        # Ruh hali analizi
        ruh_hali = self.ruh_hali_analizi(metin)
        
        # Özel gün kontrolü
        ozel_gun = self.ozel_gun_kontrol()
        
        # ========== KOMUTLAR ==========
        if metin.startswith('/'):
            komut = metin[1:].split()[0].lower()
            
            # /mod komutu
            if komut == 'mod':
                args = metin.split()
                if len(args) > 1:
                    mod = args[1].lower()
                    if mod in self.modlar:
                        self.kisilik['mod'] = mod
                        self.dosya_kaydet(self.kisilik_file, self.kisilik)
                        await mesaj.reply_text(f"Mod değiştirildi: {self.modlar[mod]} 😊")
                    else:
                        await mesaj.reply_text(f"Modlar: {', '.join(self.modlar.keys())}")
                else:
                    await mesaj.reply_text(f"Şu anki mod: {self.modlar[self.kisilik['mod']]}")
                return
            
            # /oyun komutu
            elif komut == 'oyun':
                args = metin.split()
                if len(args) > 1:
                    oyun = args[1].lower()
                    if oyun in self.oyunlar:
                        sonuc = self.oyunlar[oyun]()
                        await mesaj.reply_text(f"Sonuç: {sonuc} 🎮")
                    else:
                        await mesaj.reply_text(f"Oyunlar: {', '.join(self.oyunlar.keys())}")
                else:
                    await mesaj.reply_text(f"Oyunlar: {', '.join(self.oyunlar.keys())}")
                return
            
            # Bilinmeyen komut
            else:
                # Sessizce geç, cevap verme
                return
        
        # ========== NORMAL KONUŞMA ==========
        
        # Bot etiketlenmiş mi?
        bot_etiket = f"@{context.bot.username}"
        etiket_var = bot_etiket in metin
        
        # İsim varyasyonları var mı?
        isim_var = self.isim_var_mi(metin)
        
        # Özel sohbet kontrolü
        ozel_sohbet = update.effective_chat.type == 'private'
        
        # Sabah namazı kontrolü (05:00-15:00)
        saat = self.su_an().hour
        uyuyor_mu = 5 <= saat < 15
        
        # Uyuyorsa ve özel değilse cevap verme
        if uyuyor_mu and not ozel_sohbet:
            logger.info(f"😴 {self.isim} uyuyor")
            return
        
        # Konuşma kontrolü
        konusacak_mi = False
        
        if ozel_sohbet:
            konusacak_mi = True
            logger.info(f"💬 Özel sohbet")
        elif etiket_var or isim_var:
            konusacak_mi = True
            logger.info(f"🏷️ Etiket var")
        elif random.random() < 0.1:  # %10 ihtimalle
            konusacak_mi = True
            logger.info(f"🎲 Rastgele konuşma")
        
        if konusacak_mi:
            # Biraz bekle (insan gibi)
            await asyncio.sleep(random.randint(2, 5))
            
            # Özel kelimeler
            if "fal" in metin.lower():
                await mesaj.reply_text(random.choice(self.fallar))
                return
            
            elif "rüya" in metin.lower():
                for kelime, tabir in self.ruya_tabirleri.items():
                    if kelime in metin.lower():
                        await mesaj.reply_text(f"{tabir}")
                        return
                await mesaj.reply_text("Rüyanı yorumlayayım mı? 🔮")
                return
            
            elif "nerdesin" in metin.lower():
                mekan = random.choice(list(self.konumlar.keys()))
                await mesaj.reply_text(f"{self.konumlar[mekan]}'dayım 😊")
                return
            
            elif "müzik" in metin.lower() or "şarkı" in metin.lower():
                sarki = random.choice(list(self.sarkilar.keys()))
                await mesaj.reply_text(f"{self.sarkilar[sarki]} dinle")
                return
            
            # AI'dan cevap al
            prompt = f"Kullanıcı: {kullanici.first_name}\nMesaj: {metin}\n\nKısa ve doğal cevap ver:"
            cevap = self.ai_konus(prompt)
            
            if cevap:
                await mesaj.reply_text(cevap)
                logger.info(f"✅ Cevap gönderildi")
            else:
                # Yedek cevaplar
                yedek = random.choice([
                    "valla bilmiom 🤔",
                    "hele bi düşüniiim...",
                    "öyle mi? 😅",
                    "ya bence de",
                    "slaw canım 😊"
                ])
                await mesaj.reply_text(yedek)
    
    def run(self):
        """Botu başlat"""
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"🚀 {self.isim} çalışıyor...")
        print("="*50)
        print(f"🤖 {self.isim} botu başlatıldı!")
        print(f"✅ Groq: {'ÇALIŞIYOR' if self.ai_available else 'ÇALIŞMIYOR'}")
        print("="*50)
        print("Kullanım:")
        print("• @rondk_bot yazınca cevap verir")
        print("• /mod normal - Mod değiştir")
        print("• /oyun zar - Oyun oyna")
        print("="*50)
        
        app.run_polling()


# ==================== BAŞLAT ====================
if __name__ == "__main__":
    print("🔧 Rondk başlatılıyor...")
    
    if not TOKEN:
        print("❌ HATA: BOT_TOKEN bulunamadı!")
        exit(1)
    
    bot = RondkBot()
    bot.run()

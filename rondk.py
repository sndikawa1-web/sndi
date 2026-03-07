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
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
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
        self.gorevler_file = 'gorevler.json'
        self.kisilik_file = 'kisilik.json'
        
        # Verileri yükle
        self.kullanicilar = self.dosya_yukle(self.kullanicilar_file, {})
        self.konusmalar = self.dosya_yukle(self.konusmalar_file, {})
        self.profiller = self.dosya_yukle(self.profiller_file, {})
        self.dogumgunleri = self.dosya_yukle(self.dogumgunleri_file, {})
        self.gorevler = self.dosya_yukle(self.gorevler_file, {})
        
        # İstatistikler
        self.istatistik = self.dosya_yukle(self.istatistik_file, {
            'toplam_konusma': 0,
            'populer_kelimeler': {},
            'aktif_saatler': defaultdict(int),
            'gunluk_mesaj': 0,
            'son_sifirlama': datetime.now(IRAQ_TZ).strftime("%Y-%m-%d")
        })
        
        # Kişilik özellikleri (zamanla gelişir)
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
            "yemek": ["kleftiko", "dolma", "kebap", "biryan", "sambusa", "şila"],
            "mekan": ["çavılanda", "bazar", "gölyan", "şehitler", "süleymani park", "pira"],
            "olay": [
                "dün akşam çavılanda yangın çıkmış",
                "bazar'da indirim var",
                "gölyan'da düğün vardı",
                "yeni kafe açılmış çok güzel",
                "şehitler caddesi çok kalabalıktı"
            ]
        }
        
        # Özel günler
        self.ozel_gunler = {
            "01-01": "yılbaşı",
            "21-03": "nevroz",
            "01-05": "işçi bayramı",
            "15-08": "kurtuluş günü"
        }
        
        # Fotoğraflar (placeholder - gerçek fotoğraf URL'leri eklenebilir)
        self.fotograflar = {
            "kahvalti": "☕️ bugün kahvaltıda menemen yaptım",
            "manzara": "🌄 süleymani'den manzara harika",
            "yemek": "😋 akşam yemeğim kleftiko",
            "kedi": "🐱 caddedeki kedi çok tatlıydı",
            "cay": "🍵 çay keyfi yapıyorum"
        }
        
        # Müzikler
        self.sarkilar = {
            "şivan perwer": "🎵 https://youtu.be/bJ9zXhQrXkM",
            "ciwan haco": "🎵 https://youtu.be/8XjVJ9zXhQr",
            "xecê": "🎵 https://youtu.be/VJ9zXhQrXkM",
            "mikael": "🎵 https://youtu.be/9zXhQrXkMbJ"
        }
        
        # Konumlar
        self.konumlar = {
            "çavılanda": "📍 Çavılanda Caddesi, Süleymani",
            "bazar": "📍 Büyük Bazar, Süleymani",
            "gölyan": "📍 Gölyan Parkı, Süleymani",
            "pira": "📍 Pira Mağarası"
        }
        
        # Oyunlar
        self.oyunlar = {
            "yazı_tura": lambda: random.choice(["yazı", "tura"]),
            "zar": lambda: random.randint(1, 6),
            "taş_kağıt_makas": lambda: random.choice(["taş ✊", "kağıt ✋", "makas ✌️"])
        }
        
        # Rüya tabirleri
        self.ruya_tabirleri = {
            "yılan": "düşman var dikkat et 🐍",
            "para": "hayırlı işler geliyor 💰",
            "ölü": "uzun ömür 👻",
            "uçmak": "terfi alacaksın ✈️",
            "su": "bereket 💧",
            "ev": "huzur 🏠",
            "bebek": "müjde 👶"
        }
        
        # Fal bakma
        self.fallar = [
            "☕️ kahve falında yol görünüyor",
            "🔮 yakında güzel haber alacaksın",
            "🃏 iskambil kağıdında kara kedi var dikkat",
            "⭐️ yıldızlar sana gülüyor",
            "🌙 ay falında yeni başlangıçlar var",
            "🔮 kısmetin açık"
        ]
        
        # Aşk dedikoduları
        self.ask_dedikodulari = [
            "🤔 @ahmet ile @mehmet arasında bir şey var mı?",
            "😏 @zeynep bugün çok mutluydu, acaba biri var mı?",
            "🫢 dün @ali'yi @ayşe ile gördüm",
            "👀 kim kime bakıyor acaba?",
            "🤭 @fatma'ya biri soruyo dediler",
            "😳 @hasan'ın kalbi çarpıyo"
        ]
        
        # Görevler
        self.gorevler_listesi = {
            "gunluk": "10 kişiye selam ver 🗣️",
            "haftalik": "50 mesaj at 📝",
            "ozel": "birine yardım et 🤝"
        }
        
        # Tanıdıklar
        self.tanidiklar = {}
        
        # Kişiye özel selamlar
        self.kisiye_ozel_selam = {}
        
        # Günlük sayaç
        self.bugun_mesaj = 0
        self.bugun_konusan = set()
        
        logger.info(f"🤫 {self.isim} 2.0 başlatılıyor... (Yaş: {self.yas}, Şehir: {self.sehir})")
    
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
    
    def gunluk_sifirla(self):
        """Günlük sayaçları sıfırla"""
        bugun = self.su_an().strftime("%Y-%m-%d")
        if self.istatistik['son_sifirlama'] != bugun:
            self.bugun_mesaj = 0
            self.bugun_konusan = set()
            self.istatistik['son_sifirlama'] = bugun
            self.dosya_kaydet(self.istatistik_file, self.istatistik)
    
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
        kurtce_kelimeler = ['erê', 'na', 'slaw', 'çoni', 'başim', 'spas', 'min', 'wa', 'ka', 'de', 'ez', 'tu']
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
        mutlu = ['😂', '😊', '😁', '😍', '🥰', 'iyi', 'güzel', 'harika', 'süper', 'mutlu']
        uzgun = ['😢', '😭', '😔', '🥺', 'kötü', 'berbat', 'üzgün', 'canım sıkkın', 'ağla']
        mutlu_soz = ['aferin', 'tebrikler', 'sevindim', 'maşallah']
        
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
    
    def kelime_ogren(self, metin, kullanici_id):
        """Kullanıcının sık kullandığı kelimeleri öğren"""
        for kelime in metin.lower().split():
            if len(kelime) > 3:
                self.istatistik['populer_kelimeler'][kelime] = self.istatistik['populer_kelimeler'].get(kelime, 0) + 1
        
        # Kullanıcı profiline ekle
        if kullanici_id in self.profiller:
            if 'kelimeler' not in self.profiller[kullanici_id]:
                self.profiller[kullanici_id]['kelimeler'] = {}
            for kelime in metin.lower().split():
                if len(kelime) > 3:
                    self.profiller[kullanici_id]['kelimeler'][kelime] = self.profiller[kullanici_id]['kelimeler'].get(kelime, 0) + 1
    
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
                'ozel_notlar': {},
                'kelimeler': {},
                'toplam_mesaj': 0
            }
        
        profil = self.profiller[kullanici_id]
        profil['konusma_sayisi'] += 1
        profil['toplam_mesaj'] = profil.get('toplam_mesaj', 0) + 1
        profil['son_gorusme'] = self.su_an().isoformat()
        profil['ruh_hali'] = ruh_hali
        profil['son_konu'] = metin[:50]
        
        self.dosya_kaydet(self.profiller_file, self.profiller)
    
    def kisilik_guncelle(self):
        """Kişilik özelliklerini zamanla güncelle"""
        # Konuşkanlık artsın
        self.kisilik['konuskanlik'] = min(1.0, self.kisilik['konuskanlik'] + 0.001)
        
        # Hasret hissi
        son_konusma = max([p.get('son_gorusme', '2000-01-01') for p in self.profiller.values()])
        son_konusma_tarih = datetime.fromisoformat(son_konusma)
        gunler = (self.su_an() - son_konusma_tarih).days
        self.kisilik['hasret'] = min(1.0, gunler / 30)
        
        self.dosya_kaydet(self.kisilik_file, self.kisilik)
    
    def dogum_gunu_kontrol(self):
        """Doğum günü olan var mı?"""
        bugun = self.su_an().strftime("%d-%m")
        dogumlular = []
        for uid, tarih in self.dogumgunleri.items():
            if tarih == bugun:
                dogumlular.append(uid)
        return dogumlular
    
    def ai_konus(self, prompt, kullanici_adi=None, ruh_hali=None, ozel_gun=None):
        """Groq AI ile konuş (Profesyonel versiyon)"""
        if not hasattr(self, 'groq_client'):
            return None
        
        # Kişilik etkisi
        mizah = self.kisilik['mizah_anlayisi']
        dedikodu = self.kisilik['dedikodu_sever']
        mod = self.kisilik['mod']
        
        # Mod açıklamaları
        mod_aciklamalari = {
            'normal': 'Normal sohbet ediyorsun.',
            'esprili': 'Çok espri yap, komik ol.',
            'felsefe': 'Derin düşünceli konuş.',
            'anne': 'Şefkatli, koruyucu konuş.',
            'asi': 'Biraz asi, ukala konuş.'
        }
        
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
        
        # Dedikodu ihtimali
        dedikodu_ek = ""
        if random.random() < dedikodu * 0.3:  # Dedikodu severliğe göre
            dedikodu_ek = f" {random.choice(self.ask_dedikodulari)}"
        
        system_prompt = f"""
Sen 23 yaşında, Süleymanili bir kızsın. İsmin Rondk.
Kimliğin: Ne bileyim işte, sessiz biraz ama konuşunca konuşurum.
Şey... genelde pek karışmam ama biri seslenirse cevap veririm.

KİŞİLİK ÖZELLİKLERİN:
- Mizah anlayışın: {mizah:.1f}/1.0
- Dedikodu severliğin: {dedikodu:.1f}/1.0
- Modun: {mod_aciklamalari[mod]}

ÖZEL DURUM: {ozel_gun_msg} {ruh_mesaj} {suleymani_olay} {dedikodu_ek}
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
- Ara sıra Kürtçe kelime kullan ("wa", "erê", "slaw", "spas", "çoni")

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
                        temperature=0.9,
                        max_tokens=200
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
        
        # Günlük sayaçları sıfırla
        self.gunluk_sifirla()
        
        # İstatistik güncelle
        self.istatistik['toplam_konusma'] += 1
        self.bugun_mesaj += 1
        self.bugun_konusan.add(kullanici_id)
        self.istatistik['aktif_saatler'][str(self.su_an().hour)] = self.istatistik['aktif_saatler'].get(str(self.su_an().hour), 0) + 1
        self.kelime_ogren(metin, kullanici_id)
        self.istatistik['gunluk_mesaj'] = self.bugun_mesaj
        self.dosya_kaydet(self.istatistik_file, self.istatistik)
        
        # Kişilik güncelle
        self.kisilik_guncelle()
        
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
        
        # Doğum günü kontrolü
        dogumlular = self.dogum_gunu_kontrol()
        if kullanici_id in dogumlular:
            dogum_mesaji = f"🎂 {kullanici.first_name} doğum günün kutlu olsun! nice yıllara 🥳"
            await mesaj.reply_text(dogum_mesaji)
            return
        
        # Dil tespiti
        dil = self.dil_tani(metin)
        
        # Zaman selamı (bazen ekle)
        zaman_selami = ""
        if random.random() < 0.2:  # %20 ihtimalle
            zaman_selami = self.zaman_selami() + " "
        
        # Özel komutlar
        if metin.startswith('/mod'):
            mod = metin.replace('/mod', '').strip().lower()
            if mod in self.modlar:
                self.kisilik['mod'] = mod
                self.dosya_kaydet(self.kisilik_file, self.kisilik)
                await mesaj.reply_text(f"Mod {self.modlar[mod]} olarak değiştirildi! 😊")
                return
        
        elif metin.startswith('/dogumgunu'):
            tarih = metin.replace('/dogumgunu', '').strip()
            self.dogumgunleri[kullanici_id] = tarih
            self.dosya_kaydet(self.dogumgunleri_file, self.dogumgunleri)
            await mesaj.reply_text(f"Doğum günün {tarih} olarak kaydedildi! 🎂")
            return
        
        elif "oyun" in metin.lower() and ("ne" in metin or "var" in metin):
            oyun_list = ", ".join(self.oyunlar.keys())
            await mesaj.reply_text(f"Oynayabileceğimiz oyunlar: {oyun_list}. Hangisini istersin? 🎮")
            return
        
        elif "yazı tura" in metin.lower():
            await mesaj.reply_text(f"Sonuç: {self.oyunlar['yazı_tura']()} 🪙")
            return
        
        elif "zar" in metin.lower():
            await mesaj.reply_text(f"Zar: {self.oyunlar['zar']()} 🎲")
            return
        
        elif "taş kağıt makas" in metin.lower():
            await mesaj.reply_text(f"Ben: {self.oyunlar['taş_kağıt_makas']()} ✨")
            return
        
        elif "fal" in metin.lower():
            await mesaj.reply_text(random.choice(self.fallar))
            return
        
        elif "rüya" in metin.lower() or "düş" in metin.lower():
            for kelime, tabir in self.ruya_tabirleri.items():
                if kelime in metin.lower():
                    await mesaj.reply_text(f"Rüyanda {kelime} görmüşsün, {tabir}")
                    return
            await mesaj.reply_text("Rüyan neydi? Yorumlayayım 🔮")
            return
        
        elif "nerdesin" in metin.lower():
            mekan = random.choice(list(self.konumlar.keys()))
            await mesaj.reply_text(f"{self.konumlar[mekan]}'dayım şu an, gelirsen konuşuruz 😊")
            return
        
        elif "foto" in metin.lower() or "fotoğraf" in metin.lower():
            foto = random.choice(list(self.fotograflar.keys()))
            await mesaj.reply_text(self.fotograflar[foto])
            return
        
        elif "müzik" in metin.lower() or "şarkı" in metin.lower():
            sarki = random.choice(list(self.sarkilar.keys()))
            await mesaj.reply_text(f"{sarki} dinle bence çok güzel {self.sarkilar[sarki]}")
            return
        
        elif "görev" in metin.lower():
            gorev = random.choice(list(self.gorevler_listesi.values()))
            await mesaj.reply_text(f"Bugünkü görevin: {gorev}")
            return
        
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
                "wa gerçekten mi?",
                "ya öyle deme üzülürüm 😔",
                "çok sevindim duyduğuma 🥰"
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
        
        # Komutları cevaplama (özel komutlar hariç)
        if metin.startswith('/'):
            # Admin için günlük rapor
            if metin == '/rapor' and update.effective_user.id == ADMIN_ID:
                rapor = f"""
📊 **GÜNLÜK RAPOR**
👥 Bugün konuşan: {len(self.bugun_konusan)} kişi
💬 Toplam mesaj: {self.bugun_mesaj}
🔥 En aktif saat: {max(self.istatistik['aktif_saatler'], key=self.istatistik['aktif_saatler'].get)}:00
📈 Toplam konuşma: {self.istatistik['toplam_konusma']}
🧠 Tanınan kişi: {len(self.profiller)}
"""
                await mesaj.reply_text(rapor)
                return
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
        
        # Komutlar
        app.add_handler(CommandHandler("mod", self.mod_komutu))
        app.add_handler(CommandHandler("dogumgunu", self.dogumgunu_komutu))
        app.add_handler(CommandHandler("rapor", self.rapor_komutu))
        app.add_handler(CommandHandler("oyun", self.oyun_komutu))
        
        # Mesaj handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"🚀 {self.isim} 2.0 çalışıyor... (Şehir: {self.sehir})")
        print("="*60)
        print(f"🤖 {self.isim} 2.0 botu başlatıldı!")
        print(f"📊 Grup ID: {GROUP_ID}")
        print(f"✅ Groq: {'ÇALIŞIYOR' if self.ai_available else 'ÇALIŞMIYOR'}")
        print(f"🧠 Hafıza: {len(self.profiller)} kişi tanıyor")
        print(f"💬 Toplam konuşma: {self.istatistik['toplam_konusma']}")
        print(f"🎭 Mod: {self.modlar[self.kisilik['mod']]}")
        print("="*60)
        
        app.run_polling()
    
    # Komut fonksiyonları
    async def mod_komutu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mod değiştirme komutu"""
        if not context.args:
            modlar_list = ", ".join(self.modlar.keys())
            await update.message.reply_text(f"Kullanılabilir modlar: {modlar_list}")
            return
        
        mod = context.args[0].lower()
        if mod in self.modlar:
            self.kisilik['mod'] = mod
            self.dosya_kaydet(self.kisilik_file, self.kisilik)
            await update.message.reply_text(f"Mod {self.modlar[mod]} olarak değiştirildi! 😊")
        else:
            await update.message.reply_text("❌ Böyle bir mod yok!")
    
    async def dogumgunu_komutu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Doğum günü kaydetme komutu"""
        if not context.args:
            await update.message.reply_text("📝 Örnek: /dogumgunu 15.05")
            return
        
        tarih = context.args[0]
        self.dogumgunleri[str(update.effective_user.id)] = tarih
        self.dosya_kaydet(self.dogumgunleri_file, self.dogumgunleri)
        await update.message.reply_text(f"🎂 Doğum günün {tarih} olarak kaydedildi!")
    
    async def rapor_komutu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Günlük rapor (sadece admin)"""
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Bu komutu sadece admin kullanabilir!")
            return
        
        rapor = f"""
📊 **GÜNLÜK RAPOR**
👥 Bugün konuşan: {len(self.bugun_konusan)} kişi
💬 Toplam mesaj: {self.bugun_mesaj}
🔥 En aktif saat: {max(self.istatistik['aktif_saatler'], key=self.istatistik['aktif_saatler'].get)}:00
📈 Toplam konuşma: {self.istatistik['toplam_konusma']}
🧠 Tanınan kişi: {len(self.profiller)}
🎭 Şu anki mod: {self.modlar[self.kisilik['mod']]}
"""
        await update.message.reply_text(rapor)
    
    async def oyun_komutu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Oyun oynama komutu"""
        if not context.args:
            oyun_list = ", ".join(self.oyunlar.keys())
            await update.message.reply_text(f"Oynayabileceğimiz oyunlar: {oyun_list}. Hangisini istersin? 🎮")
            return
        
        oyun = context.args[0].lower()
        if oyun == "yazı_tura" or oyun == "yazı tura":
            await update.message.reply_text(f"Sonuç: {self.oyunlar['yazı_tura']()} 🪙")
        elif oyun == "zar":
            await update.message.reply_text(f"Zar: {self.oyunlar['zar']()} 🎲")
        elif oyun == "taş_kağıt_makas" or oyun == "tkm":
            await update.message.reply_text(f"Ben: {self.oyunlar['taş_kağıt_makas']()} ✨")
        else:
            await update.message.reply_text("❌ Bilinmeyen oyun!")


# ==================== BAŞLAT ====================
if __name__ == "__main__":
    print("🔧 Rondk 2.0 Profesyonel versiyon başlatılıyor...")
    print("="*60)
    
    if not TOKEN:
        print("❌ HATA: BOT_TOKEN bulunamadı!")
        exit(1)
    
    if not GROQ_KEY:
        print("⚠️ UYARI: GROQ_KEY bulunamadı!")
    
    bot = RondkBot()
    bot.run()

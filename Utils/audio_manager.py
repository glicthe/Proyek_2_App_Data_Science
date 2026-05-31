import threading
import time
import re
from io import BytesIO
from gtts import gTTS
import pygame

# Inisialisasi Pygame Mixer untuk pemutaran audio
try:
    pygame.mixer.init()
except Exception as e:
    print(f"Peringatan: Gagal menginisialisasi pygame mixer. Error: {e}")

# Variabel Global untuk mekanisme Cooldown
WAKTU_TERAKHIR_BUNYI = 0.0
COOLDOWN_DETIK = 4.0  # Jeda 4 detik agar suara tidak menumpuk/berisik berulang

def putar_audio_gtts(pesan: str) -> None:
    """
    Mengubah teks menjadi suara (TTS) dan memutarnya secara asinkron (tidak memblokir video).
    """
    global WAKTU_TERAKHIR_BUNYI
    sekarang = time.time()
    
    # 1. Cek Cooldown dan apakah speaker sedang dipakai (sibuk)
    if (sekarang - WAKTU_TERAKHIR_BUNYI < COOLDOWN_DETIK) or pygame.mixer.music.get_busy():
        return
        
    WAKTU_TERAKHIR_BUNYI = sekarang
    
    # 2. Bersihkan teks dari emoji (misal: 🚨) dan info "[Jarak: ~10 m]" agar enak didengar robot
    teks_bersih = re.sub(r'\[.*?\]', '', pesan)  
    teks_bersih = re.sub(r'[^\w\s.,!?-]', '', teks_bersih) 
    teks_bersih = teks_bersih.strip()
    
    # 3. Fungsi inti yang akan dijalankan di thread terpisah
    def _proses_dan_putar():
        try:
            # Generate suara dari teks (butuh koneksi internet)
            tts = gTTS(text=teks_bersih, lang='id')
            
            # Gunakan BytesIO agar tidak perlu save file .mp3 ke hardisk (Anti Error di Windows)
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            # Putar audio
            pygame.mixer.music.load(fp, 'mp3')
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Gagal memutar audio TTS (cek koneksi internet). Error: {e}")

    # 4. Lempar tugas ke Threading agar Streamlit / Video tidak nge-lag
    thread_audio = threading.Thread(target=_proses_dan_putar, daemon=True)
    thread_audio.start()
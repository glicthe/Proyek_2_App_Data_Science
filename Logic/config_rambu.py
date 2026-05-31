"""
=============================================================
Logic/config_rambu.py
Kamus konfigurasi 48 kelas rambu lalu lintas Indonesia
=============================================================
Struktur tiap entri:
  kategori       : 'info' | 'bahaya' | 'larangan' | 'speed_limit'
  pesan          : Notifikasi teks yang ditampilkan ke pengemudi
  play_audio     : True jika harus membunyikan alarm/TTS
  batas_kecepatan: Batas kecepatan dalam km/jam (khusus speed_limit)
                   None untuk semua kelas non-speed-limit
=============================================================
PANDUAN KATEGORI:
  info        → Rambu informatif / penanda fasilitas.
                Tidak memicu suara, hanya tampil di panel notifikasi.
  bahaya      → Rambu peringatan kondisi jalan berbahaya.
                Memicu audio peringatan.
  larangan    → Rambu larangan tindakan (belok, parkir, masuk, dll).
                Memicu audio peringatan.
  speed_limit → Rambu batas kecepatan.
                Logika over-speeding ditangani di core_logic.py.
=============================================================
"""

# ==============================================================
# KAMUS UTAMA — 48 KELAS RAMBU
# ==============================================================
KONFIGURASI_RAMBU: dict[str, dict] = {

    # ----------------------------------------------------------
    # KATEGORI: INFO
    # Rambu penanda fasilitas / layanan publik
    # play_audio = False — informasi pasif, tidak perlu alarm
    # ----------------------------------------------------------

    "Balai Pertolongan Pertama": {
        "kategori"        : "info",
        "pesan"           : "Balai P3K tersedia di sekitar area ini.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Gereja": {
        "kategori"        : "info",
        "pesan"           : "Kawasan gereja terdeteksi di depan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Jalur Sepeda": {
        "kategori"        : "info",
        "pesan"           : "Jalur sepeda — bagikan jalan dengan pesepeda.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Jembatan": {
        "kategori"        : "info",
        "pesan"           : "Memasuki area jembatan. Kurangi kecepatan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Lajur Kiri": {
        "kategori"        : "info",
        "pesan"           : "Tetap di lajur kiri sesuai aturan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Masjid": {
        "kategori"        : "info",
        "pesan"           : "Kawasan masjid — harap jaga ketenangan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Pemberhentian Bus": {
        "kategori"        : "info",
        "pesan"           : "Halte bus di depan. Waspadai penumpang yang menyeberang.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Pom Bensin": {
        "kategori"        : "info",
        "pesan"           : "Stasiun pengisian bahan bakar di sekitar area ini.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Rumah Sakit": {
        "kategori"        : "info",
        "pesan"           : "Kawasan rumah sakit — harap jaga ketenangan dan kecepatan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Tempat Parkir": {
        "kategori"        : "info",
        "pesan"           : "Area parkir tersedia di sekitar lokasi ini.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Ikuti Bundaran": {
        "kategori"        : "info",
        "pesan"           : "Bundaran di depan — ikuti arah putar sesuai rambu.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Perintah Jalur Penyebrangan": {
        "kategori"        : "info",
        "pesan"           : "Gunakan jalur penyeberangan yang tersedia.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Persimpangan 3 Sisi Kiri": {
        "kategori"        : "info",
        "pesan"           : "Persimpangan tiga arah sisi kiri di depan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Persimpangan 4": {
        "kategori"        : "info",
        "pesan"           : "Persimpangan empat arah di depan. Perhatikan prioritas.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Pilih Salah Satu Jalur": {
        "kategori"        : "info",
        "pesan"           : "Pilih jalur yang sesuai tujuan Anda.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    "Putar Balik": {
        "kategori"        : "info",
        "pesan"           : "Titik putar balik tersedia di depan.",
        "play_audio"      : False,
        "batas_kecepatan" : None,
    },

    # ----------------------------------------------------------
    # KATEGORI: BAHAYA
    # Rambu peringatan kondisi jalan berbahaya
    # play_audio = True — pengemudi HARUS diperingatkan secara aktif
    # ----------------------------------------------------------

    "Banyak Anak-Anak": {
        "kategori"        : "bahaya",
        "pesan"           : "HATI-HATI! Kawasan sekolah — banyak anak-anak menyeberang.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Banyak Tikungan Pertama Kanan": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Tikungan ganda — arah pertama ke kanan.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Banyak Tikungan Pertama Kiri": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Tikungan ganda — arah pertama ke kiri.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Hati-Hati": {
        "kategori"        : "bahaya",
        "pesan"           : "PERHATIAN! Kondisi jalan membutuhkan kewaspadaan ekstra.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Lampu Lalu Lintas": {
        "kategori"        : "bahaya",
        "pesan"           : "Persimpangan dengan lampu lalu lintas di depan. Siap berhenti.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Peringatan Bahaya Tanah Longsor": {
        "kategori"        : "bahaya",
        "pesan"           : "BAHAYA! Rawan tanah longsor. Tingkatkan kewaspadaan!",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Peringatan Perlintasan Kereta Api": {
        "kategori"        : "bahaya",
        "pesan"           : "BAHAYA! Perlintasan kereta api di depan. Berhenti & pastikan aman!",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Persimpangan 3 Prioritas": {
        "kategori"        : "bahaya",
        "pesan"           : "Persimpangan tiga — berikan prioritas kepada kendaraan dari arah utama.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Persimpangan 3 Prioritas Kanan": {
        "kategori"        : "bahaya",
        "pesan"           : "Persimpangan — berikan prioritas kepada kendaraan dari kanan.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Persimpangan 3 Prioritas Kiri": {
        "kategori"        : "bahaya",
        "pesan"           : "Persimpangan — berikan prioritas kepada kendaraan dari kiri.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Polisi Tidur": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Polisi tidur di depan. Kurangi kecepatan segera!",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Penyebrangan Pejalan Kaki": {
        "kategori"        : "bahaya",
        "pesan"           : "HATI-HATI! Zebra cross — utamakan pejalan kaki.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Tikungan Ganda Pertama Ke Kanan": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Tikungan ganda tajam — mulai ke kanan.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Tikungan Ganda Pertama Ke Kiri": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Tikungan ganda tajam — mulai ke kiri.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Tikungan Ke Kanan": {
        "kategori"        : "bahaya",
        "pesan"           : "WASPADA! Tikungan ke kanan. Kurangi kecepatan.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    # ----------------------------------------------------------
    # KATEGORI: LARANGAN
    # Rambu yang melarang tindakan tertentu
    # play_audio = True — pelanggaran potensial harus dibunyikan
    # ----------------------------------------------------------

    "Berhenti": {
        "kategori"        : "larangan",
        "pesan"           : "STOP! Rambu BERHENTI. Hentikan kendaraan sepenuhnya!",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Belok Kanan": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Tidak boleh belok kanan di titik ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Belok Kiri": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Tidak boleh belok kiri di titik ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Berhenti": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Dilarang berhenti di sepanjang zona ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Masuk": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Jalan ini tidak boleh dimasuki. Cari rute alternatif.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Mendahului": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Dilarang mendahului kendaraan lain di zona ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Parkir": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Dilarang memarkir kendaraan di area ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Dilarang Putar Balik": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Dilarang putar balik di titik ini.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    "Larangan Muatan > 10 ton": {
        "kategori"        : "larangan",
        "pesan"           : "LARANGAN! Kendaraan bermuatan lebih dari 10 ton dilarang melintas.",
        "play_audio"      : True,
        "batas_kecepatan" : None,
    },

    # ----------------------------------------------------------
    # KATEGORI: SPEED_LIMIT
    # Rambu batas kecepatan maksimum
    # play_audio dikontrol dinamis oleh core_logic.py
    # (True jika melanggar, False jika patuh)
    # ----------------------------------------------------------

    "Kecepatan Maks. 30 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 30 km/jam.",
        "play_audio"      : False,   # dioverride di core_logic jika over-speeding
        "batas_kecepatan" : 30,
    },

    "Kecepatan Maks. 40 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 40 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 40,
    },

    "Kecepatan Maks. 70 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 70 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 70,
    },

    "Kecepatan Maks. 80 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 80 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 80,
    },

    "Kecepatan Maks. 90 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 90 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 90,
    },

    "Kecepatan Maks. 100 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 100 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 100,
    },

    "Kecepatan Maks. 110 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 110 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 110,
    },

    "Kecepatan Maks.120 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 120 km/jam.",
        "play_audio"      : False,
        "batas_kecepatan" : 120,
    },
}

# ==============================================================
# KONSTANTA BANTU — digunakan oleh core_logic.py
# ==============================================================

# Semua nama kelas yang valid (untuk validasi input dari YOLO)
DAFTAR_KELAS: list[str] = list(KONFIGURASI_RAMBU.keys())

# Peta warna status untuk tampilan UI Streamlit
# key: status yang direturn core_logic → value: kelas CSS notifikasi
WARNA_STATUS: dict[str, str] = {
    "Aman"       : "notif-ok",
    "Info"       : "notif-ok",
    "Peringatan" : "notif-warn",
    "Larangan"   : "notif-error",
    "Pelanggaran": "notif-error",
}

# Ikon status untuk tampilan UI (opsional — dipakai di panel notifikasi)
IKON_STATUS: dict[str, str] = {
    "Aman"       : "✅",
    "Info"       : "ℹ️",
    "Peringatan" : "⚠️",
    "Larangan"   : "🚫",
    "Pelanggaran": "🚨",
}

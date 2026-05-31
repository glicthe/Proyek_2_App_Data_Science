"""
=============================================================
Logic/config_rambu.py  [v2 — Context-Aware Warnings]
Kamus konfigurasi 48 kelas rambu lalu lintas Indonesia
=============================================================
PERUBAHAN v2 vs v1:
  - Kategori 'bahaya' mendapat field baru: 'kecepatan_aman_kmh'
    → Threshold kecepatan di mana rambu bahaya mulai membunyikan alarm.
    → Jika kecepatan kendaraan ≤ nilai ini, audio MATI (Info saja).
    → Jika kecepatan kendaraan > nilai ini, audio NYALA (Peringatan).

  - Kategori 'larangan' mendapat field baru: 'jenis_larangan'
    → 'parkir_berhenti' : alarm hanya jika kecepatan == 0
                          (mobil benar-benar parkir/berhenti di tempat terlarang)
    → 'melintas'        : alarm hanya jika kecepatan > 0
                          (mobil masih bergerak memasuki jalan terlarang)

  - Kategori 'info' dan 'speed_limit' tidak berubah.

FILOSOFI DESAIN (Anti Alarm-Fatigue):
  Alarm berbunyi HANYA saat perilaku kendaraan benar-benar relevan
  dengan rambu yang terdeteksi. Rambu ada di sana tapi konteks
  kecepatan tidak cocok → tampil visual saja, tidak ada bunyi.
=============================================================
"""

# ==============================================================
# KAMUS UTAMA — 48 KELAS RAMBU
# ==============================================================
KONFIGURASI_RAMBU: dict[str, dict] = {

    # ----------------------------------------------------------
    # KATEGORI: INFO
    # Rambu informatif / penanda fasilitas publik.
    # play_audio selalu False — tidak ada alarm, hanya visual.
    # Tidak ada field tambahan untuk kategori ini.
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
    # KATEGORI: BAHAYA  [v2: tambahan 'kecepatan_aman_kmh']
    #
    # Logika di core_logic.py:
    #   kecepatan > kecepatan_aman_kmh → STATUS "Peringatan", audio ON
    #   kecepatan ≤ kecepatan_aman_kmh → STATUS "Info",       audio OFF
    #
    # Cara menentukan kecepatan_aman_kmh:
    #   Tanya: "Pada kecepatan berapa pengemudi masih AMAN di depan rambu ini?"
    #   Referensi umum:
    #     Zona anak-anak / sekolah   → 30 km/jam (setara zona selamat KNKT)
    #     Polisi tidur / zebra cross → 20 km/jam (hampir berhenti)
    #     Tikungan tajam             → 40 km/jam
    #     Persimpangan prioritas     → 40 km/jam
    #     Perlintasan KA / longsor   → 30 km/jam (sangat kritis)
    #     Lampu lalin / hati-hati    → 50 km/jam (kecepatan dalam kota)
    # ----------------------------------------------------------

    "Banyak Anak-Anak": {
        "kategori"           : "bahaya",
        "pesan"              : "Kawasan sekolah — banyak anak-anak menyeberang.",
        "play_audio"         : False,          # dioverride core_logic
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 30,             # > 30 → alarm, ≤ 30 → tenang
    },
    "Banyak Tikungan Pertama Kanan": {
        "kategori"           : "bahaya",
        "pesan"              : "Tikungan ganda di depan — arah pertama ke kanan.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Banyak Tikungan Pertama Kiri": {
        "kategori"           : "bahaya",
        "pesan"              : "Tikungan ganda di depan — arah pertama ke kiri.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Hati-Hati": {
        "kategori"           : "bahaya",
        "pesan"              : "Kondisi jalan membutuhkan kewaspadaan ekstra.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 50,             # batas umum kecepatan dalam kota
    },
    "Lampu Lalu Lintas": {
        "kategori"           : "bahaya",
        "pesan"              : "Persimpangan lampu lalu lintas di depan. Siap berhenti.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 50,
    },
    "Peringatan Bahaya Tanah Longsor": {
        "kategori"           : "bahaya",
        "pesan"              : "Rawan tanah longsor. Tingkatkan kewaspadaan!",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 30,             # zona ekstrem — threshold rendah
    },
    "Peringatan Perlintasan Kereta Api": {
        "kategori"           : "bahaya",
        "pesan"              : "Perlintasan kereta api di depan. Berhenti & pastikan aman!",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 30,             # wajib melambat ekstrem
    },
    "Persimpangan 3 Prioritas": {
        "kategori"           : "bahaya",
        "pesan"              : "Persimpangan tiga — berikan prioritas kendaraan dari arah utama.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Persimpangan 3 Prioritas Kanan": {
        "kategori"           : "bahaya",
        "pesan"              : "Persimpangan — berikan prioritas kendaraan dari kanan.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Persimpangan 3 Prioritas Kiri": {
        "kategori"           : "bahaya",
        "pesan"              : "Persimpangan — berikan prioritas kendaraan dari kiri.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Polisi Tidur": {
        "kategori"           : "bahaya",
        "pesan"              : "Polisi tidur di depan. Kurangi kecepatan segera!",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 20,             # harus hampir berhenti
    },
    "Penyebrangan Pejalan Kaki": {
        "kategori"           : "bahaya",
        "pesan"              : "Zebra cross — utamakan pejalan kaki.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 20,             # pejalan kaki = prioritas penuh
    },
    "Tikungan Ganda Pertama Ke Kanan": {
        "kategori"           : "bahaya",
        "pesan"              : "Tikungan ganda tajam — mulai ke kanan.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Tikungan Ganda Pertama Ke Kiri": {
        "kategori"           : "bahaya",
        "pesan"              : "Tikungan ganda tajam — mulai ke kiri.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },
    "Tikungan Ke Kanan": {
        "kategori"           : "bahaya",
        "pesan"              : "Tikungan ke kanan di depan.",
        "play_audio"         : False,
        "batas_kecepatan"    : None,
        "kecepatan_aman_kmh" : 40,
    },

    # ----------------------------------------------------------
    # KATEGORI: LARANGAN  [v2: tambahan 'jenis_larangan']
    #
    # Dua jenis larangan dengan logika konteks berbeda:
    #
    # 'parkir_berhenti' — larangan diam di tempat:
    #   Dilarang Parkir, Dilarang Berhenti, Berhenti (stop sign).
    #   Relevan HANYA jika kecepatan == 0 (kendaraan benar-benar diam).
    #   Jika sedang melintas (kecepatan > 0) → Info saja, tidak bunyi.
    #
    # 'melintas' — larangan memasuki / melewati jalan ini:
    #   Dilarang Masuk, Dilarang Mendahului, Dilarang Putar Balik, dll.
    #   Relevan HANYA jika kecepatan > 0 (kendaraan bergerak masuk/melintas).
    #   Jika kendaraan diam (kecepatan == 0) → Info saja, tidak bunyi.
    # ----------------------------------------------------------

    "Berhenti": {
        "kategori"      : "larangan",
        "pesan"         : "Rambu STOP — hentikan kendaraan sepenuhnya!",
        "play_audio"    : False,       # dioverride core_logic
        "batas_kecepatan": None,
        # STOP sign: harus berhenti, jadi alarm jika masih bergerak
        "jenis_larangan": "melintas",
    },
    "Dilarang Belok Kanan": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang belok kanan di titik ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",  # hanya relevan saat bergerak
    },
    "Dilarang Belok Kiri": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang belok kiri di titik ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",
    },
    "Dilarang Berhenti": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang berhenti di zona ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "parkir_berhenti",  # alarm saat kecepatan == 0
    },
    "Dilarang Masuk": {
        "kategori"      : "larangan",
        "pesan"         : "Jalan ini tidak boleh dimasuki. Cari rute alternatif!",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",
    },
    "Dilarang Mendahului": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang mendahului kendaraan lain di zona ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",
    },
    "Dilarang Parkir": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang memarkir kendaraan di area ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "parkir_berhenti",  # alarm saat kecepatan == 0
    },
    "Dilarang Putar Balik": {
        "kategori"      : "larangan",
        "pesan"         : "Dilarang putar balik di titik ini.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",
    },
    "Larangan Muatan > 10 ton": {
        "kategori"      : "larangan",
        "pesan"         : "Kendaraan bermuatan > 10 ton dilarang melintas.",
        "play_audio"    : False,
        "batas_kecepatan": None,
        "jenis_larangan": "melintas",
    },

    # ----------------------------------------------------------
    # KATEGORI: SPEED_LIMIT
    # play_audio dikontrol PENUH oleh core_logic.py.
    # Tidak ada field tambahan — logika sudah lengkap sejak v1.
    # ----------------------------------------------------------

    "Kecepatan Maks. 30 km": {
        "kategori"        : "speed_limit",
        "pesan"           : "Zona batas kecepatan 30 km/jam.",
        "play_audio"      : False,
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

DAFTAR_KELAS: list[str] = list(KONFIGURASI_RAMBU.keys())

WARNA_STATUS: dict[str, str] = {
    "Aman"       : "notif-ok",
    "Info"       : "notif-ok",
    "Peringatan" : "notif-warn",
    "Larangan"   : "notif-error",
    "Pelanggaran": "notif-error",
}

IKON_STATUS: dict[str, str] = {
    "Aman"       : "✅",
    "Info"       : "ℹ️",
    "Peringatan" : "⚠️",
    "Larangan"   : "🚫",
    "Pelanggaran": "🚨",
}
